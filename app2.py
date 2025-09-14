# app2.py - Simple Misinformation Checker UI based on agents2.py
import os
import json
import gradio as gr
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Import from agents2.py
from agents2 import make_client, run_misinfo, control_verdict
from researcher import build_evidence as build_wiki_evidence
from news_researcher import build_news_evidence

# Load environment variables
load_dotenv()

# Benchmark test cases
BENCHMARK_TESTS = [
    # Technology
    ("Apple releases Vision Pro 2.0", "FALSE", "no such release confirmed"),
    ("OpenAI launches GPT-5", "TRUE", "launched in 2024"),
    ("Tesla announces fully autonomous Level 5 car", "FALSE", "not reached full autonomy"),
    ("Meta discontinues the Quest 3 headset", "FALSE", "Quest 3 still sold"),
    ("Google unveils Pixel 10 Pro", "TRUE", "released Oct 2024"),
    
    # Entertainment
    ("Starset just released their new album", "TRUE", "released album Horizons II in Aug 2025"),
    ("Taylor Swift retires from touring", "FALSE", "still touring, no retirement announced"),
    ("Netflix cancels Stranger Things spin-off", "FALSE", "spin-off still in development"),
    
    # Science & Space
    ("NASA confirms liquid water lakes on Mars", "FALSE", "no confirmed lakes, only ice deposits"),
    ("SpaceX successfully lands Starship after orbital flight", "TRUE", "landed July 2024"),
    
    # Politics & News
    ("UK officially rejoins the EU", "FALSE", "no such decision made"),
    ("India becomes world's third-largest economy by nominal GDP", "TRUE", "confirmed 2025 IMF data"),
]

def _now_ist_iso():
    """Get current time in IST format"""
    return (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M IST")

def parse_evidence(evidence_text: str):
    """Parse evidence text into structured format"""
    items = []
    if not evidence_text:
        return items
    
    for line in evidence_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if "|" in line:
            eid, txt = line.split("|", 1)
            items.append({"id": eid.strip(), "text": txt.strip()})
        else:
            items.append({"id": f"U{len(items)+1}", "text": line})
    return items

def format_evidence_sources(evidence):
    """Format evidence sources for display"""
    if not evidence:
        return "No evidence sources provided."
    
    formatted = "📚 **Evidence Sources Used in Debate:**\n\n"
    for i, item in enumerate(evidence, 1):
        if isinstance(item, dict):
            eid = item.get("id", f"R{i}")
            text = item.get("text", "")
            title = item.get("title", "")
            url = item.get("url", "")
            
            formatted += f"**{eid}**: "
            if title:
                formatted += f"*{title}*\n"
            formatted += f"{text[:200]}{'...' if len(text) > 200 else ''}\n"
            if url:
                formatted += f"🔗 Source: {url}\n"
            formatted += "---\n"
        else:
            formatted += f"**R{i}**: {str(item)[:200]}{'...' if len(str(item)) > 200 else ''}\n---\n"
    
    return formatted

def analyze_headline(headline, evidence_text, rounds, auto_research, max_sources, source_type):
    """Main function to analyze a headline for misinformation - runs both debate and control"""
    try:
        # Validate inputs
        if not headline or not headline.strip():
            return "ERROR: No headline provided", "", "0%", "{}", "", "ERROR: No headline", "{}", "No evidence"
        
        if not client:
            return "ERROR: API client not initialized", "", "0%", "{}", "", "ERROR: Not initialized", "{}", "No evidence"
        
        # Parse manual evidence
        evidence = parse_evidence(evidence_text)
        
        # Auto research if enabled
        if auto_research:
            try:
                if source_type == "Recent News":
                    research_items, _, _ = build_news_evidence(headline, k=max_sources)
                else:  # Wikipedia
                    research_items, _, _ = build_wiki_evidence(headline, k=max_sources)
                evidence.extend(research_items)
            except Exception as e:
                print(f"Research error: {e}")
                # Continue without auto research
        
        # Run BOTH analyses in parallel
        print("Running debate analysis...")
        transcript, verdict = run_misinfo(client, headline, evidence, rounds=rounds)
        
        print("Running control analysis...")
        control_result = control_verdict(client, headline, evidence)
        
        # Format main results
        label = verdict.get("label", "uncertain").upper()
        confidence = verdict.get("confidence", 0)
        conf_text = f"Confidence: {confidence}%"
        timestamp = f"Analysis completed at {_now_ist_iso()}"
        verdict_json = json.dumps(verdict, indent=2, ensure_ascii=False)
        
        # Format control results
        control_label = control_result.get("label", "uncertain").upper()
        control_json = json.dumps(control_result, indent=2, ensure_ascii=False)
        
        # Format evidence sources for display
        evidence_display = format_evidence_sources(evidence)
        
        return label, timestamp, conf_text, verdict_json, transcript, control_label, control_json, evidence_display
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"Analysis error: {e}")
        import traceback
        traceback.print_exc()
        error_json = json.dumps({"error": str(e)}, indent=2)
        return "ERROR", error_msg, "0%", error_json, str(e), "ERROR", error_json, "Error retrieving evidence"

def get_control_verdict(headline, evidence_text):
    """Get a simple control verdict without debate"""
    try:
        if not headline or not headline.strip():
            return "ERROR: No headline provided", "{}"
        
        if not client:
            return "ERROR: API client not initialized", "{}"
        
        evidence = parse_evidence(evidence_text)
        result = control_verdict(client, headline, evidence)
        
        label = result.get("label", "uncertain").upper()
        result_json = json.dumps(result, indent=2, ensure_ascii=False)
        
        return label, result_json
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"Control verdict error: {e}")
        return "ERROR", json.dumps({"error": str(e)}, indent=2)

def run_benchmark_test(test_idx):
    """Run a specific benchmark test"""
    if test_idx < 0 or test_idx >= len(BENCHMARK_TESTS):
        return "Invalid test index", "", "", "{}", "", "ERROR", "{}"
    
    headline, expected, description = BENCHMARK_TESTS[test_idx]
    print(f"Running benchmark test {test_idx + 1}: {headline}")
    
    # Run the analysis without auto-research for consistent testing
    try:
        evidence = []  # No additional evidence for benchmark tests
        
        # Run debate analysis
        transcript, verdict = run_misinfo(client, headline, evidence, rounds=2)
        
        # Run control analysis
        control_result = control_verdict(client, headline, evidence)
        
        # Format results
        debate_label = verdict.get("label", "uncertain").upper()
        debate_confidence = verdict.get("confidence", 0)
        debate_conf_text = f"Confidence: {debate_confidence}%"
        timestamp = f"Benchmark test completed at {_now_ist_iso()}"
        debate_json = json.dumps(verdict, indent=2, ensure_ascii=False)
        
        control_label = control_result.get("label", "uncertain").upper()
        control_json = json.dumps(control_result, indent=2, ensure_ascii=False)
        
        # Check if results match expected
        expected_normalized = expected.upper()
        debate_match = "✅" if debate_label == expected_normalized else "❌"
        control_match = "✅" if control_label == expected_normalized else "❌"
        
        # Update the headline display to show test info
        test_headline = f"TEST {test_idx + 1}: {headline}\nExpected: {expected} | Debate: {debate_label} {debate_match} | Control: {control_label} {control_match}"
        
        # Format evidence for display
        evidence_display = format_evidence_sources(evidence)
        
        return test_headline, timestamp, debate_conf_text, debate_json, transcript, control_label, control_json, evidence_display
        
    except Exception as e:
        error_msg = f"Benchmark test error: {str(e)}"
        print(f"Benchmark test {test_idx + 1} error: {e}")
        error_json = json.dumps({"error": str(e)}, indent=2)
        return f"ERROR in test {test_idx + 1}", error_msg, "0%", error_json, str(e), "ERROR", error_json, "Error retrieving evidence"

def run_all_benchmarks():
    """Run all benchmark tests and return summary"""
    results = []
    for i in range(len(BENCHMARK_TESTS)):
        headline, expected, description = BENCHMARK_TESTS[i]
        try:
            evidence = []
            transcript, verdict = run_misinfo(client, headline, evidence, rounds=2)
            control_result = control_verdict(client, headline, evidence)
            
            debate_label = verdict.get("label", "uncertain").upper()
            control_label = control_result.get("label", "uncertain").upper()
            expected_normalized = expected.upper()
            
            debate_match = debate_label == expected_normalized
            control_match = control_label == expected_normalized
            
            results.append({
                "test": i + 1,
                "headline": headline,
                "expected": expected,
                "debate_result": debate_label,
                "control_result": control_label,
                "debate_correct": debate_match,
                "control_correct": control_match,
                "description": description
            })
            
            print(f"Test {i + 1}: {headline} | Expected: {expected} | Debate: {debate_label} {'✅' if debate_match else '❌'} | Control: {control_label} {'✅' if control_match else '❌'}")
            
        except Exception as e:
            print(f"Test {i + 1} failed: {e}")
            results.append({
                "test": i + 1,
                "headline": headline,
                "expected": expected,
                "debate_result": "ERROR",
                "control_result": "ERROR",
                "debate_correct": False,
                "control_correct": False,
                "description": f"Error: {str(e)}"
            })
    
    # Calculate accuracy
    debate_correct = sum(1 for r in results if r["debate_correct"])
    control_correct = sum(1 for r in results if r["control_correct"])
    total = len(results)
    
    summary = f"""
BENCHMARK RESULTS:
Debate Analysis: {debate_correct}/{total} correct ({debate_correct/total*100:.1f}%)
Control Analysis: {control_correct}/{total} correct ({control_correct/total*100:.1f}%)

Detailed Results:
"""
    for r in results:
        summary += f"Test {r['test']}: {r['headline'][:50]}... | Expected: {r['expected']} | Debate: {r['debate_result']} {'✅' if r['debate_correct'] else '❌'} | Control: {r['control_result']} {'✅' if r['control_correct'] else '❌'}\n"
    
    return summary

# Initialize client
print("Initializing Misinformation Checker...")
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY not found in environment!")
    client = None
else:
    print(f"API Key found: {api_key[:10]}...")
    try:
        client = make_client(api_key)
        print("✅ Client initialized successfully")
    except Exception as e:
        print(f"❌ Error creating client: {e}")
        client = None

# Create Gradio Interface
with gr.Blocks(title="Misinformation Checker v2", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🔍 Misinformation Checker")
    gr.Markdown("Analyze headlines for misinformation using AI-powered debate and fact-checking")
    
    with gr.Tab("Full Analysis (Debate)"):
        with gr.Row():
            with gr.Column(scale=2):
                headline_input = gr.Textbox(
                    label="Headline/Claim to Analyze",
                    placeholder="Enter a news headline or claim to fact-check...",
                    lines=2
                )
                
                evidence_input = gr.Textbox(
                    label="Additional Evidence (Optional)",
                    placeholder="Format: ID|Evidence text (one per line)\nExample: E1|Apple announced new iPhone",
                    lines=4
                )
                
                with gr.Row():
                    auto_research = gr.Checkbox(
                        label="Auto Research",
                        value=True,
                        info="Automatically gather evidence from external sources"
                    )
                    source_type = gr.Dropdown(
                        choices=["Recent News", "Wikipedia"],
                        value="Recent News",
                        label="Research Source"
                    )
                
                with gr.Row():
                    max_sources = gr.Slider(
                        minimum=1,
                        maximum=10,
                        value=5,
                        step=1,
                        label="Max Research Sources"
                    )
                    rounds = gr.Slider(
                        minimum=1,
                        maximum=5,
                        value=2,
                        step=1,
                        label="Debate Rounds"
                    )
                
                analyze_btn = gr.Button("🔍 Analyze for Misinformation", variant="primary", size="lg")
            
            with gr.Column(scale=1):
                gr.Markdown("### 🏛️ Debate Verdict")
                verdict_display = gr.Textbox(
                    label="Main Verdict (Debate)",
                    interactive=False,
                    lines=1
                )
                confidence_display = gr.Textbox(
                    label="Confidence",
                    interactive=False,
                    lines=1
                )
                
                gr.Markdown("### ⚡ Control Verdict")
                control_verdict_display = gr.Textbox(
                    label="Control Verdict (Quick)",
                    interactive=False,
                    lines=1
                )
                
                timestamp_display = gr.Textbox(
                    label="Timestamp",
                    interactive=False,
                    lines=1
                )
        
        with gr.Row():
            with gr.Column():
                verdict_json = gr.Code(
                    label="Debate Analysis (JSON)",
                    language="json",
                    lines=15
                )
            with gr.Column():
                control_json_display = gr.Code(
                    label="Control Analysis (JSON)",
                    language="json",
                    lines=15
                )
        
        with gr.Row():
            with gr.Column():
                evidence_sources = gr.Markdown(
                    label="Evidence Sources",
                    value="Evidence sources will appear here after analysis."
                )
            with gr.Column():
                transcript_display = gr.Textbox(
                    label="Debate Transcript",
                    lines=12,
                    max_lines=20
                )
    
    with gr.Tab("Quick Check (Control)"):
        with gr.Row():
            with gr.Column():
                control_headline = gr.Textbox(
                    label="Headline/Claim",
                    placeholder="Enter headline for quick fact-check...",
                    lines=2
                )
                control_evidence = gr.Textbox(
                    label="Evidence (Optional)",
                    placeholder="Format: ID|Evidence text (one per line)",
                    lines=3
                )
                control_btn = gr.Button("⚡ Quick Check", variant="secondary")
            
            with gr.Column():
                control_verdict_quick = gr.Textbox(
                    label="Quick Verdict",
                    interactive=False
                )
                control_json_quick = gr.Code(
                    label="Analysis Details",
                    language="json",
                    lines=10
                )
    
    with gr.Tab("Benchmark Testing"):
        gr.Markdown("## 🧪 Automated Benchmark Testing")
        gr.Markdown("Test the system against known true/false headlines to evaluate accuracy.")
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Individual Tests")
                test_checkboxes = []
                for i, (headline, expected, desc) in enumerate(BENCHMARK_TESTS):
                    checkbox = gr.Checkbox(
                        label=f"Test {i+1}: {headline} (Expected: {expected})",
                        value=False
                    )
                    test_checkboxes.append(checkbox)
                
                with gr.Row():
                    run_all_btn = gr.Button("🚀 Run All Benchmarks", variant="primary")
                    clear_tests_btn = gr.Button("Clear All", variant="secondary")
            
            with gr.Column():
                benchmark_results = gr.Textbox(
                    label="Benchmark Results",
                    lines=20,
                    max_lines=30
                )
        
        # Auto-run individual tests when checkboxes are clicked
        for i, checkbox in enumerate(test_checkboxes):
            checkbox.change(
                fn=lambda checked, test_idx=i: run_benchmark_test(test_idx) if checked else ("", "", "", "{}", "", "", "{}", ""),
                inputs=[checkbox],
                outputs=[
                    headline_input,
                    timestamp_display,
                    confidence_display,
                    verdict_json,
                    transcript_display,
                    control_verdict_display,
                    control_json_display,
                    evidence_sources
                ]
            )
        
        run_all_btn.click(
            fn=run_all_benchmarks,
            outputs=[benchmark_results]
        )
        
        def clear_all_tests():
            return [False] * len(BENCHMARK_TESTS)
        
        clear_tests_btn.click(
            fn=clear_all_tests,
            outputs=test_checkboxes
        )
    
    with gr.Tab("About"):
        gr.Markdown("""
        ## How it works
        
        ### Dual Analysis Approach
        This app runs **TWO DIFFERENT ANALYSES** simultaneously for comprehensive fact-checking:
        
        #### 🏛️ Debate Analysis (Main)
        - **Step 1**: Optionally gathers evidence from news sources or Wikipedia
        - **Step 2**: Two AI agents debate the headline:
          - **Agent A (Verifier)**: Argues the headline is accurate
          - **Agent B (Challenger)**: Argues the headline is misleading
        - **Step 3**: A judge analyzes the debate and makes a final verdict
        - **Result**: More thorough but slower analysis
        
        #### ⚡ Control Analysis (Quick)
        - Single AI judge directly analyzes the headline and evidence
        - No debate process - direct assessment
        - **Result**: Faster analysis for comparison
        
        ### Comparing Results
        - **Agreement**: When both analyses agree, confidence is higher
        - **Disagreement**: Indicates complex or borderline cases requiring human judgment
        - **Different approaches**: Debate vs. Direct assessment may yield different insights
        
        ### Verdict Types
        - **TRUE**: Information appears to be accurate
        - **FALSE**: Information appears to be misleading/false
        - **MIXED**: Conflicting evidence or partial truth
        - **UNVERIFIED**: Insufficient evidence to make determination
        
        ### Benchmark Testing
        The benchmark tab contains 12 test cases covering technology, entertainment, science, and politics.
        Each test has a known expected result to evaluate system accuracy.
        
        ---
        *Powered by Gemini AI with evidence from Wikipedia/Google News*
        """)
    
    # Event handlers
    analyze_btn.click(
        fn=analyze_headline,
        inputs=[
            headline_input,
            evidence_input,
            rounds,
            auto_research,
            max_sources,
            source_type
        ],
        outputs=[
            verdict_display,
            timestamp_display,
            confidence_display,
            verdict_json,
            transcript_display,
            control_verdict_display,
            control_json_display,
            evidence_sources
        ]
    )
    
    control_btn.click(
        fn=get_control_verdict,
        inputs=[control_headline, control_evidence],
        outputs=[control_verdict_quick, control_json_quick]
    )

if __name__ == "__main__":
    print(f"Starting Misinformation Checker at {_now_ist_iso()}")
    print("Client status:", "✅ Ready" if client else "❌ Not initialized")
    demo.launch(
        server_name="127.0.0.1",
        server_port=7862,
        share=False,
        show_error=True
    )
