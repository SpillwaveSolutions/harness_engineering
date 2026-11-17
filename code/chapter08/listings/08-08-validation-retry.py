"""Retry a prompt when a validator rejects the model output."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

MAX_RETRIES = 3
PRIMARY_MODEL = "claude-sonnet-4-6"
FALLBACK_MODEL = "claude-haiku-4-5"


async def _last_output(client: ClaudeSDKClient, prompt: str) -> object:
    await client.query(prompt)
    last: object = ""
    async for message in client.receive_response():
        if hasattr(message, "output"):
            last = message.output
        elif hasattr(message, "result"):
            last = message.result
    return last


async def run_with_validation_retry(
    client: ClaudeSDKClient,
    prompt: str,
    validator: Callable[[object], object],
    model: str = PRIMARY_MODEL,
    is_fallback: bool = False,
) -> object:
    last_output: object = None
    last_error: str | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        if last_error:
            correction = (
                f"Correction feedback (Attempt {attempt}/{MAX_RETRIES}): "
                f"Your previous output failed validation with: {last_error}. "
                "Review the requirements and produce a corrected output."
            )
            current_prompt = f"{prompt}\n\n{correction}"
        else:
            current_prompt = prompt

        options = ClaudeAgentOptions(model=model)
        client.options = options
        result_output = await _last_output(client, current_prompt)
        try:
            return validator(result_output)
        except ValueError as exc:
            last_output = result_output
            last_error = str(exc)

    if not is_fallback:
        return await run_with_validation_retry(
            client,
            prompt,
            validator,
            model=FALLBACK_MODEL,
            is_fallback=True,
        )

    raise RuntimeError(
        f"Validation failed after {MAX_RETRIES} retries on both "
        f"{PRIMARY_MODEL} and {FALLBACK_MODEL}. "
        f"Last error: {last_error}. Last output: {last_output}"
    )


def main() -> None:
    class _Msg:
        def __init__(self, output: str) -> None:
            self.output = output

    class _Client:
        def __init__(self) -> None:
            self.prompt = ""

        async def query(
            self, prompt: str, session_id: str = "default"
        ) -> None:
            self.prompt = prompt

        async def receive_response(self) -> Awaitable:
            if "failed validation" in self.prompt:
                yield _Msg("accepted")
            else:
                yield _Msg("rejected")

    def validator(text: object) -> dict:
        if text != "accepted":
            raise ValueError("not accepted")
        return {"status": "accepted"}

    result = asyncio.run(
        run_with_validation_retry(_Client(), "book AA100", validator)
    )
    print(result["status"])


if __name__ == "__main__":
    main()
