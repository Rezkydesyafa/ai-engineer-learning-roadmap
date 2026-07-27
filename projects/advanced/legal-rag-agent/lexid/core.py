"""LexID Core — Core data structures and engine for legal RAG."""
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from rank_bm25 import BM25Okapi


@dataclass
class ArticleChunk:
    document_id: str
    article: str
    text: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class Citation:
    document_id: str
    article: str
    quote: str


@dataclass
class VerificationResult:
    citation: Citation
    valid: bool
    reason: str


@dataclass
class VerifiedAnswer:
    answer: str
    citations: List[Citation]
    verification_results: List[VerificationResult]
    refused: bool = False


@dataclass
class ArticleStatus:
    status: str
    current_document: str
    current_article: str


def parse_articles(text: str, document_id: str, stop_at_explanation: bool = False) -> List[ArticleChunk]:
    if stop_at_explanation:
        parts = re.split(r'\b(PENJELASAN|P E N J E L A S A N)\b', text, maxsplit=1)
        text = parts[0]

    pattern = re.compile(r'\bPasal\s+(\d+[A-Z]?)\b')
    matches = list(pattern.finditer(text))
    if not matches:
        return []

    chunks = []
    seen_articles = set()

    for i, match in enumerate(matches):
        article_num = match.group(1)
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start_pos:end_pos].strip()
        
        # Bersihkan PDF header noise
        content = re.sub(r'(?i)presiden\s+republik\s+indonesia\s*-\s*\d+\s*-', '', content).strip()

        if article_num in seen_articles:
            # Jika sudah pernah dilihat tapi konten yang baru lebih substansial (>10 char),
            # mungkin itu isi asli dan yang sebelumnya hanya header PDF noise.
            # Gabungkan atau ganti isinya supaya tidak menyimpan chunk kosong.
            for chunk in chunks:
                if chunk.article == article_num:
                    if len(content) > len(chunk.text) and len(chunk.text) < 50:
                        chunk.text = content
                    elif len(content) > 10 and content not in chunk.text:
                        chunk.text += "\n" + content
                    break
            continue

        seen_articles.add(article_num)
        chunks.append(
            ArticleChunk(
                document_id=document_id,
                article=article_num,
                text=content,
                metadata={"article_num": article_num},
            )
        )

    return chunks


class VersionGraph:
    def __init__(self):
        self._amendments: Dict[str, Dict[str, tuple]] = {}

    def add_amendment(self, old_doc: str, old_art: str, new_doc: str, new_art: str):
        if old_doc not in self._amendments:
            self._amendments[old_doc] = {}
        self._amendments[old_doc][old_art] = (new_doc, new_art)

    def resolve(self, doc_id: str, article: str) -> ArticleStatus:
        if doc_id in self._amendments and article in self._amendments[doc_id]:
            new_doc, new_art = self._amendments[doc_id][article]
            return ArticleStatus(status="diubah", current_document=new_doc, current_article=new_art)
        return ArticleStatus(status="berlaku", current_document=doc_id, current_article=article)


@dataclass
class SearchHit:
    chunk: ArticleChunk
    score: float
    dense_score: float = 0.0


class HybridRetriever:
    def __init__(self, chunks: List[ArticleChunk]):
        self.chunks = chunks
        self._tokenized = [c.text.lower().split() for c in chunks]
        self.bm25 = BM25Okapi(self._tokenized) if chunks else None

    def search(self, query: str, top_k: int = 5) -> List[SearchHit]:
        if not query.strip() or not self.bm25 or not self.chunks:
            return []
        tokens = query.lower().split()
        query_terms = set(tokens)
        bm25_scores = self.bm25.get_scores(tokens)

        scored = []
        for chunk, doc_tokens, bm25_score in zip(self.chunks, self._tokenized, bm25_scores):
            clean_terms = {re.sub(r"[^a-z0-9]", "", token) for token in doc_tokens}
            lexical_overlap = len(query_terms.intersection(clean_terms)) / max(len(query_terms), 1)
            # BM25 bisa nol/negatif pada korpus sangat kecil; overlap menjamin exact legal term tetap ditemukan.
            score = max(float(bm25_score), 0.0) + lexical_overlap
            if score > 0:
                scored.append((chunk, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return [SearchHit(chunk=chunk, score=score) for chunk, score in scored[:top_k]]


def reciprocal_rank_fusion(bm25_ranked: List[str], dense_ranked: List[str], k: int = 60) -> Dict[str, float]:
    scores = {}
    for rank, doc_id in enumerate(bm25_ranked, 1):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    for rank, doc_id in enumerate(dense_ranked, 1):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    
    # Supaya bisa memanggil item pertama yang rankingnya tertinggi dengan list/index
    class RankedDict(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._sorted = sorted(self.items(), key=lambda x: x[1], reverse=True)
            self._keys = [x[0] for x in self._sorted]
            
        def __getitem__(self, key):
            if isinstance(key, int):
                return self._keys[key]
            return super().__getitem__(key)
            
    return RankedDict(scores)


class DenseHybridRetriever(HybridRetriever):
    def __init__(self, chunks: List[ArticleChunk], embedder=None):
        super().__init__(chunks)
        self.embedder = embedder
        self._doc_ids = [f"{c.document_id}:{c.article}" for c in chunks]
        self._chunk_map = {doc_id: c for doc_id, c in zip(self._doc_ids, chunks)}
        
        if self.embedder:
            texts = [c.text for c in chunks]
            vectors = list(self.embedder.embed(texts))
            # Normalisasi vektor supaya np.dot = cosine similarity
            import numpy as np
            self._vectors = np.array(vectors)
            norms = np.linalg.norm(self._vectors, axis=1, keepdims=True)
            self._vectors = np.divide(self._vectors, norms, out=np.zeros_like(self._vectors), where=norms!=0)
        else:
            self._vectors = None

    def search(self, query: str, top_k: int = 5) -> List[SearchHit]:
        if not query.strip() or not self.chunks:
            return []
            
        # 1. BM25 Search
        bm25_hits = super().search(query, top_k=len(self.chunks))
        bm25_ranked = [f"{h.chunk.document_id}:{h.chunk.article}" for h in bm25_hits]
        
        dense_hits = []
        dense_ranked = []
        
        # 2. Dense Semantic Search
        if self.embedder and self._vectors is not None:
            import numpy as np
            q_vec = list(self.embedder.embed([query]))[0]
            q_vec = np.array(q_vec)
            q_norm = np.linalg.norm(q_vec)
            if q_norm > 0:
                q_vec = q_vec / q_norm
            
            cos_scores = np.dot(self._vectors, q_vec)
            scored_dense = sorted(zip(self._doc_ids, cos_scores), key=lambda x: x[1], reverse=True)
            dense_ranked = [doc_id for doc_id, score in scored_dense if score > 0]
            dense_hits = {doc_id: float(score) for doc_id, score in scored_dense}

        # 3. Hybrid RRF Fusion
        if not dense_ranked:
            # Fallback jika model dense mati / tidak tersedia
            hits = []
            for hit in bm25_hits[:top_k]:
                # Injeksi dense_score=0.0 agar interface konsisten
                hit.dense_score = 0.0
                hits.append(hit)
            return hits
            
        # Legal query punya istilah / nomor pasal presisi, jadi BM25 diberi 2x bobot.
        # Dense dipakai untuk memperluas recall semantic, bukan mengalahkan sinyal lexical.
        fused = reciprocal_rank_fusion(bm25_ranked + bm25_ranked, dense_ranked, k=60)
        
        results = []
        for i in range(min(top_k, len(fused))):
            doc_id = fused[i]
            rrf_score = fused[doc_id]
            dense_score = dense_hits.get(doc_id, 0.0)
            
            chunk = self._chunk_map[doc_id]
            hit = SearchHit(chunk=chunk, score=rrf_score)
            hit.dense_score = dense_score
            results.append(hit)
            
        return results


@dataclass
class QueryPlan:
    in_scope: bool
    subqueries: List[str]
    article_hints: List[str]
    rationale: str


class HeuristicLegalPlanner:
    """Planner deterministic untuk mode offline; LLM planner M2 memakai schema sama."""
    RULES = [
        ("perjanjian kerja berakhir", "UU-13-2003:61", [
            "UU 13 Tahun 2003 Pasal 61 berakhirnya perjanjian kerja",
            "syarat perjanjian kerja berakhir pekerja meninggal jangka waktu selesai",
        ]),
        ("pesangon", "UU-13-2003:156", [
            "UU 13 Tahun 2003 Pasal 156 uang pesangon",
            "PP 35 Tahun 2021 Pasal 40 uang pesangon PHK",
        ]),
        ("lembur", "UU-13-2003:78", [
            "UU 13 Tahun 2003 Pasal 78 waktu kerja lembur",
            "PP 35 Tahun 2021 ketentuan waktu kerja lembur",
        ]),
        ("cuti melahirkan", "UU-13-2003:82", [
            "UU 13 Tahun 2003 Pasal 82 cuti melahirkan pekerja perempuan",
        ]),
        ("upah minimum", "UU-13-2003:89", [
            "UU 13 Tahun 2003 Pasal 89 upah minimum",
        ]),
        ("alih daya", "PP-35-2021:18", [
            "PP 35 Tahun 2021 Pasal 18 alih daya outsourcing",
        ]),
        ("pkwt", "PP-35-2021:15", [
            "PP 35 Tahun 2021 Pasal 15 uang kompensasi PKWT",
        ]),
    ]

    def plan(self, query: str) -> QueryPlan:
        if not is_in_scope(query):
            return QueryPlan(False, [], [], "Di luar domain ketenagakerjaan Indonesia.")
        normalized = query.lower()
        hints, expanded = [], []
        for trigger, hint, subqueries in self.RULES:
            if trigger in normalized:
                hints.append(hint)
                expanded.extend(subqueries)
        # Selalu pertahankan pertanyaan asli sebagai fallback semantic retrieval.
        subqueries = [query] + expanded
        unique = []
        for item in subqueries:
            if item not in unique:
                unique.append(item)
        return QueryPlan(True, unique[:3], hints, "Ontology ketenagakerjaan deterministic.")


class PlannedRetriever:
    """Bounded agent-tool loop: planner -> max N retrieval -> merge hints/results."""
    def __init__(self, retriever, planner, max_subqueries: int = 3):
        self.retriever = retriever
        self.planner = planner
        self.max_subqueries = max_subqueries
        self.chunks = retriever.chunks

    def search(self, query: str, top_k: int = 5) -> List[SearchHit]:
        plan = self.planner.plan(query)
        self.last_plan = plan
        if not plan.in_scope:
            return []
        merged = {}
        # Article hint diberi prioritas, tetapi hasil normal tetap digabung.
        for hint in plan.article_hints:
            doc_id, article = hint.split(":", 1)
            for chunk in self.chunks:
                if chunk.document_id == doc_id and chunk.article == article:
                    key = f"{doc_id}:{article}"
                    merged[key] = SearchHit(chunk=chunk, score=1.0, dense_score=0.0)
                    break
        for subquery in plan.subqueries[:self.max_subqueries]:
            for hit in self.retriever.search(subquery, top_k=top_k):
                key = f"{hit.chunk.document_id}:{hit.chunk.article}"
                if key not in merged:
                    merged[key] = hit
        return sorted(merged.values(), key=lambda h: h.score, reverse=True)[:top_k]


class CitationVerifier:
    def __init__(self, chunks: List[ArticleChunk]):
        self.corpus_map = {(c.document_id, c.article): c.text for c in chunks}

    def verify(self, citation: Citation) -> VerificationResult:
        key = (citation.document_id, citation.article)
        if key not in self.corpus_map:
            return VerificationResult(citation, valid=False, reason="Pasal tidak ditemukan di dalam korpus")
        content = self.corpus_map[key].lower()
        if citation.quote.lower() not in content:
            # cek partial coverage bila kutipan kurang persis
            quote_tokens = set(citation.quote.lower().split())
            content_tokens = set(content.split())
            overlap = len(quote_tokens.intersection(content_tokens)) / max(len(quote_tokens), 1)
            if overlap < 0.6:
                return VerificationResult(citation, valid=False, reason="Kutipan tidak sesuai dengan isi pasal")
        return VerificationResult(citation, valid=True, reason="Pasal dan kutipan terverifikasi akurat")


@dataclass
class SynthesizedAnswer:
    answer: str
    citations: List[Citation]
    assumptions: List[str]
    confidence: str
    refused: bool = False
    verification_results: List[VerificationResult] = field(default_factory=list)


def verify_synthesized_answer(answer: SynthesizedAnswer, verifier: CitationVerifier) -> SynthesizedAnswer:
    results = [verifier.verify(citation) for citation in answer.citations]
    valid_citations = [result.citation for result in results if result.valid]
    if not valid_citations:
        return SynthesizedAnswer(
            answer="Tidak ditemukan dasar hukum yang cukup jelas dan terverifikasi untuk menjawab pertanyaan ini. Konsultasikan dengan ahli hukum atau instansi ketenagakerjaan resmi.",
            citations=[], assumptions=answer.assumptions, confidence="rendah",
            refused=True, verification_results=results,
        )
    return SynthesizedAnswer(
        answer=answer.answer, citations=valid_citations, assumptions=answer.assumptions,
        confidence=answer.confidence, refused=False, verification_results=results,
    )


@dataclass
class EvaluationCase:
    question: str
    expected_document: Optional[str]
    expected_article: Optional[str]
    should_refuse: bool
    expected_current_document: Optional[str] = None
    expected_current_article: Optional[str] = None


@dataclass
class EvaluationResult:
    question: str
    retrieval_hit: bool
    citation_valid: bool
    cited_document: Optional[str]
    cited_article: Optional[str]
    refused: bool
    faithful: bool


def compute_evaluation_metrics(cases: List[EvaluationCase], results: List[EvaluationResult]) -> Dict[str, float]:
    if len(cases) != len(results):
        raise ValueError("cases dan results harus punya panjang yang sama")
    answerable = [(case, result) for case, result in zip(cases, results) if not case.should_refuse]
    refusals = [(case, result) for case, result in zip(cases, results) if case.should_refuse]

    def ratio(items, predicate):
        return sum(bool(predicate(*item)) for item in items) / len(items) if items else 1.0

    return {
        "retrieval_hit_at_5": ratio(answerable, lambda _c, r: r.retrieval_hit),
        "citation_accuracy": ratio(answerable, lambda _c, r: r.citation_valid),
        "version_accuracy": ratio(answerable, lambda c, r: (
            True if not c.expected_current_document else
            (r.cited_document == c.expected_current_document and r.cited_article == c.expected_current_article)
        )),
        "refusal_accuracy": ratio(refusals, lambda _c, r: r.refused),
        "faithfulness_proxy": ratio(answerable, lambda _c, r: r.faithful),
    }


def is_in_scope(query: str) -> bool:
    keywords = [
        "pesangon", "phk", "pekerja", "karyawan", "upah", "gaji",
        "pkwt", "pkwtt", "alih daya", "outsourcing", "cuti", "lembur",
        "tenaga kerja", "ketenagakerjaan", "perjanjian kerja",
    ]
    q_lower = query.lower()
    return any(k in q_lower for k in keywords)


def build_verified_answer(
    text: str,
    citations: List[Citation],
    verification_results: List[VerificationResult],
) -> VerifiedAnswer:
    valid_results = [v for v in verification_results if v.valid]
    if not citations or not valid_results:
        return VerifiedAnswer(
            answer="Tidak ditemukan dasar hukum yang cukup jelas dan terverifikasi untuk menjawab pertanyaan ini. Konsultasikan dengan ahli hukum atau instansi ketenagakerjaan resmi.",
            citations=[],
            verification_results=verification_results,
            refused=True,
        )
    return VerifiedAnswer(
        answer=text,
        citations=[v.citation for v in valid_results],
        verification_results=verification_results,
        refused=False,
    )
