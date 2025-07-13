<!-- original -->
# Intro

We believe within the next few years, the nature of software development will fundamentally change. Individual software engineers will leverage whole **armies** of coding agents powered by LLMs, effectively becoming managers of teams of brilliant junior engineers themselves. In this future, you will get features implemented while you sleep, or iterate on them from a high-level chat in your phone, while you are traveling or **busy with life**. 

What's the next step in this process? Tools like OpenAI's Codex give us a hint: we need to make the engineer's experimentation loop multi-threaded. With AIdeator, we've extended the workflow from Codex to work with arbitrary LLMs for chat and for the three leading CLI agents—Gemini, Claude, and Codex—for coding tasks. Each task can target a repo and run safely in sandboxed container to produce 1-5 implementations, offering alternate takes on the feature from variations in the same or different LLMs. If after iterating on the idea you are happy with the diff, you can create a pull request, ready to merge.

# Session view
- ...
- kick off some jobs

# Turns View (Session Details)
- ...
- walk through the diff

# Model selection
- ...
- show some different model options in dropdowns?

# Analytics
- ...
- Have you ever wanted empirical data on which models perform best for you? Well, with our analytics you can get it...
- (show the analytics page)

# Open source
- Because AIdeator is open-source, it is ready to evolve as new models and technologies shift the AI landscape.

---

<!-- Claude remix -->
# AIdeator: The Future of Multi-Agent Software Development

## The Vision

Within the next few years, the nature of software development will fundamentally change. Individual engineers won't just write code—they'll orchestrate **armies** of AI coding agents, effectively becoming technical leaders of brilliant virtual teams. 

Imagine:
- 🌙 Features implemented while you sleep
- 📱 High-level iteration from your phone while traveling
- 🚀 5x more productive without 5x more work
- 🧠 Multiple AI perspectives on every problem

## The Solution

AIdeator transforms the single-threaded coding experience into a **parallel, multi-agent powerhouse**. While tools like GitHub Copilot and Cursor give us AI pair programming, we're taking the next leap: AI team programming.

### Key Innovation
- **Multi-Agent Orchestration**: Run 1-5 AI agents in parallel on the same task
- **Battle-Tested Agents**: Claude, OpenAI, and Gemini CLI agents working side-by-side
- **Safe Experimentation**: Each agent runs in isolated Kubernetes containers
- **Compare & Choose**: Review multiple implementations, pick the best approach
- **One-Click Deploy**: Create pull requests directly from your chosen solution

# Demo: Session View

## Starting Your AI Team
- **Natural Language Input**: Describe your feature in plain English
- **Agent Selection**: Choose which AI models to deploy (1-5 agents)
- **Real-time Monitoring**: Watch as your AI team tackles the problem
- **Live Streaming**: See each agent's thought process and code generation

*[Demo: Create a new session for "Add dark mode to the settings page"]*

# Demo: Multi-Agent Results

## Comparing Solutions
- **Side-by-Side Views**: See how different agents approached the problem
- **Unified Diffs**: Compare code changes across all implementations
- **Quality Metrics**: Token usage, completion time, test results
- **Smart Selection**: AI-powered recommendations on the best approach

*[Demo: Show 3 different implementations of dark mode, highlighting different approaches]*

## The Power of Choice
- Agent 1: Used CSS variables for easy theming
- Agent 2: Implemented with Tailwind dark mode classes
- Agent 3: Created a full theme context with localStorage persistence

*[Walk through selecting the best implementation]*

# Flexible Model Selection

## Your AI Dream Team
- **Claude 3.5 Sonnet**: Best for complex refactoring and architecture
- **GPT-4o**: Excellent for feature implementation and debugging
- **Gemini 1.5 Pro**: Strong at data processing and optimization
- **Custom Models**: Bring your own fine-tuned models via API

## Smart Defaults
- Automatic model selection based on task type
- Cost optimization settings
- Performance vs. quality trade-offs

*[Demo: Show dropdown with model selection and variation counts]*

# Data-Driven Development

## Analytics That Matter

### Model Performance
- **Success Rates**: Which models complete tasks successfully?
- **Code Quality**: Static analysis scores by model
- **Cost Analysis**: Token usage and API costs per feature
- **Time to Solution**: Average completion times

### Your Personalized Insights
- "Claude excels at your React refactoring tasks (87% selection rate)"
- "GPT-4o is 2.3x faster for bug fixes in your Python services"
- "Gemini saves 45% on tokens for documentation tasks"

*[Demo: Show analytics dashboard with real metrics]*

## ROI Calculator
- Average time saved: 4.2 hours per feature
- Cost per feature: $0.83 in API tokens
- Developer time value: $200/hour
- **Net savings: $839.17 per feature**

# Open Source & Extensible

## Community-Driven Innovation
- **100% Open Source**: No vendor lock-in, full transparency
- **Kubernetes Native**: Deploy on any cloud or on-premise
- **Plugin Architecture**: Add new AI models as they emerge
- **Active Community**: Contributors from FAANG, startups, and academia

## Built on Modern Standards
- 🐳 **Containerized**: Each agent runs in isolated Docker containers
- ☸️ **Kubernetes Jobs**: Scalable, reliable, cloud-agnostic
- 🔄 **Real-time Streaming**: WebSocket + Server-Sent Events
- 🛡️ **Secure by Design**: Sandboxed execution, no code exposure

## Get Started Today
```bash
# One-command installation
curl -sSL https://aideator.dev/install | sh

# Start orchestrating your AI team
aideator init
aideator run "Add user authentication to my app"
```

## Join the Revolution
- 🌟 Star us on GitHub: [github.com/aideator/aideator](https://github.com/aideator/aideator)
- 💬 Discord Community: 2,500+ developers building the future
- 📚 Documentation: [docs.aideator.dev](https://docs.aideator.dev)
- 🎯 Roadmap: Claude Artifacts support, VSCode extension, AutoGPT integration
