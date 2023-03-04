import openai
from openai import Completion

MODEL_ENGINE = "gpt-3.5-turbo"
MAX_TOKENS = 500
TEMPERATURE = 0.01


def call_model_endpoint(prompt: str):
    try:
        completion: Completion = openai.ChatCompletion.create(
            model=MODEL_ENGINE,
            messages=[{"role": "user", "content": prompt}],
            n=1,
            max_tokens=MAX_TOKENS,
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
