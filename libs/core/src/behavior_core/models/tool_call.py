"""
Tool call model — records individual tool invocations by AI agents.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ToolType(str, Enum):
    """Classification of tool types available to AI agents."""

    API = "api"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    CODE_EXECUTION = "code_execution"
    NETWORK = "network"
    SEARCH = "search"
    CALCULATION = "calculation"
    VISUALIZATION = "visualization"
    CUSTOM = "custom"


class ToolCall(BaseModel):
    """Tool call model — records input, output, latency, and success/failure of a tool invocation."""

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    call_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        min_length=1,
        max_length=128,
        description="Unique identifier for this tool call (auto-generated UUID)",
    )
    tool_name: str = Field(
        ..., min_length=1, max_length=256, description="Name of the tool being invoked"
    )
    tool_type: ToolType = Field(
        default=ToolType.CUSTOM, description="Classification of the tool"
    )
    input_summary: str | None = Field(
        default=None, max_length=4096, description="Sanitized summary of tool input"
    )
    output_summary: str | None = Field(
        default=None, max_length=4096, description="Sanitized summary of tool output"
    )
    input_tokens: int = Field(
        default=0, ge=0, description="Number of tokens consumed by the tool input"
    )
    output_tokens: int = Field(
        default=0, ge=0, description="Number of tokens produced by the tool output"
    )
    latency_ms: float = Field(
        default=0.0, ge=0, description="Execution latency in milliseconds (non-negative)"
    )
    success: bool = Field(
        default=True, description="Whether the tool call succeeded"
    )
    error_type: str | None = Field(
        default=None, max_length=256, description="Error classification on failure"
    )
    error_message: str | None = Field(
        default=None, max_length=4096, description="Human-readable error description"
    )
    retry_count: int = Field(
        default=0, ge=0, description="Number of retry attempts for this call"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary key-value metadata for the call"
    )

    @field_validator("tool_name")
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        """Ensure tool_name is not blank after stripping whitespace."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("tool_name must not be blank or whitespace-only")
        return stripped

    @field_validator("error_type", "error_message")
    @classmethod
    def normalize_error_fields(cls, v: str | None) -> str | None:
        """Convert empty strings to None for error fields."""
        if v is not None and not v.strip():
            return None
        return v

    @field_validator("input_summary", "output_summary")
    @classmethod
    def normalize_summary_fields(cls, v: str | None) -> str | None:
        """Convert empty strings to None for summary fields."""
        if v is not None and not v.strip():
            return None
        return v

    @model_validator(mode="after")
    def validate_error_consistency(self) -> "ToolCall":
        """Ensure error fields are consistent with success status."""
        if not self.success:
            if not self.error_type and not self.error_message:
                raise ValueError(
                    "When success is False, at least one of error_type or error_message "
                    "must be provided to describe the failure"
                )
        if self.error_message and not self.error_type:
            raise ValueError(
                "error_type must be provided when error_message is set; "
                "an error message without a classification is ambiguous"
            )
        return self
