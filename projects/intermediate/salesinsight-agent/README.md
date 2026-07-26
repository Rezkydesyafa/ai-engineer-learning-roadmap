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

`Notebook complete` — `sales_insight_agent.ipynb` dibuat, 60 sel (31 markdown, 29 code), lolos uji bagian deterministik.

## Cara menjalankan

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # numpy<2 untuk CPU tanpa baseline X86_V2
# (opsional) aktifkan LLM — pilih salah satu provider gratis di bawah:
export SALESINSIGHT_PROVIDER=groq        # groq|cerebras|gemini|openrouter|mistral|github|router|custom
export GROQ_API_KEY=gsk_...              # sesuaikan env dengan provider
jupyter lab sales_insight_agent.ipynb     # lalu Run All
```

### Provider LLM gratis (OpenAI-compatible)

Ganti provider = ganti satu env var. Semua mendukung `response_format=json_object`.

| `SALESINSIGHT_PROVIDER` | Model default | Env API key | Catatan |
|---|---|---|---|
| `groq` ⭐ | llama-3.3-70b-versatile | `GROQ_API_KEY` | Tercepat, free tier generous |
| `cerebras` ⭐ | llama-3.3-70b | `CEREBRAS_API_KEY` | Super cepat, free tier |
| `gemini` | gemini-2.0-flash | `GEMINI_API_KEY` | Free tier besar |
| `openrouter` | llama-3.3-70b-instruct:free | `OPENROUTER_API_KEY` | Model `:free`, rate-limit ketat |
| `mistral` | mistral-small-latest | `MISTRAL_API_KEY` | Free tier |
| `github` | gpt-4o-mini | `GITHUB_TOKEN` | Gratis via GitHub token |
| `router` | hermes-claude | `ROUTER_API_KEY` | Router pribadi |
| `custom` | (atur sendiri) | `OPENAI_API_KEY` | Set `OPENAI_BASE_URL` + `SALESINSIGHT_MODEL` |

**Custom provider:** `export SALESINSIGHT_PROVIDER=custom OPENAI_BASE_URL=https://.../v1 SALESINSIGHT_MODEL=nama-model OPENAI_API_KEY=...`

Tanpa `OPENAI_API_KEY`, seluruh bagian **deterministik** (dataset, DuckDB, guardrail, security test, verifikasi ground truth) tetap berjalan penuh tanpa biaya; hanya generasi SQL, demo, dan evaluasi yang otomatis di-skip.

### Verifikasi yang sudah dijalankan

Bagian non-LLM diuji end-to-end (`python build_notebook.py --test`) — 24 sel deterministik berjalan tanpa exception:

- Dataset bercerita: 20.000 order, ~59.8K item, tren YoY tertanam (revenue 2025 > 2024).
- Koneksi read-only menolak operasi tulis.
- Guardrail: 10/10 unit test lulus + forced LIMIT 1000.
- Security testing: **10/10 blocked (100%)**.
- 50 ground-truth SQL semua tereksekusi valid.

## Highlight engineering

- **Aturan bisnis di lapisan data** (view `v_completed_sales`), bukan di prompt.
- **Validasi SQL berbasis AST (SQLGlot)**, bukan regex — tahan komentar/string literal.
- **Timeout via watchdog thread** (DuckDB tak punya statement timeout bawaan).
- **Faithfulness check** — verifikasi angka ringkasan benar ada di hasil query.
- **Execution accuracy** dengan canonicalize (sort + round + multiset) agar adil.
- **Deterministik**: `temperature=0` untuk SQL, `seed` tetap untuk dataset.

## Reproduksi notebook

Notebook di-generate dari sumber modular agar rapi & teruji:

```bash
python build_notebook.py          # rakit ulang .ipynb dari cells_*.py
python build_notebook.py --test   # exec sel deterministik untuk verifikasi
```

## Documents

- [PRD.md](PRD.md) — full product requirements document (v1.0)
- [sales_insight_agent.ipynb](sales_insight_agent.ipynb) — the end-to-end notebook (60 cells)

## Tech stack

Jupyter, Python, Pandas/NumPy, Faker, DuckDB, SQLGlot, Pydantic, Matplotlib, python-dotenv.
LLM served via an OpenAI-compatible endpoint.

## Build phases

1. **Phase 1 — Notebook prototype** (this repo): dataset, DuckDB, SQL generator, guardrails, executor, self-correction, visualization, summary, evaluation.
2. **Phase 2 — Modular Python application**: split into `agent/`, `tools/`, `guardrails/`, `database/`, `visualization/`, `evaluation/`.
3. **Phase 3 — Web application**: FastAPI + Streamlit/Next.js, PostgreSQL, Redis.
4. **Phase 4 — Production agent**: auth, RBAC, row-level security, audit log, monitoring, cost budgets, container deployment.
