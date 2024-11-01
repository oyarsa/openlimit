from typing import Any, Union

import tiktoken

# Tokenizer
CL100K_ENCODER = tiktoken.get_encoding("cl100k_base")
P50K_ENCODER = tiktoken.get_encoding("p50k_base")


def num_tokens_consumed_by_chat_request(
    messages: list[dict[str, str]], max_tokens: int = 15, n: int = 1, **kwargs: Any
) -> int:
    num_tokens = n * max_tokens
    for message in messages:
        num_tokens += (
            4  # Every message follows <im_start>{role/name}\n{content}<im_end>\n
        )
        for key, value in message.items():
            num_tokens += len(CL100K_ENCODER.encode(value))

            if key == "name":  # If there's a name, the role is omitted
                num_tokens -= 1  # Role is always required and always 1 token

    num_tokens += 2  # Every reply is primed with <im_start>assistant

    return num_tokens


def num_tokens_consumed_by_completion_request(
    prompt: Union[str, list[str]], max_tokens: int = 15, n: int = 1, **kwargs: Any
) -> int:
    num_tokens = n * max_tokens
    if isinstance(prompt, str):  # Single prompt
        num_tokens += len(P50K_ENCODER.encode(prompt))
    else:  # Multiple prompts
        num_tokens *= len(prompt)
        num_tokens += sum(len(P50K_ENCODER.encode(p)) for p in prompt)

    return num_tokens


def num_tokens_consumed_by_embedding_request(
    input: Union[str, list[str]], **kwargs: Any
) -> int:
    if isinstance(input, str):  # Single input
        return len(P50K_ENCODER.encode(input))
    else:  # Multiple inputs
        return sum(len(P50K_ENCODER.encode(i)) for i in input)
