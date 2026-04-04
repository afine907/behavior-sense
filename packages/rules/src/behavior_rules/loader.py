"""
规则加载器实现

支持从 YAML 文件和数据库加载规则，支持热更新。
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import yaml

from behavior_rules.models import Rule, RuleAction, ActionType
from behavior_rules.engine import RuleEngine


logger = logging.getLogger(__name__)


class RuleLoaderError(Exception):
    """规则加载器异常"""
    pass


class BaseRuleLoader(ABC):
    """规则加载器基类"""

    def __init__(self, engine: RuleEngine):
        self._engine = engine
        self._on_reload_callbacks: list[Callable[[], None]] = []

    @abstractmethod
    def load(self) -> list[Rule]:
        """
        加载规则

        Returns:
            加载的规则列表
        """
        pass

    @abstractmethod
    def reload(self) -> list[Rule]:
        """
        重新加载规则

        Returns:
            重新加载的规则列表
        """
        pass

    def register_reload_callback(self, callback: Callable[[], None]) -> None:
        """
        注册重载回调

        Args:
            callback: 回调函数
        """
        self._on_reload_callbacks.append(callback)

    def _notify_reload(self) -> None:
        """通知重载完成"""
        for callback in self._on_reload_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in reload callback: {e}")


class YamlRuleLoader(BaseRuleLoader):
    """
    YAML 文件规则加载器

    从 YAML 文件加载规则配置，支持单文件和多文件模式。
    """

    def __init__(
        self,
        engine: RuleEngine,
        rule_path: str | Path,
        watch: bool = False
    ):
        """
        初始化 YAML 规则加载器

        Args:
            engine: 规则引擎实例
            rule_path: 规则文件路径或目录路径
            watch: 是否监视文件变化（热更新）
        """
        super().__init__(engine)
        self.rule_path = Path(rule_path)
        self._watch = watch
        self._watcher_task: asyncio.Task | None = None
        self._last_modified: dict[str, float] = {}

    def load(self) -> list[Rule]:
        """
        从 YAML 文件加载规则

        Returns:
            加载的规则列表
        """
        rules: list[Rule] = []

        if self.rule_path.is_file():
            rules.extend(self._load_file(self.rule_path))
        elif self.rule_path.is_dir():
            for yaml_file in self.rule_path.glob("**/*.yaml"):
                rules.extend(self._load_file(yaml_file))
            for yaml_file in self.rule_path.glob("**/*.yml"):
                rules.extend(self._load_file(yaml_file))
        else:
            raise RuleLoaderError(f"Rule path not found: {self.rule_path}")

        # 注册到引擎
        for rule in rules:
            self._engine.register_rule(rule)

        logger.info(f"Loaded {len(rules)} rules from {self.rule_path}")
        return rules

    def _load_file(self, file_path: Path) -> list[Rule]:
        """
        加载单个 YAML 文件

        Args:
            file_path: 文件路径

        Returns:
            规则列表
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = yaml.safe_load_all(f)
                rules: list[Rule] = []

                for rule_data in content:
                    if rule_data is None:
                        continue

                    rule = self._parse_rule(rule_data)
                    rules.append(rule)

                # 记录文件修改时间
                self._last_modified[str(file_path)] = file_path.stat().st_mtime
                return rules

        except Exception as e:
            logger.error(f"Error loading rule file {file_path}: {e}")
            raise RuleLoaderError(f"Failed to load rule file: {e}")

    def _parse_rule(self, data: dict[str, Any]) -> Rule:
        """
        解析规则数据

        Args:
            data: 规则数据字典

        Returns:
            Rule 对象
        """
        actions: list[RuleAction] = []

        for action_data in data.get("actions", []):
            action = RuleAction(
                type=ActionType(action_data["type"]),
                params=action_data.get("params", {}),
                async_exec=action_data.get("async_exec", True),
                retry_count=action_data.get("retry_count", 3),
                retry_delay=action_data.get("retry_delay", 1.0)
            )
            actions.append(action)

        return Rule(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            condition=data["condition"],
            priority=data.get("priority", 0),
            enabled=data.get("enabled", True),
            actions=actions,
            tags=data.get("tags", []),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
            created_by=data.get("created_by"),
            version=data.get("version", 1)
        )

    def _parse_datetime(self, value: str | None) -> datetime:
        """解析日期时间"""
        if value is None:
            return datetime.utcnow()
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(value)

    def reload(self) -> list[Rule]:
        """
        重新加载规则

        Returns:
            重新加载的规则列表
        """
        # 清除现有规则
        for rule_id in list(self._engine.get_all_rules()):
            self._engine.unregister_rule(rule_id.id)

        # 重新加载
        rules = self.load()
        self._notify_reload()
        return rules

    async def start_watching(self) -> None:
        """
        启动文件监视（热更新）

        定期检查文件修改时间，发现变化时自动重新加载。
        """
        if not self._watch:
            return

        self._watcher_task = asyncio.create_task(self._watch_loop())
        logger.info(f"Started watching rule files at {self.rule_path}")

    async def stop_watching(self) -> None:
        """停止文件监视"""
        if self._watcher_task:
            self._watcher_task.cancel()
            try:
                await self._watcher_task
            except asyncio.CancelledError:
                pass
            self._watcher_task = None
            logger.info("Stopped watching rule files")

    async def _watch_loop(self) -> None:
        """文件监视循环"""
        while True:
            try:
                await asyncio.sleep(5)  # 每5秒检查一次
                await self._check_changes()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in watch loop: {e}")

    async def _check_changes(self) -> None:
        """检查文件变化"""
        changed = False

        if self.rule_path.is_file():
            changed = self._check_file_change(self.rule_path)
        elif self.rule_path.is_dir():
            for yaml_file in self.rule_path.glob("**/*.yaml"):
                if self._check_file_change(yaml_file):
                    changed = True
            for yaml_file in self.rule_path.glob("**/*.yml"):
                if self._check_file_change(yaml_file):
                    changed = True

        if changed:
            logger.info("Detected rule file changes, reloading...")
            self.reload()

    def _check_file_change(self, file_path: Path) -> bool:
        """
        检查单个文件是否变化

        Args:
            file_path: 文件路径

        Returns:
            是否有变化
        """
        try:
            current_mtime = file_path.stat().st_mtime
            stored_mtime = self._last_modified.get(str(file_path), 0)

            if current_mtime > stored_mtime:
                self._last_modified[str(file_path)] = current_mtime
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking file change {file_path}: {e}")
            return False


class DbRuleLoader(BaseRuleLoader):
    """
    数据库规则加载器

    从 PostgreSQL 数据库加载规则配置。
    """

    def __init__(
        self,
        engine: RuleEngine,
        database_url: str,
        table_name: str = "rules",
        poll_interval: float = 30.0
    ):
        """
        初始化数据库规则加载器

        Args:
            engine: 规则引擎实例
            database_url: 数据库连接URL
            table_name: 规则表名
            poll_interval: 轮询间隔（秒），用于热更新
        """
        super().__init__(engine)
        self.database_url = database_url
        self.table_name = table_name
        self.poll_interval = poll_interval
        self._pool = None
        self._poller_task: asyncio.Task | None = None
        self._last_update: datetime | None = None

    async def init_pool(self) -> None:
        """初始化数据库连接池"""
        try:
            import asyncpg
            self._pool = await asyncpg.create_pool(self.database_url)
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    async def close_pool(self) -> None:
        """关闭数据库连接池"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database connection pool closed")

    def load(self) -> list[Rule]:
        """
        同步加载（异步包装）

        Returns:
            规则列表
        """
        # 同步方法，需要事件循环
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果事件循环正在运行，创建任务
            future = asyncio.ensure_future(self._load_async())
            # 不能在运行的事件循环中等待，返回空列表
            logger.warning("Cannot load synchronously while event loop is running")
            return []
        else:
            return loop.run_until_complete(self._load_async())

    async def load_async(self) -> list[Rule]:
        """
        异步加载规则

        Returns:
            规则列表
        """
        return await self._load_async()

    async def _load_async(self) -> list[Rule]:
        """
        从数据库加载规则

        Returns:
            规则列表
        """
        if not self._pool:
            await self.init_pool()

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT id, name, description, condition, priority, enabled,
                       actions, tags, created_at, updated_at, created_by, version
                FROM {self.table_name}
                WHERE enabled = true
                ORDER BY priority DESC
                """
            )

            rules: list[Rule] = []
            for row in rows:
                rule = self._parse_row(row)
                rules.append(rule)
                self._engine.register_rule(rule)

            self._last_update = datetime.utcnow()
            logger.info(f"Loaded {len(rules)} rules from database")
            return rules

    def _parse_row(self, row: dict) -> Rule:
        """
        解析数据库行

        Args:
            row: 数据库行

        Returns:
            Rule 对象
        """
        actions: list[RuleAction] = []

        if row["actions"]:
            for action_data in row["actions"]:
                action = RuleAction(
                    type=ActionType(action_data["type"]),
                    params=action_data.get("params", {}),
                    async_exec=action_data.get("async_exec", True),
                    retry_count=action_data.get("retry_count", 3),
                    retry_delay=action_data.get("retry_delay", 1.0)
                )
                actions.append(action)

        return Rule(
            id=str(row["id"]),
            name=row["name"],
            description=row["description"],
            condition=row["condition"],
            priority=row["priority"],
            enabled=row["enabled"],
            actions=actions,
            tags=row["tags"] or [],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            created_by=row["created_by"],
            version=row["version"]
        )

    def reload(self) -> list[Rule]:
        """
        重新加载规则

        Returns:
            规则列表
        """
        # 同步方法，需要事件循环
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.ensure_future(self._reload_async())
            return []
        else:
            return loop.run_until_complete(self._reload_async())

    async def reload_async(self) -> list[Rule]:
        """
        异步重新加载规则

        Returns:
            规则列表
        """
        return await self._reload_async()

    async def _reload_async(self) -> list[Rule]:
        """
        异步重新加载规则实现

        Returns:
            规则列表
        """
        # 清除现有规则
        for rule in self._engine.get_all_rules():
            self._engine.unregister_rule(rule.id)

        # 重新加载
        rules = await self._load_async()
        self._notify_reload()
        return rules

    async def start_polling(self) -> None:
        """
        启动轮询（热更新）

        定期检查数据库中的规则更新。
        """
        self._poller_task = asyncio.create_task(self._poll_loop())
        logger.info(f"Started polling database every {self.poll_interval}s")

    async def stop_polling(self) -> None:
        """停止轮询"""
        if self._poller_task:
            self._poller_task.cancel()
            try:
                await self._poller_task
            except asyncio.CancelledError:
                pass
            self._poller_task = None
            logger.info("Stopped polling database")

    async def _poll_loop(self) -> None:
        """轮询循环"""
        while True:
            try:
                await asyncio.sleep(self.poll_interval)
                await self._check_updates()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in poll loop: {e}")

    async def _check_updates(self) -> None:
        """检查数据库更新"""
        if not self._pool or not self._last_update:
            return

        async with self._pool.acquire() as conn:
            count = await conn.fetchval(
                f"""
                SELECT COUNT(*) FROM {self.table_name}
                WHERE updated_at > $1 AND enabled = true
                """,
                self._last_update
            )

            if count > 0:
                logger.info(f"Detected {count} rule updates, reloading...")
                await self._reload_async()
