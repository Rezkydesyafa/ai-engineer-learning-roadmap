"""Grup 4: Structured output, LLM client, SQL prompt, self-correction, viz, narrative, agent loop."""

CELLS = [
    ("md", """
## 12. Structured Output (Pydantic)

LLM diminta mengembalikan objek terstruktur, bukan teks bebas. Ini membuat parsing andal dan memungkinkan validasi. `chart` mendeskripsikan visualisasi yang diinginkan; `assumptions` memaksa model mengeksplisitkan asumsinya.
"""),
    ("code", """
class ChartConfig(BaseModel):
    required: bool = False
    chart_type: Optional[str] = None      # line|bar|hbar|grouped_bar|scatter
    x: Optional[str] = None
    y: list[str] = Field(default_factory=list)
    title: Optional[str] = None

class SQLGenerationResult(BaseModel):
    question_interpretation: str
    sql: str
    expected_columns: list[str] = Field(default_factory=list)
    chart: ChartConfig = Field(default_factory=ChartConfig)
    assumptions: list[str] = Field(default_factory=list)

print("Skema Pydantic siap.")
""", "det"),

    ("md", """
## 13. LLM Client Abstraction

Satu fungsi `llm_json()` memanggil endpoint OpenAI-compatible dengan `temperature=0` dan meminta output JSON. Mengembalikan `(dict, usage)` agar token bisa dicatat. Jika LLM nonaktif, fungsi memberi error yang jelas.
"""),
    ("code", """
@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    def cost(self) -> float:
        return (self.input_tokens/1000*PRICE_INPUT_PER_1K
                + self.output_tokens/1000*PRICE_OUTPUT_PER_1K)

def llm_json(system: str, user: str, temperature: float = 0.0):
    if not LLM_ENABLED:
        raise RuntimeError("LLM nonaktif: set OPENAI_API_KEY untuk memakai fitur ini.")
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
    )
    content = resp.choices[0].message.content
    u = resp.usage
    usage = Usage(getattr(u, "prompt_tokens", 0) or 0, getattr(u, "completion_tokens", 0) or 0)
    return json.loads(content), usage

def llm_text(system: str, user: str, temperature: float = 0.0):
    if not LLM_ENABLED:
        raise RuntimeError("LLM nonaktif: set OPENAI_API_KEY.")
    resp = client.chat.completions.create(
        model=MODEL_NAME, temperature=temperature,
        messages=[{"role":"system","content":system},{"role":"user","content":user}],
    )
    u = resp.usage
    return resp.choices[0].message.content, Usage(getattr(u,"prompt_tokens",0) or 0, getattr(u,"completion_tokens",0) or 0)

print("Klien LLM siap (aktif=%s)." % LLM_ENABLED)
""", "det"),

    ("md", """
## 14. SQL Generation Prompt

Prompt menyuntikkan schema + aturan bisdan + kontrak keamanan, lalu meminta `SQLGenerationResult` sebagai JSON. Instruksi menekankan pemakaian view `v_completed_sales` untuk metrik.
"""),
    ("code", """
SQL_SYSTEM = textwrap.dedent(f'''
Anda adalah analis data SQL untuk DuckDB. Ubah pertanyaan pengguna menjadi SATU query SELECT yang aman.

{SCHEMA_DOC}
{BUSINESS_RULES}

KONTRAK KEAMANAN (WAJIB):
- Hanya SELECT atau WITH ... SELECT. Tidak boleh INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/COPY/PRAGMA.
- Tepat satu statement, tanpa tanda ';' berganda.
- Hanya tabel/view yang diizinkan: customers, categories, products, orders, order_items, v_completed_sales.
- Untuk revenue/profit, WAJIB pakai view v_completed_sales.
- Selalu batasi hasil dengan LIMIT <= {MAX_LIMIT}.

Balas HANYA JSON valid dengan skema:
{{"question_interpretation": str, "sql": str, "expected_columns": [str],
  "chart": {{"required": bool, "chart_type": "line|bar|hbar|grouped_bar|scatter|null",
             "x": str|null, "y": [str], "title": str|null}},
  "assumptions": [str]}}
''').strip()

def generate_sql(question: str, retry_context: str = ""):
    user = question if not retry_context else f"{question}\\n\\n{retry_context}"
    data, usage = llm_json(SQL_SYSTEM, user)
    return SQLGenerationResult(**data), usage

print("Prompt generator SQL siap.")
""", "det"),

    ("md", """
## 15. Self-Correction (maksimal 2x)

Bila query gagal (error sintaksis/eksekusi/timeout, atau ditolak guardrail), LLM menerima konteks: SQL sebelumnya, pesan error, nomor percobaan, dan kontrak keamanan — lalu memperbaiki **tanpa mengubah maksud** pertanyaan. Hasil koreksi divalidasi ulang. Query berbahaya **tidak** memicu self-correction berulang tanpa batas; total percobaan = 1 awal + maksimal 2 retry.
"""),
    ("code", """
MAX_RETRY = 2

def build_retry_context(prev_sql: str, error_msg: str, attempt: int) -> str:
    return textwrap.dedent(f'''
    Percobaan sebelumnya (#{attempt}) GAGAL.
    SQL sebelumnya:
    {prev_sql}
    Pesan error:
    {error_msg}
    Perbaiki SQL agar valid dan aman TANPA mengubah maksud pertanyaan.
    Patuhi kontrak keamanan dan gunakan v_completed_sales untuk metrik.
    ''').strip()
print("Self-correction util siap.")
""", "det"),

    ("md", """
## 16. Visualization Tool

Membuat grafik Matplotlib sesuai `ChartConfig`. Prinsip: judul jelas, sumbu berlabel, data waktu terurut, dan grafik tidak dibuat bila tidak relevan. Angka besar diformat ringkas.
"""),
    ("code", """
def _fmt_rupiah(v, _pos=None):
    for unit, div in [("T",1e12),("M",1e9),("jt",1e6),("rb",1e3)]:
        if abs(v) >= div:
            return f"{v/div:.1f}{unit}"
    return f"{v:.0f}"

def create_visualization(df: pd.DataFrame, cfg: ChartConfig):
    if not cfg.required or df is None or df.empty or not cfg.chart_type:
        return None
    ycols = [c for c in cfg.y if c in df.columns]
    if not ycols or (cfg.x and cfg.x not in df.columns):
        return None
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = df[cfg.x] if cfg.x else df.index
    ct = cfg.chart_type
    try:
        if ct == "line":
            d = df.sort_values(cfg.x) if cfg.x else df
            for c in ycols: ax.plot(d[cfg.x] if cfg.x else d.index, d[c], marker="o", label=c)
        elif ct == "bar":
            ax.bar(x.astype(str), df[ycols[0]])
        elif ct == "hbar":
            ax.barh(x.astype(str), df[ycols[0]]); ax.invert_yaxis()
        elif ct == "grouped_bar":
            import numpy as _np
            idx = _np.arange(len(df)); w = 0.8/max(len(ycols),1)
            for i,c in enumerate(ycols): ax.bar(idx+i*w, df[c], w, label=c)
            ax.set_xticks(idx+w*(len(ycols)-1)/2); ax.set_xticklabels(x.astype(str), rotation=45, ha="right")
        elif ct == "scatter":
            ax.scatter(df[cfg.x], df[ycols[0]])
        else:
            plt.close(fig); return None
    except Exception as e:
        plt.close(fig); print("Viz error:", e); return None
    ax.set_title(cfg.title or "")
    if cfg.x: ax.set_xlabel(cfg.x)
    ax.set_ylabel(", ".join(ycols))
    if any(k in " ".join(ycols).lower() for k in ["revenue","profit","cost","price","value","aov"]):
        ax.yaxis.set_major_formatter(plt.FuncFormatter(_fmt_rupiah))
    if len(ycols) > 1 or ct in ("line","grouped_bar"): ax.legend()
    if ct not in ("hbar",): plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    return fig
print("create_visualization siap.")
""", "det"),

    ("md", """
## 17. Narrative Summarization + Faithfulness Check

Ringkasan naratif **hanya** boleh berdasarkan hasil query. Untuk mencegah halusinasi angka, kita menjalankan **faithfulness check**: setiap angka dalam ringkasan diverifikasi keberadaannya pada DataFrame hasil (dengan toleransi pembulatan). Angka yang tidak dapat diverifikasi ditandai.
"""),
    ("code", """
def _numbers_in_text(text: str):
    raw = re.findall(r"-?\\d[\\d.,]*", text or "")
    out = []
    for r in raw:
        s = r.replace(".", "").replace(",", ".") if r.count(",")==1 and r.count(".")>=1 else r.replace(",", "")
        try: out.append(float(s))
        except Exception: pass
    return out

def _df_number_pool(df: pd.DataFrame):
    pool = set()
    for col in df.select_dtypes(include=[np.number]).columns:
        for v in df[col].dropna().tolist():
            pool.add(round(float(v), 2))
    return pool

def faithfulness_check(summary: str, df: pd.DataFrame, tol_ratio: float = 0.02):
    if df is None or df.empty:
        return {"checked": 0, "unverified": [], "score": 1.0}
    pool = _df_number_pool(df)
    pool_list = sorted(pool)
    nums = [n for n in _numbers_in_text(summary) if abs(n) >= 100]  # abaikan angka kecil (tahun, indeks)
    unverified = []
    for n in nums:
        ok = any(abs(n-p) <= max(abs(p)*tol_ratio, 1.0) for p in pool_list)
        # toleransi persentase yang dihitung dari dua nilai pool juga diterima
        if not ok:
            unverified.append(n)
    checked = len(nums)
    score = 1.0 if checked == 0 else 1 - len(unverified)/checked
    return {"checked": checked, "unverified": unverified, "score": round(score,3)}

NARR_SYSTEM = ("Anda analis data. Buat ringkasan singkat (maks 6 kalimat) HANYA berdasarkan tabel hasil. "
               "Sebutkan angka kunci apa adanya. Jangan mengarang data di luar tabel. Bahasa Indonesia.")

def summarize(question: str, df: pd.DataFrame, assumptions: list[str]):
    head = df.head(50).to_markdown(index=False)
    user = f"Pertanyaan: {question}\\n\\nTabel hasil (maks 50 baris):\\n{head}\\n\\nAsumsi: {assumptions}"
    text, usage = llm_text(NARR_SYSTEM, user)
    fc = faithfulness_check(text, df)
    return text, usage, fc

print("Narrative + faithfulness siap.")
""", "det"),

    ("md", """
## 18. Agent Orchestration Loop

Menyatukan semuanya. `run_sales_agent()` menjalankan: generate SQL -> validasi+eksekusi -> self-correct (maks 2x) -> visualisasi -> ringkasan -> catat trace. Mengembalikan objek hasil yang rapi dan menyimpan trace ke `agent_traces`.
"""),
    ("code", """
agent_traces = []

@dataclass
class AgentResult:
    question: str
    status: str
    interpretation: str = ""
    final_sql: Optional[str] = None
    dataframe: Optional[pd.DataFrame] = None
    figure: object = None
    summary: str = ""
    assumptions: list = field(default_factory=list)
    faithfulness: dict = field(default_factory=dict)
    retries: int = 0
    error: Optional[str] = None
    latency_total: float = 0.0
    latency_query: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    est_cost: float = 0.0

def run_sales_agent(question: str, show_trace: bool = True) -> AgentResult:
    t0 = time.time()
    total_usage = Usage()
    res = AgentResult(question=question, status="error")
    retry_ctx = ""; last_err = ""; gen = None
    if not LLM_ENABLED:
        res.error = "LLM nonaktif (set OPENAI_API_KEY)."; res.latency_total = time.time()-t0
        return res
    for attempt in range(MAX_RETRY + 1):
        try:
            gen, u = generate_sql(question, retry_ctx)
        except Exception as e:
            last_err = f"Generation error: {e}"; break
        total_usage.input_tokens += u.input_tokens; total_usage.output_tokens += u.output_tokens
        res.interpretation = gen.question_interpretation; res.assumptions = gen.assumptions
        q = execute_sql(gen.sql)
        res.latency_query += q.execution_time
        if q.status == "success":
            res.status = "success"; res.final_sql = q.executed_sql
            res.dataframe = q.dataframe; res.retries = attempt
            try:
                res.figure = create_visualization(q.dataframe, gen.chart)
            except Exception as e:
                print("Viz gagal:", e)
            try:
                summary, su, fc = summarize(question, q.dataframe, gen.assumptions)
                total_usage.input_tokens += su.input_tokens; total_usage.output_tokens += su.output_tokens
                res.summary = summary; res.faithfulness = fc
            except Exception as e:
                res.summary = "(ringkasan gagal dibuat)"; print("Summary gagal:", e)
            break
        else:
            last_err = f"{q.error_type}: {q.error_message}"
            retry_ctx = build_retry_context(gen.sql, last_err, attempt + 1)
            res.retries = attempt + 1
    if res.status != "success":
        res.error = last_err or "gagal"
    res.latency_total = time.time() - t0
    res.input_tokens = total_usage.input_tokens; res.output_tokens = total_usage.output_tokens
    res.est_cost = total_usage.cost()
    agent_traces.append({
        "question": question, "status": res.status, "retries": res.retries,
        "final_sql": res.final_sql, "row_count": (0 if res.dataframe is None else len(res.dataframe)),
        "latency_query": round(res.latency_query,3), "latency_total": round(res.latency_total,3),
        "input_tokens": res.input_tokens, "output_tokens": res.output_tokens,
        "est_cost": round(res.est_cost,6),
        "faithfulness": res.faithfulness.get("score") if res.faithfulness else None,
        "error": res.error,
    })
    if show_trace:
        _render_result(res)
    return res

def _render_result(res: AgentResult):
    print("="*70); print("PERTANYAAN:", res.question); print("STATUS:", res.status)
    if res.status != "success":
        print("ERROR:", res.error); return
    print("\\nInterpretasi:", res.interpretation)
    if res.dataframe is not None:
        print("\\nTabel hasil (maks 20 baris):")
        print(res.dataframe.head(20).to_string(index=False))
    print("\\nRingkasan:\\n", res.summary)
    if res.faithfulness:
        fc = res.faithfulness
        print(f"\\nFaithfulness: score={fc['score']} checked={fc['checked']} unverified={fc['unverified']}")
    print("\\nSQL final:\\n", res.final_sql)
    if res.assumptions: print("\\nAsumsi:", res.assumptions)
    print(f"\\nMetadata: retries={res.retries} | query={res.latency_query:.2f}s | "
          f"total={res.latency_total:.2f}s | in_tok={res.input_tokens} out_tok={res.output_tokens} | "
          f"biaya=${res.est_cost:.6f}")
    if res.figure is not None:
        try: res.figure.show()
        except Exception: pass

print("Agent loop siap. Panggil run_sales_agent('pertanyaan Anda').")
""", "det"),
]
