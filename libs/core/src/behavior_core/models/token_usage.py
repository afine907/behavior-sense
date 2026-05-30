"""
Token consumption model — tracks LLM token usage, costs, and cache efficiency.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TokenUsage(BaseModel):
    """Token consumption model with automatic cost estimation and cache metrics."""

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    prompt_tokens: int = Field(
        default=0, ge=0, description="Number of tokens in the prompt (input)"
    )
    completion_tokens: int = Field(
        default=0, ge=0, description="Number of tokens in the completion (output)"
    )
    total_tokens: int = Field(
        default=0, ge=0, description="Total tokens consumed (prompt + completion)"
    )
    cached_tokens: int = Field(
        default=0, ge=0, description="Number of prompt tokens served from cache"
    )
    model_name: str | None = Field(
        default=None,
        max_length=256,
        description="Name of the LLM model (e.g., 'gpt-4', 'claude-3-opus')",
    )
    cost_usd: float = Field(
        default=0.0, ge=0, description="Actual cost in USD for this request"
    )
    cache_hit_ratio: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Fraction of prompt tokens served from cache (0.0 to 1.0)",
    )

    @property
    def estimated_cost(self) -> float:
        """Estimate cost based on token counts if cost_usd not set."""
        if self.cost_usd > 0:
            return self.cost_usd
        # Rough estimate: $0.01 per 1K tokens for input, $0.03 per 1K for output
        return self.prompt_tokens * 0.00001 + self.completion_tokens * 0.00003

    @field_validator("model_name")
    @classmethod
    def normalize_model_name(cls, v: str | None) -> str | None:
        """Convert empty/whitespace-only strings to None."""
        if v is not None and not v.strip():
            return None
        return v

    @model_validator(mode="after")
    def compute_total_and_cache_ratio(self) -> "TokenUsage":
        """Auto-compute total_tokens and cache_hit_ratio; validate cached_tokens bounds."""
        # Use __dict__ to bypass validate_assignment and avoid recursion
        if self.total_tokens == 0:
            self.__dict__["total_tokens"] = self.prompt_tokens + self.completion_tokens
        if self.cached_tokens > self.prompt_tokens:
            raise ValueError(
                f"cached_tokens ({self.cached_tokens}) cannot exceed "
                f"prompt_tokens ({self.prompt_tokens})"
            )
        if self.prompt_tokens > 0 and self.cached_tokens > 0:
            computed_ratio = self.cached_tokens / self.prompt_tokens
            # Only update if the user did not explicitly set a non-zero value
            if self.cache_hit_ratio == 0.0:
                self.__dict__["cache_hit_ratio"] = round(computed_ratio, 4)
        return self
