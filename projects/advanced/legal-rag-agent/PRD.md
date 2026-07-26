# Product Requirements Document — LexID Agent

**Nama proyek:** LexID Agent (Agentic Legal RAG untuk Regulasi Indonesia)
**Versi:** 1.0
**Status:** Planning / Portfolio Project
**Domain awal:** Hukum Ketenagakerjaan Indonesia
**Tanggal:** 2026-07-26

---

## 1. Ringkasan Produk

LexID Agent adalah sistem **agentic RAG** yang menjawab pertanyaan hukum ketenagakerjaan Indonesia dengan **dasar hukum yang terverifikasi**. Berbeda dari chatbot PDF biasa, sistem ini:

1. **Memecah pertanyaan** menjadi sub-pertanyaan legal (multi-hop reasoning).
2. **Mengambil pasal** lewat hybrid retrieval (BM25 + vektor) dengan chunking per-pasal.
3. **Menyadari versi regulasi** — tahu pasal mana yang sudah diubah/dicabut oleh UU Cipta Kerja dan penggantinya.
4. **Memverifikasi sitasi** — setiap klaim wajib menunjuk pasal nyata di korpus; kalau tidak ada bukti, sistem menolak menjawab.

**Pertanyaan contoh:**
> "Kalau saya di-PHK karena efisiensi setelah kerja 5 tahun, berapa pesangon saya sekarang?"

**Prinsip inti:** di domain berisiko tinggi, **grounding + citation > fluency**. Sistem lebih baik bilang "tidak ditemukan dasar hukum yang jelas" daripada mengarang pasal.

> ⚠️ **Disclaimer produk (wajib, bukan tempelan):** LexID Agent adalah **alat bantu riset regulasi**, BUKAN nasihat hukum dan BUKAN pengganti advokat/konsultan hukum. Semua jawaban harus diverifikasi ke sumber resmi.

---

## 2. Latar Belakang & Masalah

Regulasi Indonesia sulit dinavigasi orang awam maupun profesional:

- **Struktur berjenjang:** bab → bagian → pasal → ayat → huruf. Chunking naif (per-N-token) memotong pasal sembarangan dan menghancurkan makna hukum.
- **Version drama:** UU Cipta Kerja (UU 11/2020, lalu UU 6/2023) mengubah **puluhan pasal** UU Ketenagakerjaan (UU 13/2003). Jawaban yang mengutip pasal versi lama = **salah secara hukum** meski sumbernya nyata.
- **Multi-dokumen:** satu pertanyaan sering butuh UU + PP turunan sekaligus (mis. rumus pesangon ada di PP 35/2021).
- **Risiko halusinasi tinggi:** LLM gampang mengarang nomor pasal yang terdengar meyakinkan.

RAG statis (retrieve→stuff→answer) gagal di ketiga titik ini. Perlu **agent** yang bisa retrieve berulang, resolusi versi, dan verifikasi sitasi.

---

## 3. Tujuan & Non-Tujuan

### Tujuan
- Menjawab pertanyaan hukum ketenagakerjaan dengan **dasar hukum tersitasi** dan **status keberlakuan** tiap pasal.
- Menangani **multi-hop** (UU utama → perubahan → PP turunan).
- **Menolak menjawab** saat bukti tidak memadai (refusal sebagai fitur).
- Menyediakan **eval terukur** (citation accuracy, version accuracy, faithfulness, refusal precision).

### Non-Tujuan (v1)
- **BUKAN** nasihat hukum / legal opinion.
- Tidak mencakup seluruh hukum Indonesia — **fokus satu domain** (ketenagakerjaan).
- Tidak menangani putusan pengadilan / yurisprudensi (hanya peraturan perundang-undangan).
- Tidak ada fitur multi-bahasa (Indonesia saja).
- Tidak ada fine-tuning model (memakai model instruct + retrieval).

---

## 4. Persona Pengguna (JTBD)

| Persona | Jobs-to-be-done | Kebutuhan kritis |
|---|---|---|
| **Karyawan** | "Saya mau tahu hak pesangon saya saat PHK" | Jawaban jelas + pasal + rumus, bahasa awam |
| **HR / Staf Legal UMKM** | "Saya perlu cek aturan yang berlaku sebelum ambil keputusan" | Status keberlakuan pasal, kutipan tepat |
| **Mahasiswa Hukum / Peneliti** | "Saya butuh navigasi cepat antar-pasal yang saling mengubah" | Peta versi, sitasi lengkap |

---

## 5. Ruang Lingkup Dokumen (Korpus v1)

Scope dikunci ke **hukum ketenagakerjaan Indonesia**. Dokumen sudah diunduh dari sumber resmi (lihat `SOURCES.md` + `download_corpus.py`).

| Dokumen | Peran | Status | Hal | Sumber resmi (JDIH BPK) |
|---|---|---|---|---|
| UU 13/2003 Ketenagakerjaan | UU dasar | text-based ✓ | 128 | [Details/43013](https://peraturan.bpk.go.id/details/43013) |
| UU 11/2020 Cipta Kerja | Pengubah (historis) | — | — | [Details/149750](https://peraturan.bpk.go.id/Details/149750/uu-no-11-tahun-2020) |
| UU 6/2023 (Perppu Ciptaker jadi UU) | Pengubah terkini/berlaku | text-based ✓ | 1126 | [Details/246523](https://peraturan.bpk.go.id/Details/246523/uu-no-6-tahun-2023) |
| PP 35/2021 (PKWT, alih daya, PHK) | Turunan operasional | text-based ✓ | 56 | [Details/161904](https://peraturan.bpk.go.id/Details/161904/pp-no-35-tahun-2021) |

- Ketiga PDF inti **text-based** (bukan scan) → tidak butuh OCR, cukup `pymupdf`.
- **UU 6/2023 mencakup semua sektor** (1126 hal). Sesuai scope, ingestion **memfilter hanya klaster ketenagakerjaan** (bagian yang mengubah UU 13/2003).
- Semua dokumen **produk hukum negara → domain publik** (UU Hak Cipta 28/2014 Pasal 42), aman untuk portofolio & Hugging Face.

---

## 6. Arsitektur Sistem

```text
User Query
   │
   ▼
[1] Query Planner (agent) ──── pecah jadi sub-pertanyaan legal + identifikasi entitas
   │                            (jenis PHK, masa kerja, komponen hak)
   ▼
[2] Legal Retriever (tool) ─── hybrid search (BM25 + vektor) per pasal
   │                            + filter metadata (uu, tahun, status)
   ▼
[3] Version Resolver (tool) ── cek pasal berlaku / diubah / dicabut → ambil pengganti
   │                            (loop balik ke [2] bila perlu pasal pengganti)
   ▼
[4] Reranker ──────────────── bge-reranker-v2-m3, pilih pasal paling relevan
   │
   ▼
[5] Answer Synthesizer ─────── jawaban + sitasi terstruktur (JSON)
   │
   ▼
[6] Citation Verifier (guard)─ tiap dasar_hukum harus cocok dengan korpus;
   │                            gagal verifikasi → turunkan confidence / refuse
   ▼
Jawaban + daftar pasal + status keberlakuan + confidence + disclaimer
```

Sifat **agentic**: langkah 1–3 dapat **loop**. Bila retriever kosong atau version resolver menemukan pasal dicabut, agent merumuskan ulang query dan mencari pasal pengganti (maks N iterasi).

---

## 7. Komponen Teknis

### 7.1 Ingestion & Hierarchical Chunking
- Parse PDF dengan `pymupdf` / `marker` (jaga struktur).
- Segmentasi **per pasal** via regex `Pasal\s+\d+` + deteksi ayat `\(\d+\)` dan huruf.
- Tiap chunk membawa metadata:
```json
{
  "uu": "UU 13/2003", "tahun": 2003, "pasal": "156", "ayat": "2",
  "bab": "XII", "judul_bab": "Pemutusan Hubungan Kerja",
  "status": "diubah", "pengubah": "UU 6/2023", "pengganti_ref": "UU 6/2023 Pasal 156"
}
```

### 7.2 Version Graph (killer feature)
- Bangun **peta perubahan**: pasal X di UU lama → diubah/dicabut oleh UU Y pasal Z.
- Disimpan sebagai tabel relasi (`amends`) + di-embed ke metadata tiap chunk.
- Sumber peta: bagian "ketentuan perubahan" di UU Cipta Kerja + anotasi manual untuk korpus v1.

### 7.3 Hybrid Retrieval
- **BM25** (`rank_bm25`) untuk istilah legal presisi ("pesangon", "PHK efisiensi", nomor pasal).
- **Vektor** (`multilingual-e5-large` / `BGE-m3`) untuk makna.
- Fusion **RRF** (Reciprocal Rank Fusion), lalu rerank.
- Vector store: **Qdrant / Chroma** (butuh filter metadata untuk status keberlakuan).

### 7.4 Structured Output & Citation Verifier
- Output LLM = objek Pydantic:
```json
{
  "jawaban": "…",
  "dasar_hukum": [
    {"uu": "UU 6/2023", "pasal": "156 ayat (2)", "kutipan": "…",
     "status": "berlaku"}
  ],
  "asumsi": ["masa kerja 5 tahun", "PHK karena efisiensi"],
  "confidence": "tinggi|sedang|rendah"
}
```
- **Verifier** mencocokkan tiap `dasar_hukum` dengan chunk nyata (uu+pasal ada di korpus, kutipan overlap tinggi). Sitasi tak terverifikasi → dibuang & confidence turun; bila semua gugur → refuse.

### 7.5 Refusal Policy
- Trigger refuse: skor retrieval < ambang, tidak ada pasal berlaku, atau pertanyaan di luar domain.
- Output refuse baku: "Tidak ditemukan dasar hukum yang cukup jelas untuk pertanyaan ini. Konsultasikan dengan ahli hukum."

---

## 8. Rancangan Evaluasi

### 8.1 Dataset Eval
- **80–100 pasang** {pertanyaan, jawaban acuan, pasal sumber benar (dengan versi), label bisa/harus-refuse}.
- Komposisi: faktual single-hop, multi-hop (UU+PP), version-sensitive (pasal berubah), out-of-scope (harus refuse).

### 8.2 Metrik
| Metrik | Definisi | Kenapa penting |
|---|---|---|
| **Citation Accuracy** ⭐ | % jawaban yang menyebut pasal sumber yang benar | Pembeda utama, ukur grounding |
| **Version Accuracy** ⭐ | % jawaban yang mengutip **versi pasal** yang benar-berlaku | Unik; jarang ada di portofolio lain |
| **Faithfulness** | Klaim jawaban didukung konteks terambil | Anti-halusinasi |
| **Answer Relevancy** | Jawaban relevan dengan pertanyaan | Kualitas umum |
| **Context Precision/Recall** | Kualitas retrieval | Diagnosa layer retrieval |
| **Refusal Precision** | Saat refuse, apakah memang tak ada jawaban | Ukur "tahu diri" |

### 8.3 Ablation (tabel README)
| Konfigurasi | Chunk | Embedding | Reranker | Version-aware | Faithfulness | Citation Acc. |
|---|---|---|---|---|---|---|
| Baseline | 512 token | e5-small | – | ✗ | – | – |
| Per-pasal | per pasal | e5-large | – | ✗ | – | – |
| + Hybrid | per pasal | e5-large | – | ✗ | – | – |
| + Reranker | per pasal | e5-large | bge | ✗ | – | – |
| **+ Version-aware** | per pasal | e5-large | bge | ✓ | – | – |

Narasi: satu paragraf analisis kenapa konfigurasi final menang.

---

## 9. Tech Stack

```text
Parsing PDF       : pymupdf / marker-pdf
Chunking          : custom per-pasal (regex struktur) + metadata
Embedding         : multilingual-e5-large / BGE-m3
Vector store      : Qdrant atau Chroma (metadata filter)
Hybrid            : rank_bm25 + vektor, fusion RRF
Reranker          : bge-reranker-v2-m3
Structured output : Pydantic (+ instructor opsional)
Agent loop        : LangGraph (state machine) atau custom loop
LLM               : Groq llama-3.3-70b / Gemini 2.0 flash (gratis, ID oke)
Eval              : RAGAS + metrik custom (citation/version/refusal)
Trace             : Langfuse (screenshot untuk README)
Demo              : Streamlit / Hugging Face Spaces
```

---

## 10. Roadmap Implementasi

| Fase | Isi | Output |
|---|---|---|
| **M0 — PoC Notebook** | Ingest 1–2 UU, chunking per-pasal, retrieval sederhana, 1 pertanyaan multi-hop jalan | `legal_rag_poc.ipynb` |
| **M1 — Version-aware** | Version graph + metadata filter + version resolver tool | Retrieval sadar-versi |
| **M2 — Agent + Verifier** | Query planner, agent loop, citation verifier, refusal policy | Pipeline agentic penuh |
| **M3 — Evaluasi** | Dataset 80–100 Q&A, RAGAS + metrik custom, tabel ablation | Laporan eval + tabel README |
| **M4 — Demo** | Streamlit / HF Spaces, trace Langfuse, dokumentasi | Demo yang bisa diklik |

Prinsip: **detailkan hanya milestone dekat (M0–M1)**; M2–M4 tetap tingkat-epik sampai divalidasi.

---

## 11. Risiko & Mitigasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Version graph salah/manual | Jawaban salah versi | Batasi korpus v1 kecil, anotasi versi diverifikasi manual, tandai `confidence` |
| Halusinasi pasal | Bahaya hukum | Citation verifier keras + refusal policy |
| Parsing PDF hukum berantakan | Chunk rusak | Uji parser per dokumen, validasi jumlah pasal terdeteksi vs daftar isi |
| Dikira nasihat hukum | Risiko reputasi/legal | Disclaimer di setiap jawaban + README |
| Retrieval multi-hop lemah | Jawaban tak lengkap | Query planner + loop retrieval + reranker |
| Biaya/latency agent loop | Mahal/lambat | Batas iterasi, cache retrieval, model gratis (Groq/Gemini) |

---

## 12. Definisi Selesai (Definition of Done, v1)

- [ ] Korpus 4 dokumen ter-ingest, chunking per-pasal terverifikasi (jumlah pasal cocok).
- [ ] Version graph untuk pasal-pasal ketenagakerjaan kunci (min. pesangon/PHK).
- [ ] Agent loop multi-hop jalan untuk ≥5 pertanyaan demo.
- [ ] Citation verifier + refusal policy aktif dan teruji.
- [ ] Eval ≥80 Q&A dengan citation accuracy & version accuracy terlaporkan.
- [ ] Tabel ablation di README + paragraf analisis.
- [ ] Demo bisa diklik + screenshot trace.
- [ ] Disclaimer hukum di jawaban & README.

---

## 13. Open Decisions

1. **Agent framework:** LangGraph vs custom loop? (LangGraph memudahkan state machine loop, tapi nambah dependency.)
2. **Vector store:** Qdrant (fitur filter kuat) vs Chroma (lebih ringan untuk portofolio).
3. **Version graph:** manual anotasi vs parsing otomatis bagian "ketentuan perubahan".
4. **Cakupan PP:** cukup PP 35/2021 atau tambah PP lain (pengupahan)?
5. **LLM utama:** Groq (cepat) vs Gemini flash (context besar) untuk sintesis final.

---

## 14. Narasi Portofolio

> "Saya membangun **retrieval layer version-aware** untuk dokumen hukum Indonesia, lalu membangun **agent reasoning multi-step** di atasnya, dengan **citation verifier** agar tidak berhalusinasi di domain berisiko tinggi."

Menggabungkan dua ide di catatan harian (RAG domain-spesifik + LLM agent) menjadi **satu proyek berlapis** — jauh lebih kuat daripada chatbot PDF biasa.
