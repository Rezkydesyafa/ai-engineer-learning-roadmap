"""Sel 2: ingestion dan extraction."""
CELLS = [
("md", """
## 3. Ingestion dan Ekstraksi Per-Pasal

Dokumen hukum tidak boleh di-*chunk* per-512-token, karena akan memotong konteks mengikat dari bab atau memisahkan ayat yang saling bergantung. PoC ini mengekstrak unit terdasar: **Pasal**. Tiap pasal dipertahankan utuh dan menyimpan metadata sumbernya.

Karena `UU-6-2023` berisi 1126 halaman lintas sektor (klaster penataan ruang, dsb.), kita hanya akan mengekstrak **Bab IV Bagian Kedua (Ketenagakerjaan)** untuk mengunci scope ke UU 13/2003 yang diubah.
"""),
("code", """
def extract_pdf_text(path: Path) -> str:
    doc = fitz.open(path)
    # Filter khusus UU-6-2023 (Cipta Kerja) -> klaster Ketenagakerjaan
    # Halaman 542 - 584 mengatur ketenagakerjaan
    if path.name == "UU-6-2023-CiptaKerja.pdf":
        text = "".join(doc[i].get_text() for i in range(541, 584))
    else:
        text = "".join(doc[i].get_text() for i in range(len(doc)))
    doc.close()
    return text

raw_texts = {}
for doc_id, path in PDF_FILES.items():
    if path.exists():
        raw_texts[doc_id] = extract_pdf_text(path)
        print(f"[{doc_id}] {len(raw_texts[doc_id])} karakter terambil")
""", "det"),
("code", """
all_chunks = []
for doc_id, txt in raw_texts.items():
    stop_at_explanation = doc_id == "UU-13-2003"
    doc_chunks = parse_articles(txt, doc_id, stop_at_explanation)
    print(f"[{doc_id}] {len(doc_chunks)} pasal terurai")
    all_chunks.extend(doc_chunks)

print(f"Total chunk pasal korpus v1: {len(all_chunks)}")
# Contoh satu chunk UU 13/2003
c = [c for c in all_chunks if c.document_id == "UU-13-2003" and c.article == "156"]
if c:
    print("\\nSampel Pasal 156 UU 13/2003:")
    print(c[0].text[:300] + "...")
""", "det"),
("md", """
### 3.1 Resolusi Versi (Version Graph)

Inilah *killer feature* sistem ini: **Version-aware retrieval**. UU 6/2023 mengubah 81 pasal UU 13/2003. Saat LLM menemukan Pasal 156 di teks UU 13/2003, ia akan diberi tahu bahwa pasal tersebut *telah diubah*, dan harus merujuk pada versi terbarunya di UU 6/2023.

Di sini kita menganotasi sebagian perubahan tersebut ke dalam graph relasional.
"""),
("code", """
vgraph = VersionGraph()

# Pemetaan pasal kunci UU 13/2003 ke teks pengganti di UU 6/2023.
# UU 6/2023 Pasal 81 adalah *ketentuan perubahan*; norma hasilnya tetap diberi
# nomor pasal (mis. Pasal 156) di klaster ketenagakerjaan. Karena itu resolver
# harus menunjuk Pasal 156 versi UU 6/2023, BUKAN salah menunjuk "Pasal 81".
amended_articles = [
    "66", "77", "78", "79", "88", "88A", "88B", "88C", "88D", "88E",
    "89", "90", "90A", "90B", "92", "151", "151A", "152", "153", "154",
    "154A", "155", "156", "157", "157A", "160", "161", "162", "163",
    "164", "165", "166",
]
amendments_uu13 = {article: article for article in amended_articles}  # current article in UU 6/2023
# Provenance amendment: UU 6/2023 Pasal 81 (divalidasi manual per pasal pada M2).

for old_art, new_art in amendments_uu13.items():
    vgraph.add_amendment(
        old_doc="UU-13-2003", old_art=old_art,
        new_doc="UU-6-2023", new_art=new_art
    )

stat_156 = vgraph.resolve("UU-13-2003", "156")
print(f"Status UU-13-2003 Psl 156: {stat_156.status}")
if stat_156.status == "diubah":
    print(f"  -> Pengganti: {stat_156.current_document} Psl {stat_156.current_article}")

stat_1 = vgraph.resolve("UU-13-2003", "1")
print(f"Status UU-13-2003 Psl 1  : {stat_1.status}")
""", "det"),
]
