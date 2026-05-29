"""
工具调用模型
"""
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolType(str, Enum):
    """工具类型"""
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
    """工具调用模型"""
    model_config = ConfigDict(use_enum_values=True)

    call_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str
    tool_type: ToolType = ToolType.CUSTOM
    input_summary: str | None = None  # sanitized summary of input
    output_summary: str | None = None  # sanitized summary of output
    input_tokens: int = 0  # tokens consumed by tool input
    output_tokens: int = 0  # tokens produced by tool output
    latency_ms: float = 0.0
    success: bool = True
    error_type: str | None = None
    error_message: str | None = None
    retry_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
