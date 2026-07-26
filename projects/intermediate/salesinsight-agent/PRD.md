# Product Requirements Document

## SalesInsight Agent

**Versi:** 1.0  
**Status:** Prototype / Portfolio Project  
**Format implementasi awal:** Single Jupyter Notebook  
**Nama notebook:** `sales_insight_agent.ipynb`

---

## 1. Ringkasan Produk

SalesInsight Agent adalah prototipe LLM Agent yang dapat menjawab pertanyaan analisis data penjualan menggunakan bahasa natural. Pengguna dapat memberikan pertanyaan seperti:

> Bandingkan total penjualan setiap kategori pada Q1 dan Q2, lalu tampilkan tren bulanannya.

Agent akan memahami pertanyaan, membaca schema database, menghasilkan SQL, memvalidasi keamanan query, mengeksekusi query melalui koneksi read-only, memperbaiki SQL jika terjadi error, menampilkan hasil sebagai tabel dan grafik, lalu membuat ringkasan naratif berdasarkan data.

Versi pertama dikembangkan sepenuhnya dalam satu Jupyter Notebook agar alur data, agent loop, tool use, guardrail, debugging, dan evaluasi dapat dipelajari secara transparan.

---

## 2. Latar Belakang

Analisis data bisnis umumnya membutuhkan kemampuan SQL dan pemahaman struktur database. Pengguna nonteknis sering membutuhkan bantuan data analyst untuk menjawab pertanyaan seperti:

- kategori dengan penjualan tertinggi,
- perbandingan penjualan antarperiode,
- tren revenue bulanan,
- performa wilayah,
- pertumbuhan produk,
- pelanggan dengan transaksi terbesar.

LLM dapat mengubah pertanyaan bahasa natural menjadi SQL, tetapi implementasinya memiliki risiko:

- query tidak aman,
- SQL salah secara sintaksis,
- SQL benar secara sintaksis tetapi salah secara bisnis,
- query mengambil data terlalu besar,
- agent melakukan retry tanpa batas,
- ringkasan tidak sesuai dengan hasil query,
- biaya token dan latency tidak terkontrol.

SalesInsight Agent dirancang untuk menunjukkan implementasi LLM Agent yang menggunakan tool secara aman, terukur, dan dapat dievaluasi.

---

## 3. Tujuan

### 3.1 Tujuan Utama

Membangun prototipe agent analis data yang mampu mengubah pertanyaan bahasa natural menjadi analisis berbasis SQL secara end-to-end.

### 3.2 Tujuan Pembelajaran

Proyek ini digunakan untuk mempelajari:

- LLM tool use,
- function calling,
- prompt engineering,
- text-to-SQL,
- SQL validation,
- agent loop,
- error handling,
- self-correction,
- structured output,
- data visualization,
- evaluasi aplikasi LLM,
- token usage,
- latency,
- estimasi biaya.

### 3.3 Tujuan Portofolio

Proyek harus menunjukkan kemampuan dalam:

- menghubungkan LLM dengan database,
- membuat agent yang menggunakan tool,
- menerapkan guardrail SQL,
- membangun bounded retry loop,
- mengevaluasi hasil agent,
- mempertimbangkan biaya dan latency,
- menjelaskan keterbatasan sistem.

---

## 4. Target Pengguna

Target pengguna:

- pemilik bisnis kecil,
- manajer penjualan,
- business analyst,
- data analyst pemula,
- mahasiswa AI dan data,
- pengguna nonteknis yang membutuhkan insight penjualan.

Contoh kebutuhan pengguna:

> Wilayah mana yang mengalami penurunan penjualan terbesar pada kuartal kedua?

> Tampilkan pertumbuhan revenue bulanan untuk setiap kategori.

> Siapa sepuluh pelanggan dengan total pembelian terbesar?

---

## 5. Ruang Lingkup MVP

MVP dibuat dalam satu file Jupyter Notebook.

Fitur MVP:

1. pembuatan dataset penjualan sintetis,
2. penyimpanan dataset pada DuckDB,
3. koneksi database read-only untuk agent,
4. dokumentasi schema dan aturan bisnis,
5. input pertanyaan bahasa natural,
6. pembuatan SQL oleh LLM,
7. structured output menggunakan Pydantic,
8. validasi SQL menggunakan SQLGlot,
9. eksekusi query,
10. forced query limit,
11. query timeout,
12. self-correction maksimal dua kali,
13. hasil query dalam Pandas DataFrame,
14. visualisasi menggunakan Matplotlib,
15. ringkasan naratif,
16. pencatatan latency, token, retry, dan biaya,
17. evaluasi menggunakan 50 pertanyaan dan ground truth SQL.

---

## 6. Di Luar Ruang Lingkup MVP

Versi notebook pertama belum mencakup:

- web application,
- autentikasi pengguna,
- multi-user,
- database production,
- operasi INSERT, UPDATE, atau DELETE,
- dashboard interaktif,
- scheduled report,
- role-based access control,
- vector database,
- fine-tuning,
- deployment cloud,
- Docker,
- integrasi Slack atau WhatsApp,
- query lintas beberapa database.

---

## 7. Use Case

### 7.1 Perbandingan Periode

Pertanyaan:

> Bandingkan penjualan kategori Electronics pada Q1 dan Q2.

Output:

- SQL,
- tabel hasil,
- perubahan absolut,
- persentase pertumbuhan,
- ringkasan kenaikan atau penurunan.

### 7.2 Tren Bulanan

Pertanyaan:

> Tampilkan tren revenue setiap bulan selama tahun 2025.

Output:

- tabel revenue per bulan,
- line chart,
- bulan tertinggi,
- bulan terendah.

### 7.3 Performa Kategori

Pertanyaan:

> Kategori apa yang memiliki revenue dan profit tertinggi?

Output:

- revenue per kategori,
- profit per kategori,
- bar chart,
- ringkasan performa.

### 7.4 Performa Wilayah

Pertanyaan:

> Bandingkan penjualan wilayah Jawa, Sumatra, dan Kalimantan.

Output:

- total transaksi,
- revenue,
- average order value,
- visualisasi wilayah.

### 7.5 Analisis Produk

Pertanyaan:

> Sebutkan lima produk dengan pertumbuhan penjualan tertinggi.

Output:

- produk,
- penjualan periode awal,
- penjualan periode akhir,
- persentase pertumbuhan,
- ranking.

---

## 8. Dataset

### 8.1 Strategi

Gunakan dataset sintetis agar:

- tidak memakai data pribadi,
- eksperimen dapat direproduksi,
- ground truth mudah dibuat,
- pola data dapat diatur.

### 8.2 Rekomendasi Ukuran

- periode: Januari 2024 sampai Desember 2025,
- minimal 20.000 transaksi,
- 1.000 pelanggan,
- 100 produk,
- 8 kategori,
- 6 wilayah.

### 8.3 Tabel

#### `customers`

| Kolom | Tipe | Deskripsi |
|---|---|---|
| customer_id | INTEGER | ID pelanggan |
| customer_name | VARCHAR | Nama pelanggan |
| customer_segment | VARCHAR | Segmen pelanggan |
| city | VARCHAR | Kota |
| region | VARCHAR | Wilayah |
| registered_at | DATE | Tanggal registrasi |

#### `categories`

| Kolom | Tipe | Deskripsi |
|---|---|---|
| category_id | INTEGER | ID kategori |
| category_name | VARCHAR | Nama kategori |

#### `products`

| Kolom | Tipe | Deskripsi |
|---|---|---|
| product_id | INTEGER | ID produk |
| product_name | VARCHAR | Nama produk |
| category_id | INTEGER | Relasi kategori |
| unit_cost | DECIMAL | Harga pokok |
| unit_price | DECIMAL | Harga jual |

#### `orders`

| Kolom | Tipe | Deskripsi |
|---|---|---|
| order_id | INTEGER | ID order |
| customer_id | INTEGER | Relasi pelanggan |
| order_date | DATE | Tanggal order |
| order_status | VARCHAR | Completed, Cancelled, Refunded |
| sales_channel | VARCHAR | Website, Mobile, Marketplace, Offline |
| payment_method | VARCHAR | Transfer, E-Wallet, Card, COD |

#### `order_items`

| Kolom | Tipe | Deskripsi |
|---|---|---|
| order_item_id | INTEGER | ID item |
| order_id | INTEGER | Relasi order |
| product_id | INTEGER | Relasi produk |
| quantity | INTEGER | Jumlah barang |
| unit_price | DECIMAL | Harga jual |
| discount | DECIMAL | Diskon |
| revenue | DECIMAL | Revenue setelah diskon |
| cost | DECIMAL | Total harga pokok |
| profit | DECIMAL | Revenue dikurangi cost |

---

## 9. Arsitektur

```text
Pertanyaan bahasa natural
        │
        ▼
Question Understanding
        │
        ▼
Schema dan Business Context
        │
        ▼
LLM SQL Generator
        │
        ▼
SQL Guardrail
├── SELECT only
├── Single statement
├── Table whitelist
├── Forced LIMIT
└── Blocked operations
        │
        ▼
DuckDB Read-Only Tool
        │
   ┌────┴────┐
   │         │
 Error     Success
   │         │
   ▼         ▼
Self-     Pandas DataFrame
Correction    │
Max 2x        ├── Visualisasi
              └── Ringkasan naratif
```

---

## 10. Alur Agent

1. menerima pertanyaan pengguna,
2. mengambil schema dan business context,
3. meminta LLM menghasilkan structured output,
4. mengambil SQL,
5. memvalidasi SQL,
6. menolak query tidak aman,
7. menjalankan query aman,
8. memperbaiki SQL jika error,
9. membatasi self-correction maksimal dua kali,
10. menyimpan hasil sebagai DataFrame,
11. membuat grafik jika relevan,
12. membuat ringkasan,
13. menyimpan execution trace,
14. menampilkan jawaban akhir.

---

## 11. Tools Agent

### 11.1 `get_database_schema`

Mengembalikan:

- nama tabel,
- nama kolom,
- tipe data,
- relasi tabel,
- definisi metrik bisnis.

### 11.2 `validate_sql`

Memastikan:

- hanya SELECT atau CTE yang berakhir dengan SELECT,
- hanya satu statement,
- tidak ada operasi perubahan data,
- tabel hanya dari whitelist,
- LIMIT maksimal 1000.

### 11.3 `execute_sql`

Mengembalikan:

- status,
- DataFrame,
- error type,
- error message,
- row count,
- execution time,
- SQL yang benar-benar dijalankan.

### 11.4 `create_chart`

Mendukung:

- line chart,
- bar chart,
- horizontal bar chart,
- grouped bar chart,
- scatter plot.

---

## 12. Structured Output

Gunakan Pydantic.

```python
class ChartConfig(BaseModel):
    required: bool
    chart_type: str | None
    x: str | None
    y: list[str]
    title: str | None


class SQLGenerationResult(BaseModel):
    question_interpretation: str
    sql: str
    expected_columns: list[str]
    chart: ChartConfig
    assumptions: list[str]
```

---

## 13. Aturan Bisnis

1. Revenue hanya berasal dari order berstatus `Completed`.
2. Order `Cancelled` tidak dihitung.
3. Order `Refunded` tidak dihitung sebagai revenue bersih.
4. Revenue menggunakan `order_items.revenue`.
5. Profit menggunakan `order_items.profit`.
6. Average Order Value:

```text
Total revenue / jumlah order unik
```

7. Q1: Januari–Maret.
8. Q2: April–Juni.
9. Q3: Juli–September.
10. Q4: Oktober–Desember.
11. Pertumbuhan:

```text
((nilai akhir - nilai awal) / nilai awal) × 100
```

12. Jika nilai awal nol, pertumbuhan persentase ditandai tidak dapat dihitung.
13. Mata uang menggunakan rupiah.
14. Agent harus menampilkan asumsi.

---

## 14. Guardrail

### 14.1 Read-Only Connection

Dataset dibuat menggunakan connection write. Setelah selesai, connection ditutup dan agent membuka DuckDB dalam mode read-only.

```python
duckdb.connect("sales.db", read_only=True)
```

### 14.2 Query Restriction

Query hanya boleh menggunakan:

```sql
SELECT
```

atau CTE:

```sql
WITH ... SELECT
```

### 14.3 Operasi yang Diblokir

- INSERT
- UPDATE
- DELETE
- DROP
- ALTER
- CREATE
- TRUNCATE
- MERGE
- COPY
- ATTACH
- DETACH
- INSTALL
- LOAD
- EXPORT
- IMPORT
- CALL
- PRAGMA

### 14.4 Single Statement

Query multi-statement harus ditolak.

### 14.5 Table Whitelist

Tabel yang diizinkan:

- customers
- categories
- products
- orders
- order_items

### 14.6 Forced Limit

Query dibatasi maksimal:

```sql
LIMIT 1000
```

### 14.7 Timeout

Batas waktu query:

```text
5 detik
```

### 14.8 Maximum Retry

Total percobaan:

```text
1 query awal + maksimal 2 retry
```

Self-correction tidak dijalankan untuk query berbahaya.

### 14.9 Output Limit

- maksimal hasil database: 1.000 baris,
- maksimal ditampilkan: 100 baris,
- maksimal dikirim ke LLM: 50 baris.

---

## 15. Self-Correction

Jika query gagal, LLM menerima:

- pertanyaan asli,
- schema,
- SQL sebelumnya,
- pesan error,
- nomor percobaan,
- aturan keamanan.

Agent memperbaiki SQL tanpa mengubah maksud pertanyaan. SQL hasil koreksi harus kembali melewati validator.

---

## 16. Visualisasi

| Bentuk Data | Visualisasi |
|---|---|
| Waktu dan satu metrik | Line chart |
| Kategori dan satu metrik | Bar chart |
| Kategori dan dua periode | Grouped bar chart |
| Ranking dengan label panjang | Horizontal bar chart |
| Dua metrik numerik | Scatter plot |
| Satu nilai | Tanpa grafik |

Prinsip:

- judul jelas,
- sumbu memiliki label,
- data waktu diurutkan,
- angka rupiah diformat,
- grafik tidak dibuat jika tidak relevan.

---

## 17. Format Jawaban

```text
Jawaban utama

Insight:
- ...
- ...
- ...

Tabel hasil

Grafik

SQL yang dijalankan

Asumsi:
- ...

Metadata:
- jumlah percobaan,
- query latency,
- total latency,
- input token,
- output token,
- estimasi biaya.
```

---

## 18. Struktur Notebook

1. Project Overview
2. Architecture
3. Installation
4. Imports and Configuration
5. Synthetic Dataset Generation
6. Exploratory Data Analysis
7. DuckDB Setup
8. Schema Documentation
9. Business Metric Definitions
10. Read-Only Database Connection
11. SQL Validation Guardrail
12. Database Query Tool
13. LLM Client Abstraction
14. SQL Generation Prompt
15. Self-Correction
16. Visualization Tool
17. Narrative Summarization
18. Agent Orchestration Loop
19. Demonstration Questions
20. Security Testing
21. Self-Correction Testing
22. Evaluation Dataset
23. Evaluation Runner
24. Evaluation Report
25. Error Analysis
26. Limitations
27. Roadmap
28. Conclusion

Setiap bagian harus memiliki penjelasan Markdown sebelum kode.

---

## 19. Fungsi Utama

```python
def validate_sql(sql: str):
    ...
```

```python
def execute_sql(sql: str):
    ...
```

```python
def create_visualization(dataframe, chart_config):
    ...
```

```python
def run_sales_agent(question: str, show_trace: bool = True):
    ...
```

---

## 20. Observability

Setiap eksekusi menyimpan:

- timestamp,
- question,
- interpretation,
- initial SQL,
- final SQL,
- validation result,
- error history,
- retries,
- query latency,
- LLM latency,
- total latency,
- input tokens,
- output tokens,
- estimated cost,
- row count,
- final status.

Gunakan:

```python
agent_traces = []
```

Trace dapat dikonversi menjadi DataFrame.

---

## 21. Demonstrasi

Minimal sepuluh pertanyaan:

1. Berapa total revenue tahun 2025?
2. Tampilkan tren revenue bulanan tahun 2025.
3. Bandingkan revenue Q1 dan Q2 per kategori.
4. Kategori mana yang memiliki profit tertinggi?
5. Wilayah mana dengan penjualan tertinggi?
6. Tampilkan lima produk terlaris.
7. Bandingkan average order value setiap sales channel.
8. Siapa sepuluh pelanggan dengan total pembelian terbesar?
9. Bulan mana yang mengalami penurunan revenue terbesar?
10. Bandingkan performa Website dan Marketplace.

---

## 22. Security Testing

Test minimal:

```sql
DROP TABLE orders
```

```sql
DELETE FROM customers
```

```sql
UPDATE products SET unit_price = 0
```

```sql
SELECT * FROM orders; DROP TABLE orders
```

```sql
SELECT * FROM secret_table
```

```sql
COPY orders TO '/tmp/orders.csv'
```

Hasil test:

| test_name | input_sql | expected | actual | passed |
|---|---|---|---|---|

Target:

```text
100% security test lulus
```

---

## 23. Evaluation Dataset

Buat 50 pertanyaan:

- 10 aggregation,
- 10 time-series,
- 10 comparison,
- 8 ranking,
- 7 multi-table join,
- 5 edge case.

Struktur:

| id | question | ground_truth_sql | category | difficulty |
|---|---|---|---|---|

---

## 24. Metrik Evaluasi

### 24.1 Execution Accuracy

Query agent dan ground truth dijalankan, kemudian hasilnya dibandingkan.

Query tidak harus sama secara teks.

```text
Execution Accuracy =
jumlah hasil benar / total pertanyaan
```

Target:

```text
≥ 80%
```

### 24.2 Valid SQL Rate

Target:

```text
≥ 90% setelah retry
```

### 24.3 Unsafe Query Rejection Rate

Target:

```text
100%
```

### 24.4 Average Retry

Target:

```text
≤ 0,5 retry per pertanyaan
```

### 24.5 Latency

Target:

```text
Median total latency ≤ 10 detik
```

### 24.6 Token dan Biaya

Catat:

- input token,
- output token,
- token SQL generation,
- token summarization,
- biaya per pertanyaan.

---

## 25. Error Categories

Klasifikasi error:

- schema misunderstanding,
- wrong join,
- wrong filter,
- wrong date range,
- wrong aggregation,
- wrong business definition,
- SQL syntax error,
- unsafe SQL,
- empty result,
- visualization error,
- narrative hallucination,
- timeout,
- model API error.

---

## 26. Acceptance Criteria

Prototipe dinyatakan selesai apabila:

1. notebook dapat dijalankan dari atas ke bawah,
2. dataset dibuat secara reproducible,
3. DuckDB dibuka dalam mode read-only,
4. pertanyaan natural language dapat diproses,
5. SQL dibuat oleh LLM,
6. SQL divalidasi sebelum eksekusi,
7. query berbahaya diblokir,
8. LIMIT otomatis diterapkan,
9. query error dapat diperbaiki maksimal dua kali,
10. hasil ditampilkan sebagai DataFrame,
11. grafik dibuat jika relevan,
12. ringkasan sesuai hasil query,
13. SQL akhir ditampilkan,
14. trace agent dapat diperiksa,
15. sepuluh demo tersedia,
16. 50 pertanyaan evaluasi tersedia,
17. execution accuracy dihitung,
18. latency, token, retry, dan biaya tercatat,
19. API key tidak hard-coded,
20. keterbatasan didokumentasikan.

---

## 27. Tech Stack

| Komponen | Teknologi |
|---|---|
| Environment | Jupyter Notebook |
| Bahasa | Python |
| Data processing | Pandas dan NumPy |
| Dataset generator | Faker |
| Database | DuckDB |
| SQL parser | SQLGlot |
| Data validation | Pydantic |
| Visualisasi | Matplotlib |
| LLM | Model dengan structured output atau tool calling |
| Environment | python-dotenv |
| Evaluation | Pandas dan custom evaluator |

---

## 28. Roadmap

### Fase 1 — Notebook Prototype

- dataset sintetis,
- DuckDB,
- SQL generator,
- guardrail,
- executor,
- self-correction,
- visualisasi,
- summary,
- evaluasi.

### Fase 2 — Modular Python Application

```text
src/
├── agent/
├── tools/
├── guardrails/
├── database/
├── visualization/
└── evaluation/
```

### Fase 3 — Web Application

- FastAPI,
- Streamlit atau Next.js,
- PostgreSQL,
- Redis.

### Fase 4 — Production Agent

- authentication,
- role-based access,
- row-level security,
- audit log,
- prompt versioning,
- semantic layer,
- model fallback,
- monitoring,
- cost budget,
- container deployment.

---

## 29. Definition of Done

Pengguna dapat:

1. membuka notebook,
2. mengatur API key melalui environment,
3. menjalankan seluruh cell,
4. memasukkan pertanyaan penjualan,
5. melihat SQL yang dibuat,
6. melihat hasil validasi,
7. melihat tabel dan grafik,
8. membaca ringkasan,
9. menjalankan security test,
10. menjalankan evaluasi,
11. melihat akurasi, latency, retry, token, dan biaya.
