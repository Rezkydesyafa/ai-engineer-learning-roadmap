"""Grup 5: 10 pertanyaan demo + security testing."""

CELLS = [
    ("md", """
## 19. Demonstrasi (10 Pertanyaan)

Sepuluh pertanyaan yang mencakup agregasi, time-series, perbandingan, ranking, dan multi-tabel. Jika LLM aktif, tiap pertanyaan dijalankan penuh; jika tidak, daftar tetap ditampilkan sebagai referensi.
"""),
    ("code", """
DEMO_QUESTIONS = [
    "Berapa total revenue pada tahun 2025?",
    "Tampilkan tren revenue bulanan sepanjang tahun 2025.",
    "Bandingkan revenue tiap kategori pada Q1 dan Q2 2025.",
    "Kategori mana yang memiliki profit tertinggi sepanjang 2025?",
    "Wilayah mana dengan revenue tertinggi?",
    "Tampilkan lima produk dengan revenue terbesar.",
    "Bandingkan average order value tiap sales channel.",
    "Siapa sepuluh pelanggan dengan total pembelian terbesar?",
    "Bulan mana pada 2025 yang mengalami penurunan revenue terbesar dibanding bulan sebelumnya?",
    "Bandingkan performa channel Website dan Marketplace berdasarkan revenue.",
]

if LLM_ENABLED:
    for i, q in enumerate(DEMO_QUESTIONS, 1):
        print(f"\\n########## DEMO {i}/{len(DEMO_QUESTIONS)} ##########")
        run_sales_agent(q, show_trace=True)
else:
    print("LLM nonaktif — daftar pertanyaan demo:")
    for i, q in enumerate(DEMO_QUESTIONS, 1):
        print(f"{i:2}. {q}")
""", "skip"),

    ("md", """
## 20. Security Testing

Rangkaian input berbahaya harus **100%** ditolak oleh guardrail. Ini murni deterministik (tidak butuh LLM) karena menguji `validate_sql`/`execute_sql` langsung.
"""),
    ("code", """
SECURITY_TESTS = [
    ("drop_table",      "DROP TABLE orders"),
    ("delete_rows",     "DELETE FROM customers"),
    ("update_rows",     "UPDATE products SET unit_price = 0"),
    ("stacked_query",   "SELECT * FROM orders; DROP TABLE orders"),
    ("unknown_table",   "SELECT * FROM secret_table"),
    ("copy_out",        "COPY orders TO '/tmp/orders.csv'"),
    ("pragma",          "PRAGMA database_list"),
    ("attach_db",       "ATTACH 'evil.db' AS evil"),
    ("create_table",    "CREATE TABLE hack(x INT)"),
    ("insert_rows",     "INSERT INTO customers VALUES (1)"),
]

rows = []
for name, sql in SECURITY_TESTS:
    r = execute_sql(sql)
    blocked = (r.status == "error" and r.error_type == "UnsafeSQL")
    rows.append({"test_name": name, "input_sql": sql[:45],
                 "expected": "blocked", "actual": ("blocked" if blocked else r.status),
                 "passed": blocked})
sec_df = pd.DataFrame(rows)
print(sec_df.to_string(index=False))
_passed = int(sec_df.passed.sum())
print(f"\\nSecurity: {_passed}/{len(sec_df)} lulus  ->  {_passed/len(sec_df)*100:.0f}%")
assert _passed == len(sec_df), "Ada security test yang gagal!"
print("TARGET 100% TERCAPAI.")
""", "det"),

    ("md", """
## 21. Uji Self-Correction

Menguji bahwa loop koreksi memperbaiki SQL yang error. Butuh LLM; jika nonaktif, di-skip. Kita berikan pertanyaan yang cenderung memancing kesalahan nama kolom, lalu memeriksa apakah agent berhasil pada percobaan ke-2/3.
"""),
    ("code", """
if LLM_ENABLED:
    tricky = "Tampilkan total pendapatan bersih per kuartal 2025 memakai istilah 'net_revenue'."
    r = run_sales_agent(tricky, show_trace=True)
    print("\\nHasil self-correction: status=", r.status, "retries=", r.retries)
else:
    print("LLM nonaktif — uji self-correction dilewati.")
""", "skip"),
]
