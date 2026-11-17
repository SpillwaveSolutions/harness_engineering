"""Ask for an answer that cites the retrieved chunks."""

from __future__ import annotations

import os
import sys

import anthropic


def query_with_citations(
    query: str,
    retrieved_chunks: list[dict],
) -> dict:
    """Call the model with citations enabled, or return an offline map."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ANTHROPIC_API_KEY unset; returning offline citations",
            file=sys.stderr,
        )
        citations = [
            {
                "cited_text": chunk["content"],
                "document_title": chunk["title"],
                "document_index": index,
            }
            for index, chunk in enumerate(retrieved_chunks)
        ]
        return {"answer": query, "citations": citations}

    client = anthropic.Anthropic()
    sources = [
        {
            "type": "document",
            "title": chunk["title"],
            "content": [{"type": "text", "text": chunk["content"]}],
            "citations": {"enabled": True},
        }
        for chunk in retrieved_chunks
    ]
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": sources + [{"type": "text", "text": query}],
            }
        ],
    )
    citations = []
    for block in response.content:
        if hasattr(block, "citations"):
            for citation in block.citations:
                citations.append(
                    {
                        "cited_text": citation.cited_text,
                        "document_title": citation.document_title,
                        "document_index": citation.document_index,
                    }
                )
    return {"answer": response.content[0].text, "citations": citations}


def main() -> None:
    result = query_with_citations(
        "growth?",
        [{"title": "ACME", "content": "Revenue grew."}],
    )
    print(result["answer"])
    print(result["citations"][0]["document_title"])


if __name__ == "__main__":
    main()
