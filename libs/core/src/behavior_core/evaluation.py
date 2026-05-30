"""
LLM评估框架 - 支持LLM-as-Judge评估
"""
import json
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(UTC)


class EvalMetric(str, Enum):
    """评估指标"""
    RELEVANCE = "relevance"
    HALLUCINATION = "hallucination"
    TOXICITY = "toxicity"
    COHERENCE = "coherence"
    FLUENCY = "fluency"
    FAITHFULNESS = "faithfulness"
    CORRECTNESS = "correctness"
    COMPLETENESS = "completeness"
    SAFETY = "safety"
    COST_EFFICIENCY = "cost_efficiency"


class EvalResult(BaseModel):
    """评估结果"""
    metric: EvalMetric
    score: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    evaluated_at: datetime = Field(default_factory=_utc_now)


class EvalCase(BaseModel):
    """评估用例"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    input_text: str
    output_text: str
    context: str | None = None
    expected_output: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvalDataset(BaseModel):
    """评估数据集"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    name: str
    description: str = ""
    cases: list[EvalCase] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utc_now)

    def add_case(self, case: EvalCase) -> None:
        self.cases.append(case)

    def __len__(self) -> int:
        return len(self.cases)


class EvalExperiment(BaseModel):
    """评估实验"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    name: str
    dataset_id: str
    metrics: list[EvalMetric]
    results: dict[str, list[EvalResult]] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=_utc_now)
    completed_at: datetime | None = None

    @property
    def is_complete(self) -> bool:
        return self.completed_at is not None

    def get_average_score(self, metric: EvalMetric) -> float:
        """获取指标平均分"""
        scores = []
        for case_results in self.results.values():
            for result in case_results:
                if result.metric == metric:
                    scores.append(result.score)
        return sum(scores) / len(scores) if scores else 0.0


class LLMEvaluator:
    """LLM评估器 - 使用LLM-as-Judge"""

    def __init__(self, model_name: str = "gpt-4"):
        self.model_name = model_name
        self._evaluators: dict[EvalMetric, Callable] = {}
        self._register_default_evaluators()

    def _register_default_evaluators(self) -> None:
        """注册默认评估器"""
        self._evaluators[EvalMetric.RELEVANCE] = self._eval_relevance
        self._evaluators[EvalMetric.HALLUCINATION] = self._eval_hallucination
        self._evaluators[EvalMetric.TOXICITY] = self._eval_toxicity
        self._evaluators[EvalMetric.COHERENCE] = self._eval_coherence
        self._evaluators[EvalMetric.FAITHFULNESS] = self._eval_faithfulness

    def register_evaluator(
        self,
        metric: EvalMetric,
        evaluator: Callable[[EvalCase], EvalResult],
    ) -> None:
        """注册自定义评估器"""
        self._evaluators[metric] = evaluator

    async def evaluate_case(
        self,
        case: EvalCase,
        metrics: list[EvalMetric],
    ) -> list[EvalResult]:
        """评估单个用例"""
        results = []
        for metric in metrics:
            evaluator = self._evaluators.get(metric)
            if evaluator:
                result = evaluator(case)
                results.append(result)
        return results

    async def evaluate_dataset(
        self,
        dataset: EvalDataset,
        metrics: list[EvalMetric],
    ) -> EvalExperiment:
        """评估整个数据集"""
        experiment = EvalExperiment(
            name=f"eval-{dataset.name}-{_utc_now().strftime('%Y%m%d%H%M%S')}",
            dataset_id=dataset.id,
            metrics=metrics,
        )

        for case in dataset.cases:
            results = await self.evaluate_case(case, metrics)
            experiment.results[case.id] = results

        experiment.completed_at = _utc_now()
        return experiment

    def _eval_relevance(self, case: EvalCase) -> EvalResult:
        """评估相关性"""
        # Simple keyword overlap as placeholder
        input_words = set(case.input_text.lower().split())
        output_words = set(case.output_text.lower().split())
        overlap = len(input_words & output_words)
        score = min(1.0, overlap / max(len(input_words), 1))

        return EvalResult(
            metric=EvalMetric.RELEVANCE,
            score=score,
            reasoning=f"Keyword overlap: {overlap}/{len(input_words)}",
        )

    def _eval_hallucination(self, case: EvalCase) -> EvalResult:
        """评估幻觉"""
        if not case.context:
            return EvalResult(
                metric=EvalMetric.HALLUCINATION,
                score=1.0,
                reasoning="No context provided, cannot evaluate hallucination",
            )

        context_words = set(case.context.lower().split())
        output_words = set(case.output_text.lower().split())
        overlap = len(context_words & output_words)
        score = min(1.0, overlap / max(len(output_words), 1))

        return EvalResult(
            metric=EvalMetric.HALLUCINATION,
            score=score,
            reasoning=f"Output grounded in context: {overlap}/{len(output_words)} words",
        )

    def _eval_toxicity(self, case: EvalCase) -> EvalResult:
        """评估毒性"""
        toxic_words = {"hate", "kill", "die", "stupid", "idiot", "racist", "sexist"}
        output_words = set(case.output_text.lower().split())
        toxic_count = len(output_words & toxic_words)
        score = max(0.0, 1.0 - (toxic_count * 0.2))

        return EvalResult(
            metric=EvalMetric.TOXICITY,
            score=score,
            reasoning=f"Found {toxic_count} potentially toxic words",
        )

    def _eval_coherence(self, case: EvalCase) -> EvalResult:
        """评估连贯性"""
        sentences = case.output_text.split(".")
        avg_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        score = min(1.0, avg_length / 20)  # Ideal: 10-20 words per sentence

        return EvalResult(
            metric=EvalMetric.COHERENCE,
            score=score,
            reasoning=f"Average sentence length: {avg_length:.1f} words",
        )

    def _eval_faithfulness(self, case: EvalCase) -> EvalResult:
        """评估忠实性"""
        if not case.expected_output:
            return EvalResult(
                metric=EvalMetric.FAITHFULNESS,
                score=1.0,
                reasoning="No expected output provided",
            )

        expected_words = set(case.expected_output.lower().split())
        actual_words = set(case.output_text.lower().split())
        overlap = len(expected_words & actual_words)
        score = overlap / max(len(expected_words), 1)

        return EvalResult(
            metric=EvalMetric.FAITHFULNESS,
            score=score,
            reasoning=f"Overlap with expected: {overlap}/{len(expected_words)} words",
        )


class CostEfficiencyEvaluator:
    """成本效率评估器"""

    def evaluate(
        self,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        quality_score: float,
    ) -> EvalResult:
        """评估成本效率"""
        # Cost per quality point
        if quality_score > 0:
            cost_per_quality = cost_usd / quality_score
        else:
            cost_per_quality = float("inf")

        # Score: lower cost per quality = higher score
        # Assume $0.01 per quality point is excellent
        score = max(0.0, 1.0 - (cost_per_quality / 0.01))

        return EvalResult(
            metric=EvalMetric.COST_EFFICIENCY,
            score=min(1.0, score),
            reasoning=f"Cost per quality point: ${cost_per_quality:.4f}",
            details={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost_usd,
                "quality_score": quality_score,
                "cost_per_quality": cost_per_quality,
            },
        )
