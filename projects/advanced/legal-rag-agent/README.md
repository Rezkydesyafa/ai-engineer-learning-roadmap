# LexID Agent — Agentic Legal RAG untuk Regulasi Indonesia

> Advanced portfolio project — version-aware retrieval + multi-step agent reasoning + citation verifier untuk hukum ketenagakerjaan Indonesia.

## Ringkasan

LexID Agent menjawab pertanyaan hukum ketenagakerjaan Indonesia dengan **dasar hukum terverifikasi** dan **status keberlakuan** tiap pasal. Bukan chatbot PDF biasa: sistem memecah pertanyaan jadi sub-pertanyaan, mengambil pasal via hybrid retrieval, menyadari pasal mana yang sudah diubah UU Cipta Kerja, lalu memverifikasi setiap sitasi sebelum menjawab.

**Pertanyaan contoh:**
> "Kalau saya di-PHK karena efisiensi setelah kerja 5 tahun, berapa pesangon saya sekarang?"

> ⚠️ **Alat bantu riset regulasi, BUKAN nasihat hukum.** Semua jawaban wajib diverifikasi ke sumber resmi.

## Kenapa agentic, bukan RAG biasa

Pertanyaan hukum jarang single-hop. Untuk menjawab pesangon PHK dengan benar, sistem harus: cari pasal pesangon di UU 13/2003 → sadar pasal itu diubah UU 6/2023 → cari rumus di PP 35/2021 → hitung → sebut semua sumber. Itu multi-step + multi-dokumen + version-aware. RAG statis pecah di sini.

## Fitur pembeda

- **Version-aware retrieval** — tahu pasal berlaku/diubah/dicabut + penggantinya (killer feature).
- **Structured citation + verifier** — tiap klaim menunjuk pasal nyata; sitasi karangan ketangkep.
- **Refusal sebagai fitur** — bukti tak cukup → menolak menjawab, bukan mengarang.
- **Hierarchical + hybrid retrieval** — chunking per-pasal, BM25 + vektor + reranker.
- **Eval legal-specific** — citation accuracy, version accuracy, refusal precision.

## Korpus v1 (domain: Ketenagakerjaan)

- UU 13/2003 Ketenagakerjaan
- UU 11/2020 & UU 6/2023 Cipta Kerja (pengubah)
- PP 35/2021 (turunan operasional)

Semua produk hukum negara → domain publik, aman untuk portofolio.

## Roadmap

| Fase | Isi |
|---|---|
| M0 | PoC notebook: ingest, chunking per-pasal, retrieval, 1 pertanyaan multi-hop |
| M1 | Version graph + version resolver |
| M2 | Query planner, agent loop, citation verifier, refusal policy |
| M3 | Eval 80–100 Q&A + tabel ablation |
| M4 | Demo Streamlit/HF Spaces + trace Langfuse |

## Modul roadmap terkait

- `roadmap/07-ai-agents/` — agent loop, tool use, multi-step reasoning
- `roadmap/06-rag/` — retrieval, chunking, hybrid search, reranking
- `roadmap/09-llm-evaluation/` — RAGAS, citation/version accuracy
- `roadmap/11-security/` — guardrail, refusal, anti-halusinasi

## Documents

- [PRD.md](PRD.md) — full product requirements document (v1.0, 14 bagian)
- [SOURCES.md](SOURCES.md) — daftar korpus resmi JDIH BPK + konteks versi
- [legal_rag_agent.ipynb](legal_rag_agent.ipynb) — end-to-end runnable PoC notebook (21 sel: 11 md, 10 code)

## Status

`M0 complete` — `legal_rag_agent.ipynb` berhasil dibuat dan diuji secara deterministik tanpa mock:
- 379 chunk pasal terurai dari 3 PDF resmi (UU 13/2003, UU 6/2023, PP 35/2021).
- Version graph mendeteksi status pasal yang diubah (mis. UU 13/2003 Psl 156 -> UU 6/2023 Psl 81).
- Citation verifier & refusal security 3/3 lulus.
- Evaluation baseline Hit@5 M0 terekam jujur (50.0%) sebagai benchmark untuk M1 (dense + reranker).

## Cara menjalankan PoC

```bash
python3 download_corpus.py
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 build_notebook.py --test  # determinis Run-All tanpa LLM
jupyter lab legal_rag_agent.ipynb  # jalankan interaktif
```
