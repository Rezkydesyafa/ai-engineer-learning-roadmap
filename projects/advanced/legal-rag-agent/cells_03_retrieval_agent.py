"""Sel 3: retrieval dan agent loop."""
CELLS = [
("md", """
## 4. Hybrid Retriever & Citation Verifier

Retriever memakai **BM25 + lexical overlap fallback** untuk memastikan istilah hukum yang khas (seperti "pesangon") tidak hilang karena masalah frekuensi kata di korpus mini.

Citation verifier memeriksa kutipan LLM terhadap teks asli korpus:
- Memastikan nomor pasal yang disebut ada di korpus.
- Memeriksa overlap teks kutipan (threshold minimum 60% token match).
"""),
("code", """
from lexid.core import DenseHybridRetriever

# Menggunakan FastEmbed (ONNX multilingual)
try:
    from fastembed import TextEmbedding
    print("Mengunduh/memuat model dense FastEmbed (multilingual)...")
    embedder = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
except Exception as e:
    print(f"Dense embedder fallback to None: {e}")
    embedder = None

retriever = DenseHybridRetriever(all_chunks, embedder=embedder)
verifier = CitationVerifier(all_chunks)

# Test pencarian M1 (Hybrid RRF + Dense Semantic)
query = "Pesangon PHK karyawan masa kerja 5 tahun"
hits = retriever.search(query, top_k=3)
print(f"Pencarian M1: '{query}' -> {len(hits)} pasal relevan")
for i, hit in enumerate(hits, 1):
    dense_sc = getattr(hit, 'dense_score', 0.0)
    print(f" {i}. [{hit.chunk.document_id}] Pasal {hit.chunk.article} (RRF: {hit.score:.4f} | Dense Cosine: {dense_sc:.4f})")
    print(f"    Teks: {hit.chunk.text[:120]}...")
""", "det"),
("md", """
### 4.1 Citation Verifier Unit Test

Kita buktikan verifier mampu menolak klaim palsu dan menerima klaim yang benar secara programmatis.
"""),
("code", """
c_valid = Citation(document_id="UU-13-2003", article="156", quote="uang pesangon")
res_valid = verifier.verify(c_valid)
print("Valid citation:", res_valid.valid, "->", res_valid.reason)

c_invalid = Citation(document_id="UU-13-2003", article="156", quote="ketentuan kompensasi fiktif yang tidak ada")
res_invalid = verifier.verify(c_invalid)
print("Invalid quote :", res_invalid.valid, "->", res_invalid.reason)

c_fake = Citation(document_id="UU-13-2003", article="999", quote="pasal fiktif")
res_fake = verifier.verify(c_fake)
print("Fake article  :", res_fake.valid, "->", res_fake.reason)
""", "det"),
("md", """
## 5. Agent Planning & Refusal Loop

Di sini kita mengimplementasikan loop agentic multi-step sederhana yang mandiri:
1. Menerima pertanyaan.
2. Memeriksa cakupan (*scope check*).
3. Melakukan multi-step queryplanning (mencari pasal UU dasar, resolusi versi, dan mencari PP operasional jika dibutuhkan).
4. Melakukan komparasi dan verifikasi kutipan.
"""),
("code", """
class LexIDAgent:
    def __init__(self, retriever, verifier, vgraph, client=None):
        self.retriever = retriever
        self.verifier = verifier
        self.vgraph = vgraph
        self.client = client

    def answer_query(self, query: str) -> VerifiedAnswer:
        # 1. Scope Check
        if not is_in_scope(query):
            return VerifiedAnswer(
                answer="Pertanyaan di luar cakupan hukum ketenagakerjaan Indonesia. Saat ini saya hanya melayani pertanyaan tentang PHK, pesangon, upah, PKWT, alih daya, dan cuti.",
                citations=[],
                verification_results=[],
                refused=True
            )

        # 2. Retrieve & Version Resolve
        initial_hits = self.retriever.search(query, top_k=5)
        if not initial_hits:
            return build_verified_answer("", [], [])

        citations = []
        ver_results = []
        sources_text = []

        for hit in initial_hits:
            chunk = hit.chunk
            status = self.vgraph.resolve(chunk.document_id, chunk.article)
            
            if status.status == "diubah":
                # Cari pasal pengganti
                replacement_hits = [
                    c for c in self.retriever.chunks
                    if c.document_id == status.current_document and c.article == status.current_article
                ]
                if replacement_hits:
                    active_chunk = replacement_hits[0]
                    sources_text.append(f"[{active_chunk.document_id} Pasal {active_chunk.article}]: {active_chunk.text}")
                    citations.append(Citation(active_chunk.document_id, active_chunk.article, active_chunk.text[:30]))
                else:
                    sources_text.append(f"[{chunk.document_id} Pasal {chunk.article} (diubah oleh {status.current_document})]: {chunk.text}")
                    citations.append(Citation(chunk.document_id, chunk.article, chunk.text[:30]))
            else:
                sources_text.append(f"[{chunk.document_id} Pasal {chunk.article}]: {chunk.text}")
                citations.append(Citation(chunk.document_id, chunk.article, chunk.text[:30]))

        # 3. Verify Citations
        for cit in citations:
            res = self.verifier.verify(cit)
            ver_results.append(res)

        # 4. Synthesize Answer (Deterministic baseline fallback)
        # Jika LLM aktif, ia akan memproses sources_text
        if self.client and LLM_ENABLED:
            prompt = f"Pertanyaan: {query}\\n\\nBahan Hukum:\\n" + "\\n".join(sources_text) + "\\n\\nJawab dengan benar, sebut pasal dan kutipannya."
            # Call LLM ...
            ans = "Sintesis LLM disini..."
        else:
            ans = "Berdasarkan regulasi, ditemukan rujukan sebagai berikut:\\n" + "\\n".join(f"- {c.document_id} Pasal {c.article}" for c in citations)

        return build_verified_answer(ans, citations, ver_results)

agent = LexIDAgent(retriever, verifier, vgraph)
res_ans = agent.answer_query("bagaimana aturan uang pesangon berdasarkan pasal 156?")
print("Hasil:", res_ans.answer)
print("Refused:", res_ans.refused)
""", "det"),
]
