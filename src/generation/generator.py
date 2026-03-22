from dataclasses import dataclass
from typing import Optional

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger

from config.settings import settings


RAG_SYSTEM_PROMPT = """You are a precise, grounded question-answering assistant.

Your rules:
1. Answer ONLY based on the provided context. Do not use prior knowledge.
2. If the context is empty, says there is no relevant context, or is clearly unrelated to the question, say exactly: "I don't have enough information in the provided context to answer this." Otherwise you MUST answer from the context—even if the question asks for a "definition" or "comprehensive" answer and the context only gives partial or indirect information. Summarize what the context does say; do not open with a refusal and then contradict it with a long answer.
3. If the context is relevant but incomplete (e.g. no formal definition), answer with what is stated and add a brief closing note such as "The excerpts do not give a full textbook definition, but they characterize …"—not a blanket "I don't have enough information" up front.
4. Always cite which source(s) you used in your answer.
5. Be concise and direct. No padding.
6. If the question is ambiguous, answer the most reasonable interpretation."""

RAG_USER_PROMPT_TEMPLATE = """Context:
{context}

---

Question: {question}

Answer (based strictly on the context above):"""


@dataclass
class GenerationResult:
    answer: str
    question: str
    context_used: str
    model: str
    input_tokens: int
    output_tokens: int


class Generator:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.model_name

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def generate(self, question: str, context: str) -> GenerationResult:
        prompt = RAG_USER_PROMPT_TEMPLATE.format(
            context=context,
            question=question,
        )

        logger.debug(f"Sending to Claude | model: {self.model}")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            system=RAG_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        answer = response.content[0].text

        result = GenerationResult(
            answer=answer,
            question=question,
            context_used=context,
            model=self.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

        logger.info(
            f"Generated answer | "
            f"tokens in: {result.input_tokens} | out: {result.output_tokens}"
        )
        return result
