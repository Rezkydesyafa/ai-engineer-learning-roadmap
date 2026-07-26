"""Grup 2: Dataset sintetis bercerita, DuckDB, schema docs, business rules, read-only conn."""

CELLS = [
    ("md", """
## 5. Pembuatan Dataset Sintetis (Reproducible & Bercerita)

Dataset dibuat sintetis agar: tidak memakai data pribadi, dapat direproduksi (`SEED` tetap), dan *ground truth* mudah dibuat.

**Prinsip penting:** data acak murni menghasilkan grafik datar dan demo yang hambar. Maka kita **menanamkan cerita** ke dalam data:

- **Tren pertumbuhan** year-over-year (2025 lebih tinggi dari 2024).
- **Musiman**: puncak akhir tahun (Nov–Des), lembah awal tahun.
- **Dominasi regional**: Jawa menyumbang porsi terbesar.
- **Produk bintang**: sebagian produk sengaja tumbuh tajam agar analisis "pertumbuhan tertinggi" bermakna.
- **Status order** realistis: mayoritas `Completed`, sebagian `Cancelled`/`Refunded` (penting untuk menguji aturan bisnis).
"""),
    ("code", """
from faker import Faker
fake = Faker("id_ID")
Faker.seed(SEED)

N_CUSTOMERS = 1000
N_PRODUCTS  = 100
N_ORDERS    = 20000
START_YEAR, END_YEAR = 2024, 2025

REGIONS = {
    "Jawa": 0.45, "Sumatra": 0.20, "Kalimantan": 0.12,
    "Sulawesi": 0.10, "Bali Nusra": 0.08, "Papua Maluku": 0.05,
}
CITIES = {
    "Jawa": ["Jakarta", "Bandung", "Surabaya", "Semarang", "Yogyakarta"],
    "Sumatra": ["Medan", "Palembang", "Padang", "Pekanbaru"],
    "Kalimantan": ["Pontianak", "Balikpapan", "Banjarmasin"],
    "Sulawesi": ["Makassar", "Manado", "Palu"],
    "Bali Nusra": ["Denpasar", "Mataram", "Kupang"],
    "Papua Maluku": ["Jayapura", "Ambon", "Sorong"],
}
SEGMENTS = ["Retail", "Wholesale", "Corporate"]
CATEGORIES = ["Electronics", "Fashion", "Home & Living", "Groceries",
              "Beauty", "Sports", "Toys", "Automotive"]
CHANNELS = ["Website", "Mobile", "Marketplace", "Offline"]
PAYMENTS = ["Transfer", "E-Wallet", "Card", "COD"]
STATUS_WEIGHTS = {"Completed": 0.82, "Cancelled": 0.10, "Refunded": 0.08}

def _weighted(mapping):
    keys = list(mapping); w = np.array(list(mapping.values()), float); w /= w.sum()
    return keys, w
""", "det"),

    ("md", """
### 5.1 Tabel dimensi: customers, categories, products

`products` diberi *growth factor* per produk. Sebagian kecil produk menjadi "bintang" (tumbuh tajam) agar use case *pertumbuhan produk* menghasilkan ranking yang bermakna.
"""),
    ("code", """
# customers
reg_keys, reg_w = _weighted(REGIONS)
cust_rows = []
for cid in range(1, N_CUSTOMERS + 1):
    region = np.random.choice(reg_keys, p=reg_w)
    city = random.choice(CITIES[region])
    cust_rows.append({
        "customer_id": cid,
        "customer_name": fake.name(),
        "customer_segment": random.choices(SEGMENTS, weights=[0.6, 0.25, 0.15])[0],
        "city": city,
        "region": region,
        "registered_at": fake.date_between(start_date="-3y", end_date="today"),
    })
customers = pd.DataFrame(cust_rows)

# categories
categories = pd.DataFrame(
    {"category_id": range(1, len(CATEGORIES) + 1), "category_name": CATEGORIES}
)

# products (+ growth_factor tersembunyi untuk membentuk cerita)
prod_rows = []
for pid in range(1, N_PRODUCTS + 1):
    cat_id = random.randint(1, len(CATEGORIES))
    unit_cost = round(random.uniform(10_000, 2_000_000), -2)
    margin = random.uniform(0.15, 0.55)
    unit_price = round(unit_cost * (1 + margin), -2)
    is_star = random.random() < 0.12   # 12% produk "bintang"
    growth = random.uniform(1.6, 2.8) if is_star else random.uniform(0.8, 1.25)
    prod_rows.append({
        "product_id": pid,
        "product_name": f"{random.choice(CATEGORIES)} {fake.word().title()} {random.randint(100,999)}",
        "category_id": cat_id,
        "unit_cost": unit_cost,
        "unit_price": unit_price,
        "_growth_factor": growth,
    })
products = pd.DataFrame(prod_rows)
print("customers", customers.shape, "| categories", categories.shape, "| products", products.shape)
""", "det"),

    ("md", """
### 5.2 Fakta: orders & order_items (dengan tren + musiman)

Probabilitas sebuah order jatuh pada bulan tertentu dibentuk oleh **faktor musiman** (puncak akhir tahun) dan **faktor tahun** (2025 > 2024). Kuantitas dan pemilihan produk dipengaruhi *growth factor* produk pada 2025, sehingga "produk bintang" benar-benar melonjak di tahun kedua.
"""),
    ("code", """
# Bobot musiman per bulan (1..12): lembah awal tahun, puncak Nov-Des
SEASONAL = np.array([0.7,0.75,0.9,0.95,1.0,1.05,1.1,1.05,1.1,1.2,1.45,1.6])
YEAR_FACTOR = {2024: 1.0, 2025: 1.35}  # pertumbuhan YoY

# Bangun distribusi (year, month)
ym = [(y, m) for y in range(START_YEAR, END_YEAR + 1) for m in range(1, 13)]
ym_w = np.array([SEASONAL[m - 1] * YEAR_FACTOR[y] for (y, m) in ym], float)
ym_w /= ym_w.sum()

st_keys, st_w = _weighted(STATUS_WEIGHTS)
prod_ids = products["product_id"].to_numpy()
prod_lookup = products.set_index("product_id")

order_rows, item_rows = [], []
order_item_id = 0
from datetime import date
import calendar

for oid in range(1, N_ORDERS + 1):
    idx = np.random.choice(len(ym), p=ym_w)
    y, m = ym[idx]
    day = random.randint(1, calendar.monthrange(y, m)[1])
    order_date = date(y, m, day)
    status = np.random.choice(st_keys, p=st_w)
    order_rows.append({
        "order_id": oid,
        "customer_id": random.randint(1, N_CUSTOMERS),
        "order_date": order_date,
        "order_status": status,
        "sales_channel": random.choices(CHANNELS, weights=[0.3,0.35,0.25,0.1])[0],
        "payment_method": random.choice(PAYMENTS),
    })
    # 1..5 item per order
    for _ in range(random.randint(1, 5)):
        order_item_id += 1
        pid = int(np.random.choice(prod_ids))
        row = prod_lookup.loc[pid]
        gf = row["_growth_factor"] if y == 2025 else 1.0
        base_qty = np.random.poisson(2) + 1
        qty = max(1, int(round(base_qty * (gf if gf > 1 else 1))))
        unit_price = float(row["unit_price"])
        discount = round(unit_price * qty * random.choice([0, 0, 0, 0.05, 0.1, 0.15]), -2)
        revenue = round(unit_price * qty - discount, -2)
        cost = round(float(row["unit_cost"]) * qty, -2)
        item_rows.append({
            "order_item_id": order_item_id,
            "order_id": oid,
            "product_id": pid,
            "quantity": qty,
            "unit_price": unit_price,
            "discount": discount,
            "revenue": revenue,
            "cost": cost,
            "profit": round(revenue - cost, -2),
        })

orders = pd.DataFrame(order_rows)
order_items = pd.DataFrame(item_rows)
print("orders", orders.shape, "| order_items", order_items.shape)
print("status dist:\\n", orders.order_status.value_counts(normalize=True).round(3).to_string())
""", "det"),

    ("md", """
## 6. Exploratory Data Analysis singkat

Memastikan cerita benar-benar tertanam: revenue 2025 harus di atas 2024, dan ada pola musiman.
"""),
    ("code", """
_items = order_items.merge(orders[["order_id","order_date","order_status"]], on="order_id")
_items = _items[_items.order_status == "Completed"].copy()
_items["year"] = pd.to_datetime(_items.order_date).dt.year
_items["month"] = pd.to_datetime(_items.order_date).dt.month
by_year = _items.groupby("year").revenue.sum()
print("Revenue per tahun (Completed):")
print(by_year.map(lambda v: f"Rp{v:,.0f}").to_string())
assert by_year.get(2025, 0) > by_year.get(2024, 0), "Cerita gagal: 2025 harus > 2024"
print("\\nOK: tren pertumbuhan YoY tertanam.")
""", "det"),

    ("md", """
## 7. DuckDB Setup

Semua tabel ditulis ke database file DuckDB. Kolom internal `_growth_factor` **tidak** ikut ditulis (hanya alat pembentuk cerita).
"""),
    ("code", """
DB_PATH = "sales.db"
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

_con = duckdb.connect(DB_PATH)  # koneksi write, hanya untuk setup
_con.execute("CREATE TABLE customers  AS SELECT * FROM customers")
_con.execute("CREATE TABLE categories AS SELECT * FROM categories")
_con.execute("CREATE TABLE products   AS SELECT * EXCLUDE (_growth_factor) FROM products")
_con.execute("CREATE TABLE orders      AS SELECT * FROM orders")
_con.execute("CREATE TABLE order_items AS SELECT * FROM order_items")
print("Tabel dibuat:", [r[0] for r in _con.execute("SHOW TABLES").fetchall()])
""", "det"),

    ("md", """
## 8. Dokumentasi Schema & 9. Definisi Metrik Bisnis (Semantic Views)

Inilah inti keandalan: **aturan bisnis ditegakkan sebagai VIEW**, bukan diserahkan ke LLM.

- `v_completed_sales` — hanya order `Completed`, sudah join ke `orders`. Semua perhitungan revenue/profit sebaiknya dari sini.
- Definisi kuartal, AOV, dan pertumbuhan didokumentasikan agar LLM konsisten.

Dengan cara ini, meski LLM lupa memfilter status, angka dari view tetap benar.
"""),
    ("code", """
_con.execute('''
CREATE VIEW v_completed_sales AS
SELECT
    oi.order_item_id, oi.order_id, oi.product_id,
    oi.quantity, oi.unit_price, oi.discount,
    oi.revenue, oi.cost, oi.profit,
    o.customer_id, o.order_date, o.sales_channel, o.payment_method,
    EXTRACT(year  FROM o.order_date) AS year,
    EXTRACT(month FROM o.order_date) AS month,
    EXTRACT(quarter FROM o.order_date) AS quarter
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status = 'Completed';
''')
print("View v_completed_sales dibuat.")
_con.close()   # tutup koneksi write; selanjutnya read-only
print("Koneksi write ditutup.")
""", "det"),

    ("code", """
SCHEMA_DOC = '''
TABEL & VIEW (semua kolom hanya-baca):

view v_completed_sales  -- GUNAKAN INI untuk semua metrik revenue/profit (hanya order Completed)
  order_item_id, order_id, product_id, quantity, unit_price, discount,
  revenue, cost, profit, customer_id, order_date, sales_channel, payment_method,
  year, month, quarter

table customers(customer_id, customer_name, customer_segment, city, region, registered_at)
table categories(category_id, category_name)
table products(product_id, product_name, category_id, unit_cost, unit_price)
table orders(order_id, customer_id, order_date, order_status, sales_channel, payment_method)
table order_items(order_item_id, order_id, product_id, quantity, unit_price, discount, revenue, cost, profit)

RELASI:
  products.category_id     -> categories.category_id
  orders.customer_id       -> customers.customer_id
  order_items.order_id     -> orders.order_id
  order_items.product_id   -> products.product_id
'''

BUSINESS_RULES = '''
ATURAN BISNIS:
1. Revenue & profit HANYA dari order berstatus Completed. Gunakan view v_completed_sales.
2. Order Cancelled dan Refunded TIDAK dihitung sebagai revenue.
3. Revenue = kolom revenue; Profit = kolom profit (sudah bersih diskon & cost).
4. Average Order Value (AOV) = SUM(revenue) / COUNT(DISTINCT order_id).
5. Kuartal: Q1=Jan-Mar, Q2=Apr-Jun, Q3=Jul-Sep, Q4=Okt-Des (pakai kolom quarter).
6. Pertumbuhan (%) = (akhir - awal) / awal * 100. Jika awal = 0 -> tidak dapat dihitung.
7. Mata uang: Rupiah (IDR).
8. Untuk analisis produk/kategori/wilayah, join view v_completed_sales ke tabel dimensi.
'''
print("Schema & business rules terdokumentasi.")
""", "det"),

    ("md", """
## 10. Koneksi Database Read-Only

Setelah setup selesai, agent **hanya** membuka DuckDB dalam mode read-only. Ini lapisan pertahanan terluar: bahkan jika guardrail tertembus, engine menolak operasi tulis.
"""),
    ("code", """
def get_readonly_connection():
    return duckdb.connect(DB_PATH, read_only=True)

# Uji: koneksi read-only menolak operasi tulis
_ro = get_readonly_connection()
_denied = False
try:
    _ro.execute("CREATE TABLE hack(x INT)")
except Exception as e:
    _denied = True
    _msg = str(e).splitlines()[0]
_ro.close()
assert _denied, "read-only gagal menolak tulis!"
print("OK read-only menolak tulis:", _msg[:80])
""", "det"),
]
