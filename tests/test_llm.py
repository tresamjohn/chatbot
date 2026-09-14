from utils.llm_client import ask_llm

response = ask_llm(
    "What is the capital of England? Answer in one word."
)

print(response)