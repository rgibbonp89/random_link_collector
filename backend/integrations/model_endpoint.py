from typing import Optional

import openai
from dotenv import load_dotenv
from openai import Completion
import os

MODEL_ENGINE = "gpt-3.5-turbo"
MODEL_ENGINE_LARGE = "gpt-4"
MAX_TOKENS = 500
TEMPERATURE = 0.01
MODEL_THRESHOLD = 3000
load_dotenv()

openai.api_key = os.environ.get("OPENAI_KEY")


def call_model_endpoint(
    prompt: str,
    model: Optional[str] = None,
    max_tokens: int = 500,
):
    if not model:
        model = (
            MODEL_ENGINE_LARGE
            if (len(prompt.split()) + max_tokens) > MODEL_THRESHOLD
            else MODEL_ENGINE
        )
    try:
        completion: Completion = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            n=1,
            max_tokens=max_tokens,
            temperature=TEMPERATURE,
        )
        saved_text = (
            completion.choices[0]
            .message.content.replace("• ", "* ")
            .replace("- ", "* ")
        )
    except openai.error.InvalidRequestError as exception:
        saved_text = exception.user_message
    return saved_text
