from pathlib import Path


DATA_FILE = Path("data/solides_jobs.json")
PAGE_SIZE_OPTIONS = [4, 6, 8, 10, 12]
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BRAND_NAME = "SaborJob"
ADHERENCE_TOOLTIP = "Percentual estimado de compatibilidade entre a vaga e seu curriculo."
FLAVOR_TOOLTIP = "Leitura rapida do potencial da vaga. Quanto mais sabor, mais faz sentido olhar com atencao."
PROFILE_KEYWORDS = [
    "python",
    "django",
    "flask",
    "fastapi",
    "java",
    "spring",
    "javascript",
    "typescript",
    "node",
    "react",
    "next.js",
    "next",
    "angular",
    "vue",
    "php",
    "laravel",
    "c#",
    ".net",
    "dotnet",
    "golang",
    "go",
    "ruby",
    "rails",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "graphql",
    "rest",
    "microservices",
    "api",
]
SENIORITY_PATTERNS = {
    "Junior": [r"\bjunior\b", r"\bjr\b", r"\btrainee\b", r"\bestagi[áa]rio\b"],
    "Pleno": [r"\bpleno\b", r"\bpl\b", r"\bmid\b", r"\bintermedi[áa]rio\b"],
    "Senior": [r"\bsenior\b", r"\bsr\b", r"\bespecialista\b", r"\blead\b", r"\bstaff\b"],
}
