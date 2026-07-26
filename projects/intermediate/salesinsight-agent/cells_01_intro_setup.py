"""Grup 1: Intro, arsitektur, instalasi, imports, konfigurasi LLM."""

CELLS = [
    ("md", """
# SalesInsight Agent

**Natural-language-to-SQL data analysis agent** dengan guardrail keamanan, self-correction, visualisasi otomatis, ringkasan naratif yang ter-*grounding*, dan evaluasi berbasis *execution accuracy*.

> Notebook ini dirancang untuk dijalankan **dari atas ke bawah** (Run All). Bagian yang membutuhkan LLM akan otomatis di-*skip* dengan aman jika `OPENAI_API_KEY` belum diset, sehingga seluruh bagian deterministik (dataset, database, guardrail, security test) tetap bisa dijalankan tanpa biaya.

**Penulis:** Rezky Desyafa · **Versi:** 1.0 · **Level:** Intermediate portfolio project
"""),

    ("md", """
## 1. Ringkasan Proyek

SalesInsight Agent mengubah pertanyaan bahasa natural menjadi analisis data penjualan. Alurnya:

1. Pengguna bertanya, misal *"Bandingkan revenue kategori Electronics pada Q1 dan Q2 2025."*
2. Agent membaca **schema** dan **aturan bisnis**.
3. LLM menghasilkan **SQL** dalam bentuk *structured output* (Pydantic).
4. SQL divalidasi **sebelum** dieksekusi (SELECT-only, single statement, whitelist tabel, forced LIMIT).
5. Query dijalankan di koneksi **read-only** dengan **timeout**.
6. Jika error, agent **memperbaiki** SQL maksimal dua kali.
7. Hasil ditampilkan sebagai **tabel + grafik**, lalu diringkas dengan **ringkasan naratif** yang diverifikasi agar tidak mengarang angka.
8. Setiap eksekusi dicatat: latency, token, retry, dan estimasi biaya.

### Keputusan desain penting

- **Aturan bisnis ditegakkan di lapisan data (SQL VIEW), bukan di prompt.** LLM cukup query dari view `v_completed_sales` yang sudah mem-*filter* order `Completed`. Ini menutup risiko "SQL valid tapi salah bisnis".
- **Validasi SQL berbasis AST (SQLGlot), bukan regex.** Regex mudah tertipu komentar dan string literal; AST tidak.
- **Deterministik.** `temperature=0` untuk generasi SQL dan `seed` tetap untuk dataset, agar hasil dapat direproduksi dan dievaluasi secara adil.
"""),

    ("md", """
## 2. Arsitektur

```text
Pertanyaan (natural language)
        |
        v
  Schema + Business Context  <-- get_database_schema()
        |
        v
  LLM SQL Generator (structured output, temperature=0)
        |
        v
  SQL Guardrail (AST / SQLGlot)
   |-- SELECT / CTE-SELECT saja
   |-- Single statement
   |-- Table whitelist (termasuk view)
   |-- Forced LIMIT <= 1000
   +-- Blokir semua operasi tulis/berbahaya
        |
        v
  DuckDB Read-Only + Timeout (watchdog thread)
        |
   +----+----+
   |         |
 Error     Sukses
   |         |
   v         v
Self-      DataFrame --> Visualisasi (Matplotlib)
Correction          +--> Ringkasan naratif (grounded, faithfulness-checked)
(max 2x)            +--> Execution trace (latency, token, retry, biaya)
```
"""),

    ("md", """
## 3. Instalasi

Jalankan sel di bawah bila dependensi belum terpasang. Di lingkungan yang sudah siap, sel ini bisa dilewati.

> Catatan: pada beberapa CPU lama, NumPy 2.x gagal karena butuh baseline `X86_V2`. Gunakan `numpy<2` jika menemui `RuntimeError` terkait baseline optimizations.
"""),
    ("code", """
# !pip install -q "numpy<2" duckdb sqlglot "pydantic>=2" faker matplotlib pandas openai python-dotenv
print("Lewati sel ini jika dependensi sudah terpasang.")
""", "skip"),

    ("md", """
## 4. Imports dan Konfigurasi

Semua import dikumpulkan di satu tempat. Konfigurasi LLM dibaca dari *environment* (tidak ada API key yang di-*hardcode*). Notebook mendukung endpoint **OpenAI-compatible** apa pun lewat `OPENAI_BASE_URL`.
"""),
    ("code", """
import os, re, json, time, threading, textwrap, random
from dataclasses import dataclass, field, asdict
from typing import Optional

import numpy as np
import pandas as pd
import duckdb
import sqlglot
from sqlglot import expressions as exp
from pydantic import BaseModel, Field
import matplotlib
matplotlib.use("Agg")  # aman untuk headless; ganti ke inline saat interaktif
import matplotlib.pyplot as plt

pd.set_option("display.max_rows", 100)
pd.set_option("display.width", 120)

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

print("Imports OK. numpy", np.__version__, "| duckdb", duckdb.__version__, "| sqlglot", sqlglot.__version__)
""", "det"),

    ("md", """
### 4.1 Registry Provider LLM (banyak pilihan gratis)

Notebook ini OpenAI-compatible, jadi provider apa pun yang punya endpoint `/chat/completions` bisa dipakai hanya dengan mengganti `base_url`, `model`, dan API key.

**Provider gratis yang direkomendasikan** (semua mendukung `response_format=json_object` untuk structured output):

| Provider | Model gratis | Env API key |
|---|---|---|
| `groq` ⭐ | llama-3.3-70b-versatile | `GROQ_API_KEY` |
| `cerebras` ⭐ | llama-3.3-70b | `CEREBRAS_API_KEY` |
| `gemini` | gemini-2.0-flash | `GEMINI_API_KEY` |
| `openrouter` | llama-3.3-70b-instruct:free | `OPENROUTER_API_KEY` |
| `mistral` | mistral-small-latest | `MISTRAL_API_KEY` |
| `github` | gpt-4o-mini | `GITHUB_TOKEN` |
| `router` | hermes-claude (router pribadi) | `ROUTER_API_KEY` |
| `custom` | atur sendiri via env | `OPENAI_API_KEY` |

**Cara pakai:** set `SALESINSIGHT_PROVIDER` ke salah satu nama di atas dan isi API key-nya. Contoh Groq (paling cepat & gratis):

```bash
export SALESINSIGHT_PROVIDER=groq
export GROQ_API_KEY=gsk_...
```

Untuk provider yang belum terdaftar, pakai `custom` lalu set `OPENAI_BASE_URL`, `SALESINSIGHT_MODEL`, dan `OPENAI_API_KEY` sendiri.

`temperature=0` memastikan SQL deterministik. Harga token hanya untuk estimasi biaya di trace (provider gratis → biaya 0).
"""),
    ("code", """
# --- Registry provider: nama -> (base_url, default_model, env_api_key, harga in/out per 1K USD) ---
PROVIDERS = {
    "groq":       ("https://api.groq.com/openai/v1",            "llama-3.3-70b-versatile",              "GROQ_API_KEY",       0.0, 0.0),
    "cerebras":   ("https://api.cerebras.ai/v1",                "llama-3.3-70b",                        "CEREBRAS_API_KEY",   0.0, 0.0),
    "gemini":     ("https://generativelanguage.googleapis.com/v1beta/openai/", "gemini-2.0-flash",     "GEMINI_API_KEY",     0.0, 0.0),
    "openrouter": ("https://openrouter.ai/api/v1",              "meta-llama/llama-3.3-70b-instruct:free","OPENROUTER_API_KEY",0.0, 0.0),
    "mistral":    ("https://api.mistral.ai/v1",                 "mistral-small-latest",                 "MISTRAL_API_KEY",    0.0, 0.0),
    "github":     ("https://models.inference.ai.azure.com",     "gpt-4o-mini",                          "GITHUB_TOKEN",       0.0, 0.0),
    "router":     ("https://router.unitrade.web.id/v1",         "hermes-claude",                        "ROUTER_API_KEY",     0.0, 0.0),
    "openai":     ("https://api.openai.com/v1",                 "gpt-4o-mini",                          "OPENAI_API_KEY",     0.00015, 0.00060),
    # --- CUSTOM PROVIDER: edit baris ini atau override via env ---
    "custom":     (os.getenv("OPENAI_BASE_URL", ""),            os.getenv("SALESINSIGHT_MODEL", "gpt-4o-mini"), "OPENAI_API_KEY", 0.0, 0.0),
}

PROVIDER = os.getenv("SALESINSIGHT_PROVIDER", "custom").lower()
if PROVIDER not in PROVIDERS:
    raise ValueError(f"Provider '{PROVIDER}' tak dikenal. Pilihan: {list(PROVIDERS)}")

_base, _model, _keyenv, _pin, _pout = PROVIDERS[PROVIDER]
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL") or _base or None
MODEL_NAME      = os.getenv("SALESINSIGHT_MODEL", _model)
OPENAI_API_KEY  = os.getenv(_keyenv) or os.getenv("OPENAI_API_KEY")
PRICE_INPUT_PER_1K  = float(os.getenv("SALESINSIGHT_PRICE_IN",  str(_pin)))
PRICE_OUTPUT_PER_1K = float(os.getenv("SALESINSIGHT_PRICE_OUT", str(_pout)))

LLM_ENABLED = bool(OPENAI_API_KEY)

def _make_client():
    if not LLM_ENABLED:
        return None
    from openai import OpenAI
    kwargs = {"api_key": OPENAI_API_KEY}
    if OPENAI_BASE_URL:
        kwargs["base_url"] = OPENAI_BASE_URL
    return OpenAI(**kwargs)

client = _make_client()
print(f"Provider: {PROVIDER} | model: {MODEL_NAME} | base_url: {OPENAI_BASE_URL or 'default'}")
print("LLM:", "AKTIF" if LLM_ENABLED else f"NONAKTIF — set {_keyenv} untuk mengaktifkan")
""", "det"),
]

