import pytest


def test_parse_pasal_extracts_number_and_text():
    from lexid.core import parse_articles
    text = "BAB I\nKETENTUAN UMUM\nPasal 1\n(1) Pekerja adalah setiap orang.\n(2) Upah adalah hak pekerja.\nPasal 2\nPembangunan ketenagakerjaan berlandaskan Pancasila."
    chunks = parse_articles(text, document_id="UU-13-2003")
    assert len(chunks) == 2
    assert chunks[0].article == "1"
    assert chunks[0].document_id == "UU-13-2003"
    assert "Upah adalah hak pekerja" in chunks[0].text


def test_version_resolver_returns_current_replacement():
    from lexid.core import VersionGraph
    graph = VersionGraph()
    graph.add_amendment("UU-13-2003", "156", "UU-6-2023", "81-47")
    status = graph.resolve("UU-13-2003", "156")
    assert status.status == "diubah"
    assert status.current_document == "UU-6-2023"
    assert status.current_article == "81-47"


def test_hybrid_search_finds_exact_legal_term():
    from lexid.core import ArticleChunk, HybridRetriever
    chunks = [
        ArticleChunk("UU-13-2003", "1", "Definisi tenaga kerja dan pekerja."),
        ArticleChunk("PP-35-2021", "40", "Pengusaha wajib membayar uang pesangon dan uang penghargaan masa kerja."),
    ]
    hits = HybridRetriever(chunks).search("berapa uang pesangon PHK", top_k=1)
    assert hits[0].chunk.article == "40"
    assert hits[0].score > 0


def test_citation_verifier_accepts_exact_and_rejects_fake():
    from lexid.core import ArticleChunk, Citation, CitationVerifier
    chunks = [ArticleChunk("PP-35-2021", "40", "Pengusaha wajib membayar uang pesangon.")]
    verifier = CitationVerifier(chunks)
    assert verifier.verify(Citation("PP-35-2021", "40", "wajib membayar uang pesangon")).valid
    assert not verifier.verify(Citation("PP-35-2021", "999", "pasal fiktif")).valid


def test_out_of_scope_query_is_detected():
    from lexid.core import is_in_scope
    assert is_in_scope("berapa pesangon pekerja yang di-PHK?")
    assert not is_in_scope("berapa tarif pajak pertambahan nilai?")


def test_refusal_when_no_verified_citation():
    from lexid.core import build_verified_answer
    answer = build_verified_answer("Jawaban tanpa bukti", citations=[], verification_results=[])
    assert answer.refused is True
    assert "Tidak ditemukan dasar hukum" in answer.answer


def test_parse_articles_ignores_explanatory_duplicate():
    from lexid.core import parse_articles
    text = "Pasal 1\nIsi norma utama.\nPENJELASAN\nPasal 1\nCukup jelas."
    chunks = parse_articles(text, document_id="UU-X", stop_at_explanation=True)
    assert len(chunks) == 1
    assert "Isi norma utama" in chunks[0].text


def test_search_empty_query_returns_no_hits():
    from lexid.core import ArticleChunk, HybridRetriever
    hits = HybridRetriever([ArticleChunk("UU-X", "1", "teks")]).search("", top_k=5)
    assert hits == []


def test_parse_articles_keeps_longest_duplicate_from_pdf_headers():
    from lexid.core import parse_articles
    text = (
        "Pasal 156\nPRESIDEN REPUBLIK INDONESIA - 61 -\n"
        "Pasal 156\n(1) Dalam hal terjadi PHK, pengusaha wajib membayar uang pesangon.\n"
        "Pasal 157\nKetentuan berikutnya."
    )
    chunks = parse_articles(text, document_id="UU-13-2003")
    pasal_156 = [c for c in chunks if c.article == "156"]
    assert len(pasal_156) == 1
    assert "wajib membayar uang pesangon" in pasal_156[0].text


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
