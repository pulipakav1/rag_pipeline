import json
from dataclasses import dataclass, field

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger

from config.settings import settings


FAITHFULNESS_PROMPT = """You are an evaluation judge. Your job is to determine whether an AI-generated answer is faithful to the provided context (i.e., does not hallucinate).

Context:
{context}

Answer:
{answer}

Evaluate faithfulness strictly: Is every claim in the answer directly supported by the context? Score 1.0 if fully grounded, 0.0 if completely hallucinated, fractional scores for partial grounding.

Respond ONLY with valid JSON in this exact format:
{{"score": <float 0.0-1.0>, "reasoning": "<one sentence explanation>", "hallucinated_claims": [<list any claims not in context, or empty list>]}}"""


RELEVANCE_PROMPT = """You are an evaluation judge. Your job is to determine whether an AI-generated answer actually addresses the question asked.

Question:
{question}

Answer:
{answer}

Score 1.0 if the answer directly and completely addresses the question. Score 0.0 if it is completely off-topic. Use fractional scores for partial relevance.

Respond ONLY with valid JSON in this exact format:
{{"score": <float 0.0-1.0>, "reasoning": "<one sentence explanation>"}}"""


RETRIEVAL_PRECISION_PROMPT = """You are an evaluation judge. Your job is to determine whether the retrieved context chunks are relevant to the question.

Question:
{question}

Retrieved Context:
{context}

For each chunk, is it relevant to answering the question? Score 1.0 if all chunks are highly relevant, 0.0 if none are relevant.

Respond ONLY with valid JSON in this exact format:
{{"score": <float 0.0-1.0>, "reasoning": "<one sentence explanation>", "relevant_chunks": <int count of relevant chunks>, "total_chunks": <int total chunks>}}"""


@dataclass
class MetricScore:
    name: str
    score: float
    reasoning: str
    details: dict = field(default_factory=dict)


@dataclass
class EvaluationResult:
    question: str
    answer: str
    context: str
    faithfulness: MetricScore
    relevance: MetricScore
    retrieval_precision: MetricScore
    overall_score: float = 0.0

    def __post_init__(self):
        self.overall_score = round(
            (self.faithfulness.score + self.relevance.score + self.retrieval_precision.score) / 3,
            3,
        )

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "answer": self.answer,
            "overall_score": self.overall_score,
            "metrics": {
                "faithfulness": {
                    "score": self.faithfulness.score,
                    "reasoning": self.faithfulness.reasoning,
                    "details": self.faithfulness.details,
                },
                "relevance": {
                    "score": self.relevance.score,
                    "reasoning": self.relevance.reasoning,
                },
                "retrieval_precision": {
                    "score": self.retrieval_precision.score,
                    "reasoning": self.retrieval_precision.reasoning,
                    "details": self.retrieval_precision.details,
                },
            },
        }


@dataclass
class EvaluationSummary:
    total_questions: int
    avg_faithfulness: float
    avg_relevance: float
    avg_retrieval_precision: float
    avg_overall: float
    results: list[EvaluationResult]

    def to_dict(self) -> dict:
        return {
            "summary": {
                "total_questions": self.total_questions,
                "avg_faithfulness": round(self.avg_faithfulness, 3),
                "avg_relevance": round(self.avg_relevance, 3),
                "avg_retrieval_precision": round(self.avg_retrieval_precision, 3),
                "avg_overall_score": round(self.avg_overall, 3),
            },
            "results": [r.to_dict() for r in self.results],
        }


class RAGEvaluator:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.model_name

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    def _judge(self, prompt: str) -> dict:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())

    def evaluate_faithfulness(self, answer: str, context: str) -> MetricScore:
        prompt = FAITHFULNESS_PROMPT.format(context=context, answer=answer)
        try:
            result = self._judge(prompt)
            return MetricScore(
                name="faithfulness",
                score=float(result["score"]),
                reasoning=result["reasoning"],
                details={"hallucinated_claims": result.get("hallucinated_claims", [])},
            )
        except Exception as e:
            logger.error(f"Faithfulness eval failed: {e}")
            return MetricScore(name="faithfulness", score=0.0, reasoning=f"Eval error: {e}")

    def evaluate_relevance(self, question: str, answer: str) -> MetricScore:
        prompt = RELEVANCE_PROMPT.format(question=question, answer=answer)
        try:
            result = self._judge(prompt)
            return MetricScore(
                name="relevance",
                score=float(result["score"]),
                reasoning=result["reasoning"],
            )
        except Exception as e:
            logger.error(f"Relevance eval failed: {e}")
            return MetricScore(name="relevance", score=0.0, reasoning=f"Eval error: {e}")

    def evaluate_retrieval_precision(self, question: str, context: str) -> MetricScore:
        prompt = RETRIEVAL_PRECISION_PROMPT.format(question=question, context=context)
        try:
            result = self._judge(prompt)
            return MetricScore(
                name="retrieval_precision",
                score=float(result["score"]),
                reasoning=result["reasoning"],
                details={
                    "relevant_chunks": result.get("relevant_chunks", 0),
                    "total_chunks": result.get("total_chunks", 0),
                },
            )
        except Exception as e:
            logger.error(f"Retrieval precision eval failed: {e}")
            return MetricScore(name="retrieval_precision", score=0.0, reasoning=f"Eval error: {e}")

    def evaluate(self, question: str, answer: str, context: str) -> EvaluationResult:
        logger.info(f"Evaluating: '{question[:60]}...'")

        faithfulness = self.evaluate_faithfulness(answer=answer, context=context)
        relevance = self.evaluate_relevance(question=question, answer=answer)
        retrieval_precision = self.evaluate_retrieval_precision(question=question, context=context)

        result = EvaluationResult(
            question=question,
            answer=answer,
            context=context,
            faithfulness=faithfulness,
            relevance=relevance,
            retrieval_precision=retrieval_precision,
        )

        logger.info(
            f"Scores | Faithfulness: {faithfulness.score:.2f} | "
            f"Relevance: {relevance.score:.2f} | "
            f"Retrieval Precision: {retrieval_precision.score:.2f} | "
            f"Overall: {result.overall_score:.2f}"
        )
        return result

    def evaluate_batch(self, test_cases: list[dict]) -> EvaluationSummary:
        results = []
        for i, case in enumerate(test_cases):
            logger.info(f"Evaluating case {i+1}/{len(test_cases)}")
            result = self.evaluate(
                question=case["question"],
                answer=case["answer"],
                context=case["context"],
            )
            results.append(result)

        summary = EvaluationSummary(
            total_questions=len(results),
            avg_faithfulness=sum(r.faithfulness.score for r in results) / len(results),
            avg_relevance=sum(r.relevance.score for r in results) / len(results),
            avg_retrieval_precision=sum(r.retrieval_precision.score for r in results) / len(results),
            avg_overall=sum(r.overall_score for r in results) / len(results),
            results=results,
        )
        return summary
