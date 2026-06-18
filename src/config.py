import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CONFIG_DIR = os.path.join(PROJECT_ROOT, "configs")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")

EMBEDDING_CACHE_DIR = os.path.join(OUTPUT_DIR, "embeddings")
TRACES_DIR = os.path.join(OUTPUT_DIR, "traces")
EXPERIMENTS_DIR = os.path.join(OUTPUT_DIR, "experiments")
FIGURES_DIR = os.path.join(OUTPUT_DIR, "figures")
REPORTS_DIR = os.path.join(OUTPUT_DIR, "reports")

for d in [EMBEDDING_CACHE_DIR, TRACES_DIR, EXPERIMENTS_DIR, FIGURES_DIR, REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "facebook/esm2_t6_8M_UR50D")
DEVICE = os.getenv("DEVICE", "cuda")
EXPERIMENT_RUNS = int(os.getenv("EXPERIMENT_RUNS", "5"))
CACHE_EMBEDDINGS = os.getenv("CACHE_EMBEDDINGS", "true").lower() == "true"
