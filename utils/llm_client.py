from ollama import chat


def ask_llm(prompt: str, model: str) -> str:
    """
    Send a prompt to an Ollama model and return the response text.

    Args:
        prompt: Prompt/question to send to the model.
        model: Ollama model name to use.

    Returns:
        Model response as a string.
    """

    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    if not model or not model.strip():
        raise ValueError("Model name cannot be empty.")

    try:
        response = chat(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return response.message.content.strip()

    except Exception as error:
        raise RuntimeError(
            f"Failed to get response from model '{model}': {error}"
        ) from error