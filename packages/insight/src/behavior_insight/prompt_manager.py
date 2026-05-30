"""
Prompt管理系统 - 版本控制和模板管理
"""
import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(UTC)


class PromptVersion(BaseModel):
    """Prompt版本"""
    version_id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    prompt_id: str
    version: int
    content: str
    variables: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    hash: str = ""
    created_at: datetime = Field(default_factory=_utc_now)
    created_by: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.hash:
            self.hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]


class PromptTemplate(BaseModel):
    """Prompt模板"""
    prompt_id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    name: str
    description: str = ""
    content: str
    variables: list[str] = Field(default_factory=list)
    category: str = "general"
    tags: list[str] = Field(default_factory=list)

    # Version tracking
    current_version: int = 1
    versions: list[PromptVersion] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
    created_by: str = ""

    def render(self, variables: dict[str, str] | None = None) -> str:
        """渲染Prompt"""
        content = self.content
        if variables:
            for key, value in variables.items():
                content = content.replace(f"{{{{{key}}}}}", value)
        return content

    def create_version(self, content: str, created_by: str = "") -> PromptVersion:
        """创建新版本"""
        self.current_version += 1
        version = PromptVersion(
            prompt_id=self.prompt_id,
            version=self.current_version,
            content=content,
            variables=self.variables,
            created_by=created_by,
        )
        self.versions.append(version)
        self.content = content
        self.updated_at = _utc_now()
        return version

    def get_version(self, version: int) -> PromptVersion | None:
        """获取指定版本"""
        for v in self.versions:
            if v.version == version:
                return v
        return None

    def rollback(self, version: int) -> bool:
        """回滚到指定版本"""
        target = self.get_version(version)
        if target:
            self.content = target.content
            self.current_version = version
            self.updated_at = _utc_now()
            return True
        return False


class PromptManager:
    """Prompt管理器"""

    def __init__(self):
        self._prompts: dict[str, PromptTemplate] = {}
        self._categories: set[str] = {"general", "chat", "completion", "embedding", "agent"}

    def create_prompt(
        self,
        name: str,
        content: str,
        description: str = "",
        variables: list[str] | None = None,
        category: str = "general",
        tags: list[str] | None = None,
        created_by: str = "",
    ) -> PromptTemplate:
        """创建Prompt"""
        prompt = PromptTemplate(
            name=name,
            description=description,
            content=content,
            variables=variables or [],
            category=category,
            tags=tags or [],
            created_by=created_by,
        )

        # Create initial version
        prompt.versions.append(PromptVersion(
            prompt_id=prompt.prompt_id,
            version=1,
            content=content,
            variables=prompt.variables,
            created_by=created_by,
        ))

        self._prompts[prompt.prompt_id] = prompt
        return prompt

    def get_prompt(self, prompt_id: str) -> PromptTemplate | None:
        """获取Prompt"""
        return self._prompts.get(prompt_id)

    def get_prompt_by_name(self, name: str) -> PromptTemplate | None:
        """按名称获取Prompt"""
        for prompt in self._prompts.values():
            if prompt.name == name:
                return prompt
        return None

    def update_prompt(
        self,
        prompt_id: str,
        content: str,
        created_by: str = "",
    ) -> PromptVersion | None:
        """更新Prompt"""
        prompt = self._prompts.get(prompt_id)
        if not prompt:
            return None
        return prompt.create_version(content, created_by)

    def delete_prompt(self, prompt_id: str) -> bool:
        """删除Prompt"""
        if prompt_id in self._prompts:
            del self._prompts[prompt_id]
            return True
        return False

    def list_prompts(
        self,
        category: str | None = None,
        tag: str | None = None,
    ) -> list[PromptTemplate]:
        """列出Prompt"""
        prompts = list(self._prompts.values())

        if category:
            prompts = [p for p in prompts if p.category == category]

        if tag:
            prompts = [p for p in prompts if tag in p.tags]

        return prompts

    def render_prompt(
        self,
        prompt_id: str,
        variables: dict[str, str] | None = None,
    ) -> str | None:
        """渲染Prompt"""
        prompt = self._prompts.get(prompt_id)
        if not prompt:
            return None
        return prompt.render(variables)

    def get_categories(self) -> list[str]:
        """获取所有分类"""
        return sorted(self._categories)

    def add_category(self, category: str) -> None:
        """添加分类"""
        self._categories.add(category)

    def get_prompt_history(self, prompt_id: str) -> list[PromptVersion]:
        """获取Prompt版本历史"""
        prompt = self._prompts.get(prompt_id)
        if not prompt:
            return []
        return prompt.versions

    def compare_versions(
        self,
        prompt_id: str,
        version1: int,
        version2: int,
    ) -> dict[str, Any] | None:
        """比较两个版本"""
        prompt = self._prompts.get(prompt_id)
        if not prompt:
            return None

        v1 = prompt.get_version(version1)
        v2 = prompt.get_version(version2)

        if not v1 or not v2:
            return None

        return {
            "version1": {
                "version": v1.version,
                "content": v1.content,
                "hash": v1.hash,
                "created_at": v1.created_at.isoformat(),
            },
            "version2": {
                "version": v2.version,
                "content": v2.content,
                "hash": v2.hash,
                "created_at": v2.created_at.isoformat(),
            },
            "changed": v1.hash != v2.hash,
        }
