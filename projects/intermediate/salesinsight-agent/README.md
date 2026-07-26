# SalesInsight Agent

> Intermediate portfolio project — a natural-language-to-SQL data analysis agent with safety guardrails and evaluation.

## Summary

SalesInsight Agent is an LLM agent prototype that answers sales-data questions in natural language. It reads the database schema, generates SQL, validates the query for safety, executes it against a read-only connection, self-corrects on error, then returns a table, chart, and narrative summary.

The first version is built entirely in a single Jupyter notebook (`sales_insight_agent.ipynb`) so the data flow, agent loop, tool use, guardrails, and evaluation are transparent and easy to study.

## What this project demonstrates

- LLM tool use and function calling
- Text-to-SQL with structured output (Pydantic)
- SQL safety guardrails (SELECT-only, table whitelist, forced LIMIT, blocked operations)
- A bounded self-correction loop (max 2 retries)
- Agent evaluation with execution accuracy against ground-truth SQL
- Observability: latency, token usage, retries, and cost per question

## Related roadmap modules

This project applies and reinforces:

- [07 — AI Agents](../../../roadmap/07-ai-agents/) — tools, agent loop, tool calling
- [09 — LLM Evaluation](../../../roadmap/09-llm-evaluation/) — execution accuracy, observability
- [11 — Security and Responsible AI](../../../roadmap/11-security-and-responsible-ai/) — SQL guardrails, prompt-injection surface
- [05 — LLM Fundamentals](../../../roadmap/05-llm-fundamentals/) — structured output, tool calling

## Documents

- [PRD.md](PRD.md) — full product requirements document (v1.0)

## Status

`Planning` — PRD complete, implementation not started.

## Tech stack

Jupyter, Python, Pandas/NumPy, Faker, DuckDB, SQLGlot, Pydantic, Matplotlib, python-dotenv.
LLM served via an OpenAI-compatible endpoint.

## Build phases

1. **Phase 1 — Notebook prototype** (this repo): dataset, DuckDB, SQL generator, guardrails, executor, self-correction, visualization, summary, evaluation.
2. **Phase 2 — Modular Python application**: split into `agent/`, `tools/`, `guardrails/`, `database/`, `visualization/`, `evaluation/`.
3. **Phase 3 — Web application**: FastAPI + Streamlit/Next.js, PostgreSQL, Redis.
4. **Phase 4 — Production agent**: auth, RBAC, row-level security, audit log, monitoring, cost budgets, container deployment.
