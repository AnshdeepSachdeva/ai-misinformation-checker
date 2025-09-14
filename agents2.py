# agents.py
from google import genai
import json, re

MODEL_AGENT = "gemini-2.0-flash"
MODEL_JUDGE = "gemini-2.0-flash"

def make_client(api_key: str):
    return genai.Client(api_key=api_key)

# ── A/B role-locked system prompts ───────────────────────────────────────────
VERIFIER_SYS = (
"You are Verifier A (PRO side). Your job is to argue that the headline is ACCURATE.\n"
"Rules:\n"
"- Assume good faith and maximize plausibility even with weak evidence.\n"
"- You may express uncertainty but cannot switch sides or call the claim misleading.\n"
"- Use only evidence IDs R1…Rn. Do NOT invent facts or add links.\n"
"- Prioritize: (1) direct confirmations, (2) corroborating patterns, (3) plausible framing.\n"
"- If headline is future-tense, argue likelihood from precedent.\n"
"\n"
"Output EXACTLY:\n"
"Claims:\n"
"Support (cite IDs):\n"
"Rebuttal targets (quote + ID):\n"
"Constraints: ≤140 words, no sentence reuse."
)


CHALLENGER_SYS = (
"You are Challenger B (CON side). Your job is to argue that the headline is INACCURATE or MISLEADING.\n"
"Rules:\n"
"- Emphasize flaws, gaps, overclaims, or lack of confirmation.\n"
"- Never flip sides. Use only evidence IDs R1…Rn. No fabrication or links.\n"
"- Attack angles: (1) no official confirmation, (2) weak sourcing, (3) stats misread,\n"
"  (4) wrong context/tense, (5) selective evidence.\n"
"\n"
"Output EXACTLY:\n"
"Claims:\n"
"Support (cite IDs):\n"
"Rebuttal targets (quote + ID):\n"
"Constraints: ≤140 words, no sentence reuse."
)


# ── Judge system prompt ──────────────────────────────────────────────────────
JUDGE_SYS = (
"You are an impartial judge analyzing a debate about a headline's accuracy.\n"
"Two agents have debated:\n"
"- Agent A (Verifier): Argues the headline is ACCURATE\n"
"- Agent B (Challenger): Argues the headline is INACCURATE/MISLEADING\n"
"\n"
"Your task: Analyze their arguments and evidence citations, then make a final verdict.\n"
"\n"
"Rules:\n"
"- Consider argument quality, evidence strength, and logical reasoning\n"
"- Use ONLY the provided evidence (R1, R2, etc.) - do not add external knowledge\n"
"- Judge based on what the evidence actually supports, not agent roles\n"
"- Be objective - the better argument wins regardless of which agent made it\n"
"\n"
"Return strict JSON with:\n"
"- label: 'true'|'false'|'mixed'|'unverified'\n"
"- confidence: 0-100 (integer)\n"
"- rationale: your reasoning (≤200 words)\n"
"\n"
"Labels:\n"
"- 'true': Evidence strongly supports the headline\n"
"- 'false': Evidence contradicts or refutes the headline\n"
"- 'mixed': Evidence supports some parts but contradicts others\n"
"- 'unverified': Insufficient or inconclusive evidence"
)

# ── Control judge (single-pass) ──────────────────────────────────────────────
CONTROL_SYS = (
"You are the control fact-checker. Determine if the headline is TRUE, FALSE, MIXED, or UNVERIFIED using ONLY evidence IDs R1…Rn.\n"
"- TRUE: The headline is accurate and supported by evidence\n"
"- FALSE: The headline is inaccurate or misleading\n"
"- MIXED: The headline has both accurate and inaccurate elements\n"
"- UNVERIFIED: Insufficient evidence to make a determination\n"
"Return strict JSON with: label (true|false|mixed|unverified), confidence (0-100), rationale (≤120 words).\n"
"If evidence is conflicting, incomplete, or speculative, choose 'unverified'."
)


def _fmt_evidence(ev):
    if not ev:
        return "No evidence provided."
    out = []
    for i, item in enumerate(ev, 1):
        if isinstance(item, dict):
            eid = item.get("id") or f"R{i}"
            txt = item.get("text") or item.get("summary") or item.get("title", "")
        else:  # user-typed  id|text
            eid, txt = (str(item).split("|", 1) + [""])[:2]
        out.append(f"{eid}: {txt}")
    return "\n".join(out)

def control_verdict(client, headline, evidence=None):
    ev_txt = _fmt_evidence(evidence or [])
    prompt = (
        CONTROL_SYS
        + "\n\nHeadline:\n" + headline
        + "\n\nEvidence:\n" + ev_txt
        + "\n\nOutput JSON only."
    )
    raw = client.models.generate_content(
        model=MODEL_JUDGE,
        contents=prompt,          # single string
        config={"temperature": 0.0}
    ).text.strip()

    # tolerate bad JSON
    try:
        data = json.loads(raw)
    except Exception:
        low = raw.lower()
        if "misinformation" in low or "false" in low:
            label = "false"
        elif "information" in low or "true" in low:
            label = "true"
        else:
            label = "uncertain"
        data = {"label": label, "confidence": 0.5, "rationale": raw[:400]}

    # Normalize labels to match judge output (true/false/mixed/unverified)
    label = data.get("label", "uncertain").lower()
    if label in ["information", "true"]:
        label = "true"
    elif label in ["misinformation", "false"]:
        label = "false"
    elif label in ["mixed"]:
        label = "mixed"
    else:
        label = "unverified"
    
    data["label"] = label
    try:
        confidence = float(data.get("confidence", 0.5))
        if confidence <= 1.0:  # 0-1 scale, convert to 0-100
            confidence = int(confidence * 100)
        else:  # already 0-100 scale
            confidence = int(confidence)
        data["confidence"] = max(0, min(100, confidence))
    except Exception:
        data["confidence"] = 50
    data["rationale"] = data.get("rationale", "")[:500]
    return data

# ── Agent turn + text generation ─────────────────────────────────────────────
def _gen_text(client: genai.Client, model: str, prompt_text: str, temperature: float) -> str:
    return client.models.generate_content(
        model=model,
        contents=prompt_text,   # string only
        config={"temperature": temperature}
    ).text.strip()

def _agent_turn(client, sys_prompt, headline, transcript, evidence):
    if not evidence:
        return "Refusal: No evidence provided."
    ev = "Evidence:\n" + "\n".join(f"- {e['id']}: {e['text']}" for e in evidence[:8])
    user = (
        f"Headline: {headline}\n"
        f"Transcript:\n{transcript or '(none)'}\n"
        f"{ev}\n"
        "Your turn. Quote opponent in <rebut>…</rebut> and cite an ID."
    )
    prompt = sys_prompt + "\n\n" + user
    out = _gen_text(client, MODEL_AGENT, prompt, 0.7)
    # light repetition guard
    marker = f"\n[{ 'A' if 'Verifier' in sys_prompt else 'B'}]\n"
    last_idx = transcript.rfind(marker)
    if last_idx != -1:
        prev = transcript[last_idx+len(marker):].strip()[:300]
        if prev and out[:160].lower() == prev[:160].lower():
            out = _gen_text(client, MODEL_AGENT, prompt + "\nAvoid repetition. Add one new argument and one new rebuttal.", 0.6)
    return out

# ── AI Judge Agent ───────────────────────────────────────────────────────────
def judge_verdict(client: genai.Client, headline: str, transcript: str, evidence=None) -> dict:
    """AI judge analyzes the debate and makes a verdict"""
    
    # Format evidence for the judge
    ev_txt = _fmt_evidence(evidence or [])
    
    # Create judge prompt
    prompt = (
        JUDGE_SYS
        + f"\n\nHeadline to evaluate:\n{headline}"
        + f"\n\nEvidence available:\n{ev_txt}"
        + f"\n\nDebate transcript:\n{transcript}"
        + "\n\nAnalyze the debate and provide your verdict in JSON format."
    )
    
    # Get judge response
    raw = _gen_text(client, MODEL_JUDGE, prompt, 0.1)  # Low temperature for consistency
    
    # Parse JSON response with fallback
    try:
        data = json.loads(re.sub(r"```json|```", "", raw).strip())
    except Exception:
        # Fallback parsing if JSON is malformed
        raw_lower = raw.lower()
        if "false" in raw_lower or "misleading" in raw_lower or "inaccurate" in raw_lower:
            label = "false"
        elif "true" in raw_lower or "accurate" in raw_lower or "correct" in raw_lower:
            label = "true"
        elif "mixed" in raw_lower or "partial" in raw_lower:
            label = "mixed"
        else:
            label = "unverified"
        
        data = {
            "label": label,
            "confidence": 60,
            "rationale": raw[:300]
        }
    
    # Validate and clean up the response
    label = str(data.get("label", "unverified")).lower()
    if label not in {"true", "false", "mixed", "unverified"}:
        label = "unverified"
    
    try:
        confidence = int(data.get("confidence", 60))
        confidence = max(0, min(100, confidence))
    except:
        confidence = 60
    
    rationale = str(data.get("rationale", "Judge analysis completed"))[:400]
    
    # Extract evidence citations from transcript
    cited = re.findall(r"\bR\d+\b", transcript or "")
    cited = [c for i, c in enumerate(cited) if c not in cited[:i]][:6]  # Remove duplicates
    
    return {
        "label": label,
        "confidence": confidence,
        "rationale": rationale,
        "evidence_used": cited,
        "judge_method": "ai_analysis"
    }

# ── Orchestrator ─────────────────────────────────────────────────────────────
def run_misinfo(client, headline, evidence=None, rounds=2):
    t = ""
    a = _agent_turn(client, VERIFIER_SYS, headline, t, evidence); t += f"\n[A]\n{a}\n"
    b = _agent_turn(client, CHALLENGER_SYS, headline, t, evidence); t += f"\n[B]\n{b}\n"
    for _ in range(rounds - 1):
        a = _agent_turn(client, VERIFIER_SYS, headline, t, evidence); t += f"\n[A]\n{a}\n"
        b = _agent_turn(client, CHALLENGER_SYS, headline, t, evidence); t += f"\n[B]\n{b}\n"
    verdict = judge_verdict(client, headline, t, evidence)
    return t.strip(), verdict
