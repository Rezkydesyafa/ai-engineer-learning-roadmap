"""Grup 3: SQL guardrail (AST/SQLGlot), forced LIMIT, execute tool + timeout watchdog."""

CELLS = [
    ("md", """
## 11. SQL Validation Guardrail (berbasis AST)

Validasi memakai **AST SQLGlot** (dialek `duckdb`), bukan regex. Aturan:

1. **Single statement** — query multi-statement ditolak.
2. **SELECT-only** — hanya `SELECT` atau CTE (`WITH ... SELECT`). Semua DML/DDL diblokir.
3. **Table whitelist** — hanya tabel/view yang diizinkan.
4. **Blokir operasi berbahaya** — INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/ATTACH/COPY/PRAGMA/dst.
5. **Forced LIMIT** — jika tidak ada LIMIT atau LIMIT > 1000, dipaksa menjadi 1000 (dilakukan di AST, aman terhadap komentar/CTE).

Hasil validasi berupa objek terstruktur: `ok`, `reason`, dan `safe_sql` (SQL final yang sudah di-inject LIMIT).
"""),
    ("code", """
ALLOWED_TABLES = {
    "customers", "categories", "products", "orders", "order_items",
    "v_completed_sales",
}
MAX_LIMIT = 1000
QUERY_TIMEOUT_SEC = 5

# Node ekspresi yang menandakan operasi menulis/berbahaya
FORBIDDEN_NODES = (
    exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter,
    exp.Command,   # PRAGMA, CALL, COPY, dsb sering diparse sebagai Command
    exp.Merge,
)

@dataclass
class ValidationResult:
    ok: bool
    reason: str = ""
    safe_sql: Optional[str] = None

def _extract_tables(tree) -> set:
    names = set()
    for t in tree.find_all(exp.Table):
        names.add(t.name.lower())
    return names

def _cte_names(tree) -> set:
    names = set()
    for cte in tree.find_all(exp.CTE):
        if cte.alias:
            names.add(cte.alias.lower())
    return names

def validate_sql(sql: str) -> ValidationResult:
    if not sql or not sql.strip():
        return ValidationResult(False, "SQL kosong.")
    # 1) parse semua statement dgn dialek duckdb
    try:
        statements = sqlglot.parse(sql, dialect="duckdb")
    except Exception as e:
        return ValidationResult(False, f"Parse error: {str(e).splitlines()[0]}")
    statements = [s for s in statements if s is not None]
    if len(statements) != 1:
        return ValidationResult(False, f"Harus tepat satu statement (ditemukan {len(statements)}).")
    tree = statements[0]

    # 2) blokir node berbahaya di mana pun dalam pohon
    for node_type in FORBIDDEN_NODES:
        if tree.find(node_type) is not None:
            return ValidationResult(False, f"Operasi dilarang terdeteksi: {node_type.__name__}.")

    # 3) root harus SELECT (langsung atau via WITH)
    root = tree
    if not isinstance(root, (exp.Select,)):
        # WITH ... SELECT diparse sebagai Select dengan args['with']; jika bukan Select -> tolak
        if not (isinstance(root, exp.Subquery) and isinstance(root.this, exp.Select)):
            return ValidationResult(False, f"Hanya SELECT/CTE-SELECT yang diizinkan (root={type(root).__name__}).")

    # 4) whitelist tabel (abaikan nama CTE)
    ctes = _cte_names(tree)
    used = _extract_tables(tree) - ctes
    illegal = used - ALLOWED_TABLES
    if illegal:
        return ValidationResult(False, f"Tabel tidak diizinkan: {sorted(illegal)}.")

    # 5) forced LIMIT di AST
    limit = root.args.get("limit")
    if limit is not None:
        try:
            cur = int(limit.expression.this)
            if cur > MAX_LIMIT:
                root.set("limit", exp.Limit(expression=exp.Literal.number(MAX_LIMIT)))
        except Exception:
            root.set("limit", exp.Limit(expression=exp.Literal.number(MAX_LIMIT)))
    else:
        root.set("limit", exp.Limit(expression=exp.Literal.number(MAX_LIMIT)))

    safe_sql = root.sql(dialect="duckdb")
    return ValidationResult(True, "OK", safe_sql)

print("validate_sql siap.")
""", "det"),

    ("md", """
### 11.1 Uji cepat guardrail (deterministik)

Beberapa kasus positif/negatif untuk memastikan validator bekerja sebelum menyentuh LLM.
"""),
    ("code", """
_cases = [
    ("SELECT SUM(revenue) FROM v_completed_sales", True),
    ("WITH t AS (SELECT year, SUM(revenue) r FROM v_completed_sales GROUP BY year) SELECT * FROM t", True),
    ("SELECT * FROM v_completed_sales LIMIT 999999", True),   # akan dipaksa 1000
    ("DROP TABLE orders", False),
    ("DELETE FROM customers", False),
    ("UPDATE products SET unit_price = 0", False),
    ("SELECT * FROM orders; DROP TABLE orders", False),
    ("SELECT * FROM secret_table", False),
    ("COPY orders TO '/tmp/x.csv'", False),
    ("PRAGMA database_list", False),
]
_pass = 0
for sql, expect in _cases:
    r = validate_sql(sql)
    ok = (r.ok == expect)
    _pass += ok
    tag = "OK " if ok else "XX "
    print(f"{tag} expect={expect!s:5} got={r.ok!s:5}  {sql[:48]}")
print(f"\\nGuardrail unit: {_pass}/{len(_cases)} lulus")
assert _pass == len(_cases), "Ada kasus guardrail gagal!"
# cek forced limit benar-benar 1000
_r = validate_sql("SELECT * FROM v_completed_sales LIMIT 999999")
assert "1000" in _r.safe_sql and "999999" not in _r.safe_sql, "Forced LIMIT gagal"
print("Forced LIMIT OK ->", _r.safe_sql)
""", "det"),

    ("md", """
## 12. Database Query Tool (dengan timeout)

DuckDB tidak memiliki `statement_timeout` bawaan seperti PostgreSQL. Kita menerapkan **watchdog thread** yang memanggil `connection.interrupt()` bila query melewati batas waktu. `execute_sql` mengembalikan metadata lengkap untuk trace.
"""),
    ("code", """
@dataclass
class QueryResult:
    status: str                     # 'success' | 'error' | 'timeout'
    dataframe: Optional[pd.DataFrame] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    row_count: int = 0
    execution_time: float = 0.0
    executed_sql: Optional[str] = None

def execute_sql(sql: str, timeout_sec: int = QUERY_TIMEOUT_SEC) -> QueryResult:
    \"\"\"Validasi lalu eksekusi di koneksi read-only dengan timeout watchdog.\"\"\"
    v = validate_sql(sql)
    if not v.ok:
        return QueryResult(status="error", error_type="UnsafeSQL", error_message=v.reason, executed_sql=sql)

    safe_sql = v.safe_sql
    con = get_readonly_connection()
    timed_out = {"flag": False}
    def _watchdog():
        timed_out["flag"] = True
        try:
            con.interrupt()
        except Exception:
            pass
    timer = threading.Timer(timeout_sec, _watchdog)
    t0 = time.time()
    try:
        timer.start()
        df = con.execute(safe_sql).fetchdf()
        elapsed = time.time() - t0
        return QueryResult("success", dataframe=df, row_count=len(df),
                           execution_time=elapsed, executed_sql=safe_sql)
    except Exception as e:
        elapsed = time.time() - t0
        if timed_out["flag"]:
            return QueryResult("timeout", error_type="Timeout",
                               error_message=f"Query melebihi {timeout_sec}s",
                               execution_time=elapsed, executed_sql=safe_sql)
        return QueryResult("error", error_type=type(e).__name__,
                           error_message=str(e).splitlines()[0],
                           execution_time=elapsed, executed_sql=safe_sql)
    finally:
        timer.cancel()
        con.close()

# Uji deterministik: query benar mengembalikan data
_r = execute_sql("SELECT year, SUM(revenue) AS revenue FROM v_completed_sales GROUP BY year ORDER BY year")
assert _r.status == "success" and _r.row_count >= 1, _r
print("execute_sql OK:", _r.status, "rows=", _r.row_count)
print(_r.dataframe.assign(revenue=lambda d: d.revenue.map(lambda v: f"Rp{v:,.0f}")).to_string(index=False))
# Uji: unsafe ditolak sebelum eksekusi
_r2 = execute_sql("DROP TABLE orders")
assert _r2.status == "error" and _r2.error_type == "UnsafeSQL"
print("execute_sql menolak unsafe:", _r2.error_message)
""", "det"),
]
