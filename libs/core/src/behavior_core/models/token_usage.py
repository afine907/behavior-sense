"""
Token消耗模型
"""
from pydantic import BaseModel, ConfigDict, model_validator


class TokenUsage(BaseModel):
    """Token消耗模型"""
    model_config = ConfigDict(use_enum_values=True)

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0  # prompt cache hits
    model_name: str | None = None  # e.g., "gpt-4", "claude-3-opus"
    cost_usd: float = 0.0
    cache_hit_ratio: float = 0.0  # 0.0-1.0

    @property
    def estimated_cost(self) -> float:
        """Estimate cost based on token counts if cost_usd not set"""
        if self.cost_usd > 0:
            return self.cost_usd
        # Rough estimate: $0.01 per 1K tokens for input, $0.03 per 1K for output
        return (self.prompt_tokens * 0.00001 + self.completion_tokens * 0.00003)

    @model_validator(mode='after')
    def compute_total(self) -> 'TokenUsage':
        if self.total_tokens == 0:
            self.total_tokens = self.prompt_tokens + self.completion_tokens
        if self.prompt_tokens > 0 and self.cached_tokens > 0:
            self.cache_hit_ratio = self.cached_tokens / self.prompt_tokens
        return self
