import openai
from dotenv import load_dotenv
from openai import Completion
import os

MODEL_ENGINE = "gpt-3.5-turbo"
MAX_TOKENS = 500
TEMPERATURE = 0.01

load_dotenv()

openai.api_key = os.environ.get("OPENAI_KEY")


def call_model_endpoint(prompt: str, max_tokens: int = 500):
    try:
        completion: Completion = openai.ChatCompletion.create(
            model=MODEL_ENGINE,
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
