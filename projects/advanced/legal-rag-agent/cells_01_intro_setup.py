"""Sel 1: konteks proyek dan setup."""
CELLS = [
("md", """
# LexID Agent — Agentic RAG Hukum Ketenagakerjaan Indonesia

Notebook ini membangun PoC end-to-end sesuai PRD:

1. ingest PDF resmi ketenagakerjaan;
2. chunking **per-pasal**;
3. retrieval lexical/hybrid baseline;
4. version graph untuk pasal yang diubah;
5. agent workflow multi-step yang bounded;
6. citation verifier + refusal policy;
7. evaluasi retrieval dan sitasi.

> ⚠️ **Bukan nasihat hukum.** Ini alat bantu riset regulasi. Jawaban selalu harus diverifikasi pada dokumen resmi dan profesional hukum.
"""),
("md", """
## 1. Arsitektur dan batasan PoC

```text
Pertanyaan → scope guard → planner → retrieve → version resolver →
answer synthesis → citation verifier → answer/refusal
```

Versi ini sengaja deterministic untuk membuktikan fondasi. Planner/synthesis LLM bersifat **opsional**; tanpa API key, notebook tetap menjalankan retrieval, version resolution, verifier, security test, dan evaluasi.
"""),
("code", """
from pathlib import Path
import os, re, json, time, hashlib
from dataclasses import asdict
import fitz
import pandas as pd
from lexid.core import (
    ArticleChunk, Citation, CitationVerifier, HybridRetriever,
    VersionGraph, VerifiedAnswer, build_verified_answer, is_in_scope, parse_articles,
)

ROOT = Path.cwd()
RAW = ROOT / "data" / "raw"
SEED = 42
PDF_FILES = {
    "UU-13-2003": RAW / "UU-13-2003-Ketenagakerjaan.pdf",
    "UU-6-2023": RAW / "UU-6-2023-CiptaKerja.pdf",
    "PP-35-2021": RAW / "PP-35-2021-Ketenagakerjaan.pdf",
}
print("Root:", ROOT)
print("Korpus tersedia:", {k: v.exists() for k, v in PDF_FILES.items()})
""", "det"),
("md", """
## 2. Provider LLM (opsional)

Untuk portfolio, retrieval/verifier lebih penting daripada LLM. Bila ingin menjalankan planner dan synthesis dengan endpoint OpenAI-compatible, set env berikut sebelum membuka Jupyter:

```bash
export OPENAI_API_KEY=...
export OPENAI_BASE_URL=https://.../v1  # opsional
export LEXID_MODEL=llama-3.3-70b-versatile
```

Model akan dipanggil dengan `temperature=0`, maksimal tiga langkah retrieval, dan tidak pernah menerima instruksi dari isi dokumen sebagai perintah.
"""),
("code", """
LLM_ENABLED = bool(os.getenv("OPENAI_API_KEY"))
MODEL_NAME = os.getenv("LEXID_MODEL", "llama-3.3-70b-versatile")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
print("LLM:", f"aktif ({MODEL_NAME})" if LLM_ENABLED else "nonaktif — deterministic mode")
""", "det"),
]
