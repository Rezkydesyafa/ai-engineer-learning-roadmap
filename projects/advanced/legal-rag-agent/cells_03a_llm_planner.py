"""Sel 3a: LLM planner structured output + provider registry."""
CELLS = [
("md", """
## 5. LLM Query Planner Terstruktur (Opsional)

M2 menambahkan planner LLM yang tugasnya **hanya menyusun rencana retrieval**, bukan menjawab hukum. Output dipaksa mengikuti schema Pydantic:

- `in_scope`: apakah pertanyaan termasuk ketenagakerjaan;
- `subqueries`: maksimal tiga query pencarian;
- `article_hints`: referensi kandidat seperti `UU-13-2003:156`;
- `rationale`: alasan singkat dan dapat diaudit.

Jika provider gagal, output invalid, atau key tidak tersedia, sistem otomatis kembali ke `HeuristicLegalPlanner`. Jadi jalur retrieval tidak pernah tergantung mutlak pada LLM.
"""),
("code", """
from pydantic import BaseModel, Field
from typing import List
from lexid.core import QueryPlan, HeuristicLegalPlanner

class QueryPlanOutput(BaseModel):
    in_scope: bool
    subqueries: List[str] = Field(default_factory=list, max_length=3)
    article_hints: List[str] = Field(default_factory=list, max_length=5)
    rationale: str

PROVIDERS = {
    "groq": ("https://api.groq.com/openai/v1", "llama-3.3-70b-versatile", "GROQ_API_KEY"),
    "cerebras": ("https://api.cerebras.ai/v1", "llama-3.3-70b", "CEREBRAS_API_KEY"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/", "gemini-2.0-flash", "GEMINI_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1", "meta-llama/llama-3.3-70b-instruct:free", "OPENROUTER_API_KEY"),
    "router": ("https://router.unitrade.web.id/v1", "hermes-claude", "ROUTER_API_KEY"),
    "custom": (os.getenv("OPENAI_BASE_URL", ""), os.getenv("LEXID_MODEL", "gpt-4o-mini"), "OPENAI_API_KEY"),
}
PROVIDER = os.getenv("LEXID_PROVIDER", "custom").lower()
if PROVIDER not in PROVIDERS:
    raise ValueError(f"Provider tak dikenal: {PROVIDER}")
PROVIDER_BASE_URL, PROVIDER_MODEL, PROVIDER_KEY_ENV = PROVIDERS[PROVIDER]
PROVIDER_BASE_URL = os.getenv("OPENAI_BASE_URL") or PROVIDER_BASE_URL or None
PROVIDER_MODEL = os.getenv("LEXID_MODEL", PROVIDER_MODEL)
PROVIDER_KEY = os.getenv(PROVIDER_KEY_ENV) or os.getenv("OPENAI_API_KEY")
print(f"Planner provider: {PROVIDER} | model: {PROVIDER_MODEL} | enabled: {bool(PROVIDER_KEY)}")
""", "det"),
("code", """
class LLMLegalPlanner:
    SYSTEM = '''Anda adalah query planner untuk korpus hukum ketenagakerjaan Indonesia.
Jangan menjawab pertanyaan. Pecah menjadi maksimal 3 query retrieval yang presisi.
Gunakan hanya referensi dokumen: UU-13-2003, UU-6-2023, PP-35-2021.
article_hints harus berbentuk DOKUMEN:PASAL bila yakin; jangan mengarang nomor pasal.
Pertanyaan di luar ketenagakerjaan: in_scope=false.'''

    def __init__(self, client, model, fallback=None):
        self.client = client
        self.model = model
        self.fallback = fallback or HeuristicLegalPlanner()

    def plan(self, query: str) -> QueryPlan:
        if not self.client:
            return self.fallback.plan(query)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": self.SYSTEM + "\\nSchema JSON: " + json.dumps(QueryPlanOutput.model_json_schema())},
                    {"role": "user", "content": query},
                ],
            )
            parsed = QueryPlanOutput.model_validate_json(response.choices[0].message.content)
            return QueryPlan(parsed.in_scope, parsed.subqueries[:3], parsed.article_hints, parsed.rationale)
        except Exception as exc:
            print(f"LLM planner gagal; fallback deterministic: {type(exc).__name__}")
            return self.fallback.plan(query)

llm_planner_client = None
if PROVIDER_KEY:
    from openai import OpenAI
    kwargs = {"api_key": PROVIDER_KEY}
    if PROVIDER_BASE_URL:
        kwargs["base_url"] = PROVIDER_BASE_URL
    llm_planner_client = OpenAI(**kwargs)

planner = LLMLegalPlanner(llm_planner_client, PROVIDER_MODEL)
sample_plan = planner.plan("kapan perjanjian kerja berakhir?")
print(json.dumps(asdict(sample_plan), indent=2, ensure_ascii=False))
""", "det"),
]
