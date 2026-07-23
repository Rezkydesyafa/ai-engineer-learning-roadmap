# AI Engineer Learning Roadmap

A structured, hands-on learning repository documenting my journey from software foundations to building production-ready AI systems.

This repository combines:

- Concise learning notes
- Jupyter Notebook experiments
- Practical exercises
- Reusable Python examples
- End-to-end portfolio projects
- Progress tracking

## Roadmap

| # | Module | Focus |
|---|---|---|
| 00 | [Foundations](roadmap/00-foundations/) | Linux, Git, Python, mathematics, SQL |
| 01 | [Software Engineering](roadmap/01-software-engineering/) | Clean code, testing, APIs, FastAPI, Docker, system design |
| 02 | [Data Engineering](roadmap/02-data-engineering/) | NumPy, pandas, cleaning, pipelines, vector databases |
| 03 | [Machine Learning](roadmap/03-machine-learning/) | Core ML, supervised/unsupervised learning, evaluation |
| 04 | [Deep Learning](roadmap/04-deep-learning/) | Neural networks, PyTorch, CNN, RNN, transformers |
| 05 | [LLM Fundamentals](roadmap/05-llm-fundamentals/) | Tokenization, prompting, structured output, tool calling |
| 06 | [Retrieval-Augmented Generation](roadmap/06-rag/) | Embeddings, chunking, retrieval, RAG evaluation |
| 07 | [AI Agents](roadmap/07-ai-agents/) | Tools, memory, MCP, single and multi-agent systems |
| 08 | [Fine-Tuning](roadmap/08-fine-tuning/) | Dataset preparation, LoRA/QLoRA, SFT |
| 09 | [LLM Evaluation](roadmap/09-llm-evaluation/) | RAG evaluation, agent evaluation, observability |
| 10 | [MLOps and Deployment](roadmap/10-mlops-and-deployment/) | Serving, Docker, CI/CD, monitoring, cloud deployment |
| 11 | [Security and Responsible AI](roadmap/11-security-and-responsible-ai/) | Prompt injection, privacy, guardrails, responsible AI |

See [ROADMAP.md](ROADMAP.md) for the complete curriculum and [PROGRESS.md](PROGRESS.md) for progress tracking.

## Repository Structure

```text
roadmap/<module>/
├── README.md              # Module objectives and topic index
├── notebooks/             # Jupyter experiments for this module
└── <topic>/
    ├── README.md          # Objectives and references
    ├── notes.md           # Personal learning notes
    ├── exercises/         # Practice tasks
    └── src/               # Reusable Python code

projects/
├── beginner/
├── intermediate/
└── advanced/
```

## Learning Workflow

1. Pick the next unchecked module in `PROGRESS.md`.
2. Read official documentation and trusted references.
3. Write concise notes in the topic's `notes.md`.
4. Experiment in the module's `notebooks/` directory.
5. Move reusable logic from notebooks into `src/`.
6. Complete exercises and tests.
7. Build a portfolio project after each major milestone.
8. Update progress and commit the learning outcome.

## Notebook Conventions

- Use descriptive names: `01_linear_regression.ipynb`.
- Keep notebooks focused on one concept.
- Restart and run all cells before committing.
- Clear large or sensitive outputs.
- Never commit API keys, tokens, private datasets, or model weights.

## Local Setup

```bash
git clone https://github.com/Rezkydesyafa/ai-engineer-learning-roadmap.git
cd ai-engineer-learning-roadmap
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
jupyter lab
```

## Portfolio Projects

Projects live under `projects/` and are grouped by difficulty. Each completed project should include:

- Problem statement
- Architecture overview
- Setup instructions
- Tests
- Evaluation results
- Screenshots or demo
- Lessons learned

## Status

This is a living repository. Content is added as each roadmap topic is studied and implemented.

## License

Learning notes and original code are available under the [MIT License](LICENSE). Third-party datasets, papers, and code retain their original licenses.
