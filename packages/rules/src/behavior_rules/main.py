"""
Behavior Rules 服务入口

FastAPI 应用，提供规则管理 API 和规则评估接口。
"""
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from behavior_core.config.settings import settings
from behavior_core.middleware.tracing import TraceIDMiddleware
from behavior_core.middleware.rate_limit import RateLimitMiddleware
from behavior_core.metrics import get_metrics, set_service_info
from behavior_rules.models import (
    Rule,
    RuleCreate,
    RuleUpdate,
    RuleMatchResult,
    EvaluateRequest,
    EvaluateResponse
)
from behavior_rules.engine import RuleEngine, get_rule_engine
from behavior_rules.loader import YamlRuleLoader, DbRuleLoader
from behavior_rules.actions import tag_user, trigger_audit


# 规则存储（简化实现，实际应使用数据库）
_rules_store: dict[str, Rule] = {}

# 规则加载器
_yaml_loader: YamlRuleLoader | None = None
_db_loader: DbRuleLoader | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    engine = get_rule_engine()

    # 注册动作处理器
    engine.register_action_handler("TAG_USER", tag_user)
    engine.register_action_handler("TRIGGER_AUDIT", trigger_audit)

    # 加载规则（从 YAML 文件，如果存在）
    # 实际部署时可根据配置选择加载方式
    rules_dir = "rules"
    import os
    if os.path.exists(rules_dir):
        global _yaml_loader
        _yaml_loader = YamlRuleLoader(engine, rules_dir, watch=True)
        _yaml_loader.load()
        await _yaml_loader.start_watching()

    # 存储已注册的规则
    for rule in engine.get_all_rules():
        _rules_store[rule.id] = rule

    print(f"Behavior Rules service started on port {settings.rules_port}")

    yield

    # 关闭时清理
    if _yaml_loader:
        await _yaml_loader.stop_watching()

    print("Behavior Rules service stopped")


# 创建 FastAPI 应用
app = FastAPI(
    title="Behavior Rules Service",
    description="规则引擎服务，提供规则管理和评估功能",
    version="1.0.0",
    lifespan=lifespan
)

# 设置服务信息
set_service_info("behavior-rules", "1.0.0")

# 添加 TraceID 中间件
app.add_middleware(TraceIDMiddleware)

# 添加限流中间件
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=100,
    window_seconds=60,
)

# 配置 CORS (从配置读取允许的域名)
cors_origins = settings.cors_origins.split(",") if settings.cors_origins else ["*"] if settings.debug else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 健康检查 ====================

@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, Any]:
    """
    健康检查

    Returns:
        服务状态信息
    """
    engine = get_rule_engine()
    return {
        "status": "healthy",
        "service": "behavior-rules",
        "rules_count": len(_rules_store),
        "handlers_count": len(engine._action_handlers),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/ready", tags=["Health"])
async def readiness_check() -> dict[str, Any]:
    """
    就绪检查

    Returns:
        服务就绪状态
    """
    return {
        "ready": True,
        "service": "behavior-rules"
    }


@app.get("/metrics", response_class=PlainTextResponse, tags=["Monitoring"])
async def metrics_endpoint() -> str:
    """
    Prometheus 指标端点

    Returns:
        Prometheus 格式的监控指标
    """
    return get_metrics()


# ==================== 规则管理 API ====================

@app.get("/api/rules", response_model=list[Rule], tags=["Rules"])
async def list_rules(
    enabled: bool | None = Query(None, description="按启用状态过滤"),
    tag: str | None = Query(None, description="按标签过滤"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> list[Rule]:
    """
    获取规则列表

    Args:
        enabled: 按启用状态过滤
        tag: 按标签过滤
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        规则列表
    """
    rules = list(_rules_store.values())

    # 过滤
    if enabled is not None:
        rules = [r for r in rules if r.enabled == enabled]
    if tag:
        rules = [r for r in rules if tag in r.tags]

    # 排序（按优先级降序）
    rules.sort(key=lambda r: r.priority, reverse=True)

    # 分页
    return rules[offset:offset + limit]


@app.post("/api/rules", response_model=Rule, status_code=201, tags=["Rules"])
async def create_rule(rule_create: RuleCreate) -> Rule:
    """
    创建规则

    Args:
        rule_create: 规则创建请求

    Returns:
        创建的规则
    """
    engine = get_rule_engine()

    # 创建规则对象
    rule = Rule(
        name=rule_create.name,
        description=rule_create.description,
        condition=rule_create.condition,
        priority=rule_create.priority,
        enabled=rule_create.enabled,
        actions=rule_create.actions,
        tags=rule_create.tags
    )

    # 存储并注册
    _rules_store[rule.id] = rule
    engine.register_rule(rule)

    return rule


@app.get("/api/rules/{rule_id}", response_model=Rule, tags=["Rules"])
async def get_rule(rule_id: str) -> Rule:
    """
    获取规则详情

    Args:
        rule_id: 规则ID

    Returns:
        规则详情

    Raises:
        HTTPException: 规则不存在
    """
    if rule_id not in _rules_store:
        raise HTTPException(status_code=404, detail="Rule not found")

    return _rules_store[rule_id]


@app.put("/api/rules/{rule_id}", response_model=Rule, tags=["Rules"])
async def update_rule(rule_id: str, rule_update: RuleUpdate) -> Rule:
    """
    更新规则

    Args:
        rule_id: 规则ID
        rule_update: 规则更新请求

    Returns:
        更新后的规则

    Raises:
        HTTPException: 规则不存在
    """
    if rule_id not in _rules_store:
        raise HTTPException(status_code=404, detail="Rule not found")

    engine = get_rule_engine()
    existing_rule = _rules_store[rule_id]

    # 更新字段
    update_data = rule_update.model_dump(exclude_unset=True)

    # 创建更新后的规则
    updated_rule = existing_rule.model_copy(update={
        **update_data,
        "updated_at": datetime.utcnow(),
        "version": existing_rule.version + 1
    })

    # 存储并重新注册
    _rules_store[rule_id] = updated_rule
    engine.register_rule(updated_rule)

    return updated_rule


@app.delete("/api/rules/{rule_id}", status_code=204, tags=["Rules"])
async def delete_rule(rule_id: str) -> None:
    """
    删除规则

    Args:
        rule_id: 规则ID

    Raises:
        HTTPException: 规则不存在
    """
    if rule_id not in _rules_store:
        raise HTTPException(status_code=404, detail="Rule not found")

    engine = get_rule_engine()

    del _rules_store[rule_id]
    engine.unregister_rule(rule_id)


# ==================== 规则评估 API ====================

@app.post("/api/rules/evaluate", response_model=EvaluateResponse, tags=["Evaluation"])
async def evaluate_rules(request: EvaluateRequest) -> EvaluateResponse:
    """
    评估规则

    根据提供的上下文评估所有规则，返回匹配结果。

    Args:
        request: 评估请求

    Returns:
        评估响应，包含匹配的规则和执行结果
    """
    engine = get_rule_engine()
    start_time = time.perf_counter()

    # 评估并执行动作
    results = await engine.evaluate_and_execute(
        context=request.context,
        rule_ids=request.rule_ids,
        execute_actions=request.execute_actions
    )

    execution_time = (time.perf_counter() - start_time) * 1000

    return EvaluateResponse(
        matched_rules=results,
        total_rules_evaluated=len(request.rule_ids) if request.rule_ids else len(_rules_store),
        execution_time_ms=round(execution_time, 2)
    )


@app.post("/api/rules/evaluate/dry-run", response_model=EvaluateResponse, tags=["Evaluation"])
async def dry_run_evaluate(request: EvaluateRequest) -> EvaluateResponse:
    """
    演练评估（不执行动作）

    用于测试规则条件是否匹配，但不执行实际动作。

    Args:
        request: 评估请求

    Returns:
        评估响应
    """
    engine = get_rule_engine()
    start_time = time.perf_counter()

    # 只评估，不执行动作
    matched_rules = engine.evaluate(
        context=request.context,
        rule_ids=request.rule_ids
    )

    execution_time = (time.perf_counter() - start_time) * 1000

    # 构建结果（不包含动作执行结果）
    results = [
        RuleMatchResult(
            rule_id=rule.id,
            rule_name=rule.name,
            matched=True,
            context=request.context,
            actions_executed=[],
            execution_time_ms=0.0
        )
        for rule in matched_rules
    ]

    return EvaluateResponse(
        matched_rules=results,
        total_rules_evaluated=len(request.rule_ids) if request.rule_ids else len(_rules_store),
        execution_time_ms=round(execution_time, 2)
    )


# ==================== 规则验证 API ====================

@app.post("/api/rules/validate", tags=["Evaluation"])
async def validate_rule(rule_create: RuleCreate) -> dict[str, Any]:
    """
    验证规则

    验证规则条件表达式是否有效。

    Args:
        rule_create: 规则创建请求

    Returns:
        验证结果
    """
    engine = get_rule_engine()

    # 使用示例上下文测试条件
    test_context = {
        "user_id": "test_user",
        "event_count": 0,
        "purchase_count": 0,
        "total_amount": 0.0,
        "view_count": 0,
        "click_count": 0
    }

    try:
        engine._safe_eval(rule_create.condition, test_context)
        return {
            "valid": True,
            "condition": rule_create.condition
        }
    except Exception as e:
        return {
            "valid": False,
            "condition": rule_create.condition,
            "error": str(e)
        }


# ==================== 统计 API ====================

@app.get("/api/rules/stats", tags=["Statistics"])
async def get_rules_stats() -> dict[str, Any]:
    """
    获取规则统计信息

    Returns:
        统计信息
    """
    rules = list(_rules_store.values())

    enabled_count = sum(1 for r in rules if r.enabled)
    disabled_count = len(rules) - enabled_count

    # 按标签统计
    tag_counts: dict[str, int] = {}
    for rule in rules:
        for tag in rule.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # 按优先级统计
    priority_counts: dict[int, int] = {}
    for rule in rules:
        priority_counts[rule.priority] = priority_counts.get(rule.priority, 0) + 1

    return {
        "total_rules": len(rules),
        "enabled_rules": enabled_count,
        "disabled_rules": disabled_count,
        "tags": tag_counts,
        "priority_distribution": priority_counts
    }


# ==================== 入口 ====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "behavior_rules.main:app",
        host="0.0.0.0",
        port=settings.rules_port,
        reload=settings.debug
    )
