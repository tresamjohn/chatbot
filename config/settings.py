from pathlib import Path

# ============================================================
# Project
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# Available Local LLM Models
# ============================================================

AVAILABLE_MODELS = {
    "qwen": "qwen3:4b-instruct-2507-q4_K_M",
    "llama": "llama3.2:3b",
    "gemma": "gemma3:4b",
}


# ============================================================
# LLM Roles
# ============================================================

# Generates questions and expected answers from the knowledge base
GENERATOR_MODEL = AVAILABLE_MODELS["qwen"]

# Chatbot/model that we are testing
TARGET_CHATBOT_MODEL = AVAILABLE_MODELS["llama"]

# Evaluates expected answer vs actual chatbot answer
EVALUATOR_MODEL = AVAILABLE_MODELS["qwen"]


# ============================================================
# Ollama
# ============================================================

OLLAMA_BASE_URL = "http://localhost:11434"

OLLAMA_CHAT_ENDPOINT = f"{OLLAMA_BASE_URL}/api/chat"


# ============================================================
# Knowledge Base
# ============================================================

KNOWLEDGE_BASE_FILE = (
    BASE_DIR
    / "knowledge_base"
    / "General_Knowledge_Base.md"
)


# ============================================================
# Data
# ============================================================

TESTCASES_FILE = (
    BASE_DIR
    / "data"
    / "testcases.json"
)

EXECUTION_RESULTS_FILE = (
    BASE_DIR
    / "data"
    / "execution_results.jsonl"
)

EVALUATED_RESULTS_FILE = (
    BASE_DIR
    / "data"
    / "evaluated_results.jsonl"
)


# ============================================================
# Reports
# ============================================================

REPORT_FILE = (
    BASE_DIR
    / "reports"
    / "report.xlsx"
)

HTML_REPORT_FILE = (
    BASE_DIR
    / "reports"
    / "report.html"
)


# ============================================================
# Test Generation
# ============================================================

DEFAULT_TESTCASE_COUNT = 10

GENERATION_BATCH_SIZE = 10

GENERATION_MAX_RETRIES = 3


# ============================================================
# Positive Test Strategies
# ============================================================

POSITIVE_STRATEGIES = [
    "direct",
    "rephrased",
    "conversational",
    "short",
    "verbose",
    "typo",
    "case_variation",
    "contextual",
]


# ============================================================
# Negative Test Strategies
# ============================================================

NEGATIVE_STRATEGIES = [
    "out_of_scope",
    "non_kb",
    "ambiguous",
    "nonsense",
    "malformed",
    "false_premise",
    "unsupported",
    "prompt_injection",
]


DEFAULT_STRATEGIES = [
    "direct",
]


CHATBOT_TIMEOUT_SECONDS = 60