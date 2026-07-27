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


def is_in_scope(query: str) -> bool:
    keywords = [
        "pesangon", "phk", "pekerja", "karyawan", "upah", "gaji",
        "pkwt", "pkwtt", "alih daya", "outsourcing", "cuti", "lembur",
        "tenaga kerja", "ketenagakerjaan",
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
