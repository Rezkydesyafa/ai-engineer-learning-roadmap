"""Grup 6: Evaluation dataset (50), runner, execution accuracy, report, penutup."""

CELLS = [
    ("md", """
## 22. Evaluation Dataset (50 Pertanyaan)

Lima puluh pertanyaan dengan **ground-truth SQL** yang sudah diverifikasi berjalan di database. Komposisi: agregasi, time-series, perbandingan, ranking, multi-table join, dan edge case. Ground truth memakai view `v_completed_sales` sesuai aturan bisnis.
"""),
    ("code", """
# Setiap entri: (id, question, ground_truth_sql, category, difficulty)
EVAL = [
    # --- aggregation (10) ---
    (1,"Total revenue 2025","SELECT SUM(revenue) AS revenue FROM v_completed_sales WHERE year=2025","aggregation","easy"),
    (2,"Total profit 2025","SELECT SUM(profit) AS profit FROM v_completed_sales WHERE year=2025","aggregation","easy"),
    (3,"Jumlah order unik 2025","SELECT COUNT(DISTINCT order_id) AS orders FROM v_completed_sales WHERE year=2025","aggregation","easy"),
    (4,"Total quantity terjual 2024","SELECT SUM(quantity) AS qty FROM v_completed_sales WHERE year=2024","aggregation","easy"),
    (5,"Rata-rata revenue per item 2025","SELECT AVG(revenue) AS avg_rev FROM v_completed_sales WHERE year=2025","aggregation","medium"),
    (6,"Total diskon 2025","SELECT SUM(discount) AS discount FROM v_completed_sales WHERE year=2025","aggregation","easy"),
    (7,"AOV keseluruhan 2025","SELECT SUM(revenue)/COUNT(DISTINCT order_id) AS aov FROM v_completed_sales WHERE year=2025","aggregation","medium"),
    (8,"Total revenue seluruh periode","SELECT SUM(revenue) AS revenue FROM v_completed_sales","aggregation","easy"),
    (9,"Jumlah pelanggan aktif 2025","SELECT COUNT(DISTINCT customer_id) AS customers FROM v_completed_sales WHERE year=2025","aggregation","medium"),
    (10,"Total profit seluruh periode","SELECT SUM(profit) AS profit FROM v_completed_sales","aggregation","easy"),
    # --- time-series (10) ---
    (11,"Revenue per bulan 2025","SELECT month, SUM(revenue) AS revenue FROM v_completed_sales WHERE year=2025 GROUP BY month ORDER BY month","time-series","medium"),
    (12,"Revenue per kuartal 2025","SELECT quarter, SUM(revenue) AS revenue FROM v_completed_sales WHERE year=2025 GROUP BY quarter ORDER BY quarter","time-series","medium"),
    (13,"Revenue per tahun","SELECT year, SUM(revenue) AS revenue FROM v_completed_sales GROUP BY year ORDER BY year","time-series","easy"),
    (14,"Profit per bulan 2024","SELECT month, SUM(profit) AS profit FROM v_completed_sales WHERE year=2024 GROUP BY month ORDER BY month","time-series","medium"),
    (15,"Order per bulan 2025","SELECT month, COUNT(DISTINCT order_id) AS orders FROM v_completed_sales WHERE year=2025 GROUP BY month ORDER BY month","time-series","medium"),
    (16,"Quantity per kuartal 2025","SELECT quarter, SUM(quantity) AS qty FROM v_completed_sales WHERE year=2025 GROUP BY quarter ORDER BY quarter","time-series","medium"),
    (17,"Revenue per bulan 2024","SELECT month, SUM(revenue) AS revenue FROM v_completed_sales WHERE year=2024 GROUP BY month ORDER BY month","time-series","medium"),
    (18,"AOV per kuartal 2025","SELECT quarter, SUM(revenue)/COUNT(DISTINCT order_id) AS aov FROM v_completed_sales WHERE year=2025 GROUP BY quarter ORDER BY quarter","time-series","hard"),
    (19,"Revenue kumulatif per bulan 2025","SELECT month, SUM(SUM(revenue)) OVER (ORDER BY month) AS cum_rev FROM v_completed_sales WHERE year=2025 GROUP BY month ORDER BY month","time-series","hard"),
    (20,"Profit per tahun","SELECT year, SUM(profit) AS profit FROM v_completed_sales GROUP BY year ORDER BY year","time-series","easy"),
    # --- comparison (10) ---
    (21,"Revenue Q1 vs Q2 2025","SELECT quarter, SUM(revenue) AS revenue FROM v_completed_sales WHERE year=2025 AND quarter IN (1,2) GROUP BY quarter ORDER BY quarter","comparison","medium"),
    (22,"Revenue 2024 vs 2025","SELECT year, SUM(revenue) AS revenue FROM v_completed_sales GROUP BY year ORDER BY year","comparison","easy"),
    (23,"Revenue per sales channel 2025","SELECT sales_channel, SUM(revenue) AS revenue FROM v_completed_sales WHERE year=2025 GROUP BY sales_channel ORDER BY revenue DESC","comparison","medium"),
    (24,"AOV per sales channel 2025","SELECT sales_channel, SUM(revenue)/COUNT(DISTINCT order_id) AS aov FROM v_completed_sales WHERE year=2025 GROUP BY sales_channel ORDER BY aov DESC","comparison","hard"),
    (25,"Revenue per payment method 2025","SELECT payment_method, SUM(revenue) AS revenue FROM v_completed_sales WHERE year=2025 GROUP BY payment_method ORDER BY revenue DESC","comparison","medium"),
    (26,"Profit Q3 vs Q4 2025","SELECT quarter, SUM(profit) AS profit FROM v_completed_sales WHERE year=2025 AND quarter IN (3,4) GROUP BY quarter ORDER BY quarter","comparison","medium"),
    (27,"Website vs Marketplace revenue 2025","SELECT sales_channel, SUM(revenue) AS revenue FROM v_completed_sales WHERE year=2025 AND sales_channel IN ('Website','Marketplace') GROUP BY sales_channel","comparison","medium"),
    (28,"Revenue per kategori 2025","SELECT c.category_name, SUM(v.revenue) AS revenue FROM v_completed_sales v JOIN products p ON v.product_id=p.product_id JOIN categories c ON p.category_id=c.category_id WHERE v.year=2025 GROUP BY c.category_name ORDER BY revenue DESC","comparison","hard"),
    (29,"Revenue per region 2025","SELECT cu.region, SUM(v.revenue) AS revenue FROM v_completed_sales v JOIN customers cu ON v.customer_id=cu.customer_id WHERE v.year=2025 GROUP BY cu.region ORDER BY revenue DESC","comparison","hard"),
    (30,"Quantity 2024 vs 2025","SELECT year, SUM(quantity) AS qty FROM v_completed_sales GROUP BY year ORDER BY year","comparison","easy"),
    # --- ranking (8) ---
    (31,"5 produk revenue terbesar 2025","SELECT p.product_name, SUM(v.revenue) AS revenue FROM v_completed_sales v JOIN products p ON v.product_id=p.product_id WHERE v.year=2025 GROUP BY p.product_name ORDER BY revenue DESC LIMIT 5","ranking","hard"),
    (32,"10 pelanggan pembelian terbesar 2025","SELECT cu.customer_name, SUM(v.revenue) AS revenue FROM v_completed_sales v JOIN customers cu ON v.customer_id=cu.customer_id WHERE v.year=2025 GROUP BY cu.customer_name ORDER BY revenue DESC LIMIT 10","ranking","hard"),
    (33,"Kategori profit tertinggi 2025","SELECT c.category_name, SUM(v.profit) AS profit FROM v_completed_sales v JOIN products p ON v.product_id=p.product_id JOIN categories c ON p.category_id=c.category_id WHERE v.year=2025 GROUP BY c.category_name ORDER BY profit DESC LIMIT 1","ranking","hard"),
    (34,"Region revenue tertinggi 2025","SELECT cu.region, SUM(v.revenue) AS revenue FROM v_completed_sales v JOIN customers cu ON v.customer_id=cu.customer_id WHERE v.year=2025 GROUP BY cu.region ORDER BY revenue DESC LIMIT 1","ranking","hard"),
    (35,"5 kategori revenue terbesar seluruh periode","SELECT c.category_name, SUM(v.revenue) AS revenue FROM v_completed_sales v JOIN products p ON v.product_id=p.product_id JOIN categories c ON p.category_id=c.category_id GROUP BY c.category_name ORDER BY revenue DESC LIMIT 5","ranking","hard"),
    (36,"10 produk quantity terbesar 2025","SELECT p.product_name, SUM(v.quantity) AS qty FROM v_completed_sales v JOIN products p ON v.product_id=p.product_id WHERE v.year=2025 GROUP BY p.product_name ORDER BY qty DESC LIMIT 10","ranking","hard"),
    (37,"3 channel revenue terbesar 2025","SELECT sales_channel, SUM(revenue) AS revenue FROM v_completed_sales WHERE year=2025 GROUP BY sales_channel ORDER BY revenue DESC LIMIT 3","ranking","medium"),
    (38,"5 kota revenue terbesar 2025","SELECT cu.city, SUM(v.revenue) AS revenue FROM v_completed_sales v JOIN customers cu ON v.customer_id=cu.customer_id WHERE v.year=2025 GROUP BY cu.city ORDER BY revenue DESC LIMIT 5","ranking","hard"),
    # --- multi-table join (7) ---
    (39,"Profit per kategori 2025","SELECT c.category_name, SUM(v.profit) AS profit FROM v_completed_sales v JOIN products p ON v.product_id=p.product_id JOIN categories c ON p.category_id=c.category_id WHERE v.year=2025 GROUP BY c.category_name ORDER BY profit DESC","join","hard"),
    (40,"Revenue per segment pelanggan 2025","SELECT cu.customer_segment, SUM(v.revenue) AS revenue FROM v_completed_sales v JOIN customers cu ON v.customer_id=cu.customer_id WHERE v.year=2025 GROUP BY cu.customer_segment ORDER BY revenue DESC","join","hard"),
    (41,"Revenue kategori per region 2025","SELECT cu.region, c.category_name, SUM(v.revenue) AS revenue FROM v_completed_sales v JOIN customers cu ON v.customer_id=cu.customer_id JOIN products p ON v.product_id=p.product_id JOIN categories c ON p.category_id=c.category_id WHERE v.year=2025 GROUP BY cu.region, c.category_name ORDER BY revenue DESC LIMIT 20","join","hard"),
    (42,"AOV per region 2025","SELECT cu.region, SUM(v.revenue)/COUNT(DISTINCT v.order_id) AS aov FROM v_completed_sales v JOIN customers cu ON v.customer_id=cu.customer_id WHERE v.year=2025 GROUP BY cu.region ORDER BY aov DESC","join","hard"),
    (43,"Profit per region 2025","SELECT cu.region, SUM(v.profit) AS profit FROM v_completed_sales v JOIN customers cu ON v.customer_id=cu.customer_id WHERE v.year=2025 GROUP BY cu.region ORDER BY profit DESC","join","hard"),
    (44,"Revenue kategori per channel 2025","SELECT v.sales_channel, c.category_name, SUM(v.revenue) AS revenue FROM v_completed_sales v JOIN products p ON v.product_id=p.product_id JOIN categories c ON p.category_id=c.category_id WHERE v.year=2025 GROUP BY v.sales_channel, c.category_name ORDER BY revenue DESC LIMIT 20","join","hard"),
    (45,"Jumlah produk per kategori","SELECT c.category_name, COUNT(*) AS n_products FROM products p JOIN categories c ON p.category_id=c.category_id GROUP BY c.category_name ORDER BY n_products DESC","join","medium"),
    # --- edge case (5) ---
    (46,"Revenue kategori Automotive 2025 (mungkin kecil/kosong)","SELECT c.category_name, SUM(v.revenue) AS revenue FROM v_completed_sales v JOIN products p ON v.product_id=p.product_id JOIN categories c ON p.category_id=c.category_id WHERE v.year=2025 AND c.category_name='Automotive' GROUP BY c.category_name","edge","medium"),
    (47,"Revenue tahun 2030 (tidak ada data)","SELECT SUM(revenue) AS revenue FROM v_completed_sales WHERE year=2030","edge","medium"),
    (48,"Order dengan revenue negatif (seharusnya tidak ada)","SELECT COUNT(*) AS n FROM v_completed_sales WHERE revenue < 0","edge","medium"),
    (49,"Pelanggan tanpa transaksi completed","SELECT COUNT(*) AS n FROM customers cu WHERE cu.customer_id NOT IN (SELECT DISTINCT customer_id FROM v_completed_sales)","edge","hard"),
    (50,"Revenue bulan 13 (invalid, harus kosong)","SELECT SUM(revenue) AS revenue FROM v_completed_sales WHERE month=13","edge","medium"),
]
eval_df = pd.DataFrame(EVAL, columns=["id","question","ground_truth_sql","category","difficulty"])
print("Eval dataset:", eval_df.shape)
print(eval_df.category.value_counts().to_string())
""", "det"),

    ("md", """
### 22.1 Verifikasi ground truth berjalan (deterministik)

Setiap ground-truth SQL harus lolos guardrail dan tereksekusi. Ini menjamin dataset evaluasi valid sebelum dipakai menilai agent.
"""),
    ("code", """
_gt_ok = 0
_gt_fail = []
for _, row in eval_df.iterrows():
    r = execute_sql(row.ground_truth_sql)
    if r.status == "success":
        _gt_ok += 1
    else:
        _gt_fail.append((row.id, r.error_type, r.error_message))
print(f"Ground truth valid: {_gt_ok}/{len(eval_df)}")
if _gt_fail:
    print("GAGAL:", _gt_fail)
assert _gt_ok == len(eval_df), "Ada ground truth yang tidak jalan!"
print("Semua ground truth tereksekusi.")
""", "det"),

    ("md", """
## 23. Evaluation Runner & 24. Metrik

**Execution accuracy**: hasil SQL agent dibandingkan dengan hasil ground truth berdasarkan **nilai**, bukan teks SQL. Untuk adil, hasil di-*canonicalize*: ambil nilai numerik, dibulatkan 2 desimal, diurutkan, dibandingkan sebagai multiset. Ini menghilangkan false-negative akibat beda urutan baris/kolom atau presisi float.
"""),
    ("code", """
def canonicalize(df: pd.DataFrame):
    if df is None:
        return None
    vals = []
    for col in df.columns:
        s = df[col]
        if pd.api.types.is_numeric_dtype(s):
            vals.extend(sorted(round(float(x), 2) for x in s.dropna().tolist()))
        else:
            vals.extend(sorted(str(x) for x in s.dropna().tolist()))
    return tuple(sorted(map(str, vals)))

def results_match(df_a, df_b):
    return canonicalize(df_a) == canonicalize(df_b)

def run_evaluation(sample: Optional[int] = None):
    if not LLM_ENABLED:
        print("LLM nonaktif — evaluasi dilewati.")
        return None
    data = eval_df if sample is None else eval_df.head(sample)
    rows = []
    for _, row in data.iterrows():
        gt = execute_sql(row.ground_truth_sql)
        res = run_sales_agent(row.question, show_trace=False)
        agent_df = res.dataframe if res.status == "success" else None
        correct = (res.status == "success" and gt.status == "success"
                   and results_match(agent_df, gt.dataframe))
        rows.append({
            "id": row.id, "category": row.category, "difficulty": row.difficulty,
            "agent_status": res.status, "correct": bool(correct),
            "retries": res.retries, "latency": round(res.latency_total,2),
            "in_tok": res.input_tokens, "out_tok": res.output_tokens,
            "cost": round(res.est_cost,6),
            "faithfulness": (res.faithfulness or {}).get("score"),
        })
    return pd.DataFrame(rows)

print("Evaluation runner siap. Panggil run_evaluation() atau run_evaluation(sample=10).")
""", "det"),

    ("code", """
if LLM_ENABLED:
    eval_result = run_evaluation()   # jalankan 50 pertanyaan
    n = len(eval_result)
    exec_acc = eval_result.correct.mean()
    valid_sql_rate = (eval_result.agent_status == "success").mean()
    avg_retry = eval_result.retries.mean()
    med_latency = eval_result.latency.median()
    total_cost = eval_result.cost.sum()
    faith = eval_result.faithfulness.dropna().mean() if eval_result.faithfulness.notna().any() else None

    print("="*60)
    print("LAPORAN EVALUASI")
    print("="*60)
    print(f"Execution Accuracy   : {exec_acc*100:.1f}%   (target >= 80%)")
    print(f"Valid SQL Rate       : {valid_sql_rate*100:.1f}%   (target >= 90%)")
    print(f"Average Retry        : {avg_retry:.2f}      (target <= 0.5)")
    print(f"Median Latency       : {med_latency:.2f}s    (target <= 10s)")
    print(f"Faithfulness (avg)   : {('%.2f'%faith) if faith is not None else 'n/a'}")
    print(f"Total Cost (50 q)    : ${total_cost:.4f}")
    print("\\nAkurasi per kategori:")
    print((eval_result.groupby('category').correct.mean()*100).round(1).to_string())
    print("\\nAkurasi per difficulty:")
    print((eval_result.groupby('difficulty').correct.mean()*100).round(1).to_string())
else:
    print("LLM nonaktif — laporan evaluasi tidak dibuat. Aktifkan OPENAI_API_KEY lalu jalankan ulang bagian ini.")
""", "skip"),

    ("md", """
## 25. Error Analysis

Bila ada pertanyaan yang salah, kelompokkan penyebabnya untuk perbaikan terarah.
"""),
    ("code", """
if LLM_ENABLED and 'eval_result' in dir():
    wrong = eval_result[~eval_result.correct]
    if len(wrong):
        print("Pertanyaan yang belum benar:")
        print(wrong[["id","category","difficulty","agent_status","retries"]].to_string(index=False))
        print("\\nKategori error kandidat: wrong_join, wrong_filter, wrong_aggregation,")
        print("wrong_business_definition, empty_result, sql_syntax, timeout.")
    else:
        print("Tidak ada error — seluruh pertanyaan benar.")
else:
    print("Jalankan evaluasi (LLM aktif) untuk analisis error.")

# Trace keseluruhan dapat dikonversi ke DataFrame
if agent_traces:
    print("\\nContoh trace terakhir:")
    print(pd.DataFrame(agent_traces).tail(3).to_string(index=False))
""", "skip"),

    ("md", """
## 26. Keterbatasan

- **Bukan ReAct agent**, melainkan *bounded pipeline* deterministik (understand → generate → validate → execute → correct). Untuk domain SQL, keandalan lebih penting daripada kebebasan perencanaan. Ini pilihan desain sadar, bukan kekurangan.
- **Data sintetis** — pola dibuat manual; tidak mewakili dinamika bisnis nyata.
- **Faithfulness check berbasis pencocokan angka** — pendekatan heuristik; tidak menangkap kesalahan interpretasi kualitatif.
- **Execution accuracy** bergantung pada kualitas ground truth; pertanyaan ambigu bisa memiliki lebih dari satu jawaban benar.
- **Biaya/latency** bergantung pada provider LLM yang dipakai.

## 27. Roadmap

1. **Fase 1 (notebook ini)** — prototipe end-to-end.
2. **Fase 2** — modularisasi ke paket Python (`agent/`, `tools/`, `guardrails/`, `database/`, `visualization/`, `evaluation/`).
3. **Fase 3** — aplikasi web (FastAPI + Streamlit/Next.js), PostgreSQL, Redis.
4. **Fase 4** — produksi: auth, RBAC, row-level security, audit log, prompt versioning, semantic layer, model fallback, monitoring, cost budget, container.

## 28. Kesimpulan

SalesInsight Agent menunjukkan cara menghubungkan LLM ke database secara **aman dan terukur**: aturan bisnis ditegakkan di lapisan data (view), SQL divalidasi lewat AST sebelum dieksekusi, koneksi read-only plus timeout membatasi dampak, self-correction menaikkan keberhasilan, dan evaluasi berbasis *execution accuracy* memberi ukuran kualitas yang jujur. Pola ini dapat ditingkatkan menjadi aplikasi produksi tanpa mengubah prinsip intinya: **pipa deterministik dengan LLM sebagai komponen, bukan pengambil keputusan yang tak terkendali.**
"""),
]
