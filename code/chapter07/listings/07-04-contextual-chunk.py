"""Prepend a short context sentence to a retrieved chunk."""

from __future__ import annotations

import os
import sys

import anthropic


def augment_chunk(
    raw_chunk: str,
    document_title: str,
    client: anthropic.Anthropic | None,
) -> str:
    """Prepend a contextual summary to a raw chunk before embedding."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ANTHROPIC_API_KEY unset; returning offline chunk",
            file=sys.stderr,
        )
        return f"Context from {document_title}.\n\n{raw_chunk}"
    if client is None:
        client = anthropic.Anthropic()
    prompt = (
        f"Document: {document_title}\n\n"
        f"Chunk:\n{raw_chunk}\n\n"
        "Write a one-to-two sentence context that situates this chunk "
        "within the broader document. Be specific. Do not restate the chunk."
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=120,
        messages=[{"role": "user", "content": prompt}],
    )
    context = response.content[0].text.strip()
    return f"{context}\n\n{raw_chunk}"


def main() -> None:
    text = augment_chunk(
        "Revenue grew by 3 percent.",
        "ACME Q2",
        None,
    )
    print(text)


if __name__ == "__main__":
    main()
