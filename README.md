# 🔍 AI Misinformation Checker

A comprehensive misinformation detection system that uses AI-powered debate and fact-checking to analyze news headlines and claims for accuracy.

## 🌟 Features

### Dual Analysis System
- **🏛️ Debate Analysis**: Two AI agents debate the headline (pro vs. con) while a judge makes the final verdict
- **⚡ Control Analysis**: Direct single-pass fact-checking for comparison
- **📊 Benchmark Testing**: Automated testing with 12 predefined test cases

### Smart Evidence Gathering
- **📰 News Research**: Automatic evidence collection from Google News RSS feeds
- **📚 Wikipedia Research**: Evidence gathering from Wikipedia articles
- **🔍 Source Display**: Clear visualization of all evidence sources used in analysis

### Interactive UI
- Clean, intuitive Gradio interface
- Real-time analysis with progress tracking
- Detailed JSON outputs and debate transcripts
- Benchmark testing with accuracy metrics

## 🚀 Quick Start

### Installation

1. **Clone the repository**
```bash
git clone [<your-repo-url>](https://github.com/AnshdeepSachdeva/ai-misinformation-checker.git)
cd ai-misinformation-checker
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

4. **Run the application**
```bash
python app2.py
```

5. **Open your browser**
Navigate to `http://127.0.0.1:7862` to use the application.

## 🛠️ Project Structure

```
misinformation-checker/
├── app2.py                 # Main Gradio application
├── agents2.py              # AI agents and debate logic
├── news_researcher.py      # Google News evidence collection
├── researcher.py           # Wikipedia evidence collection
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables (create this)
└── README.md              # This file
```

## 📊 How It Works

### 1. Debate Analysis Process
1. **Evidence Collection**: Automatically gathers relevant information from news sources or Wikipedia
2. **Agent Debate**: 
   - **Verifier Agent (A)**: Argues that the headline is accurate
   - **Challenger Agent (B)**: Argues that the headline is misleading/false
3. **Judge Analysis**: An AI judge analyzes the debate and makes a final verdict

### 2. Control Analysis
- Single AI judge directly analyzes the headline and evidence
- Provides a baseline for comparison with the debate approach

### 3. Verdict Types
- **TRUE**: Information appears to be accurate
- **FALSE**: Information appears to be misleading/false  
- **MIXED**: Conflicting evidence or partial truth
- **UNVERIFIED**: Insufficient evidence to make determination

## 🧪 Benchmark Testing

The system includes 12 predefined test cases covering:

### Technology
- Apple Vision Pro 2.0 release
- OpenAI GPT-5 launch
- Tesla autonomous vehicles
- Meta Quest 3 discontinuation
- Google Pixel 10 Pro

### Entertainment  
- Starset album releases
- Taylor Swift retirement
- Netflix show cancellations

### Science & Space
- NASA Mars discoveries
- SpaceX Starship achievements

### Politics & News
- UK-EU relations
- Global economic rankings

## 📈 Usage Examples

### Basic Analysis
1. Enter a headline: "Apple releases Vision Pro 2.0"
2. Enable auto-research 
3. Click "Analyze for Misinformation"
4. View both debate and control verdicts

### Custom Evidence
1. Enter headline and custom evidence in format: `ID|Evidence text`
2. Disable auto-research to use only your evidence
3. Run analysis

### Benchmark Testing
1. Go to "Benchmark Testing" tab
2. Check individual test cases or click "Run All Benchmarks"
3. View accuracy metrics and detailed results

## 🔧 Configuration

### Environment Variables
- `GEMINI_API_KEY`: Your Google Gemini API key (required)

### Customization Options
- **Debate Rounds**: 1-5 rounds of agent debate
- **Max Sources**: 1-10 automatic research sources
- **Source Type**: Recent News or Wikipedia
- **Evidence Format**: Custom evidence with ID|Text format

## 📊 API Requirements

- **Google Gemini API**: Used for all AI analysis
- **Google News RSS**: For news evidence collection
- **Wikipedia API**: For encyclopedia evidence collection

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimers

- This tool is for research and educational purposes
- AI-generated verdicts should not be considered definitive fact-checking
- Always verify important information through multiple reliable sources
- The system's accuracy depends on the quality and availability of evidence

## 🔮 Future Enhancements

- [ ] Support for additional AI models
- [ ] More sophisticated evidence weighting
- [ ] Multi-language support
- [ ] Enhanced benchmark test suites
- [ ] Integration with fact-checking databases
- [ ] Real-time monitoring of trending claims

## 📞 Support

For questions, issues, or contributions, please open an issue on GitHub or contact the maintainers.

---

*Powered by Google Gemini AI with evidence from Wikipedia and Google News*
