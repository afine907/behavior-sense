"""
BehaviorSense 性能测试
使用 locust 进行负载测试
"""
from locust import HttpUser, task, between
import random
import json


class BehaviorSenseUser(HttpUser):
    """模拟用户行为"""

    wait_time = between(1, 3)

    def on_start(self):
        """用户开始时的操作"""
        self.user_ids = [f"user_{i:04d}" for i in range(100)]
        self.rule_ids = [f"rule_{i:04d}" for i in range(10)]

    @task(3)
    def get_health(self):
        """健康检查"""
        self.client.get("/health")

    @task(5)
    def list_rules(self):
        """获取规则列表"""
        self.client.get("/api/rules/")

    @task(2)
    def create_rule(self):
        """创建规则"""
        rule_data = {
            "name": f"perf_test_rule_{random.randint(1000, 9999)}",
            "description": "性能测试规则",
            "condition": "purchase_count > 5",
            "priority": random.randint(1, 10),
            "enabled": True,
            "actions": [
                {"type": "TAG_USER", "params": {"tags": ["perf_test"]}}
            ],
        }
        self.client.post("/api/rules/", json=rule_data)

    @task(4)
    def evaluate_rules(self):
        """评估规则"""
        context = {
            "user_id": random.choice(self.user_ids),
            "purchase_count": random.randint(0, 20),
            "total_amount": random.uniform(0, 10000),
            "view_count": random.randint(0, 100),
        }
        self.client.post("/api/rules/evaluate", json=context)

    @task(3)
    def get_user_tags(self):
        """获取用户标签"""
        user_id = random.choice(self.user_ids)
        self.client.get(f"/api/insight/user/{user_id}/tags")

    @task(2)
    def update_user_tag(self):
        """更新用户标签"""
        user_id = random.choice(self.user_ids)
        tag_data = {
            "tag_name": "perf_tag",
            "tag_value": str(random.randint(1, 5)),
            "source": "manual",
        }
        self.client.put(f"/api/insight/user/{user_id}/tag", json=tag_data)

    @task(3)
    def list_audit_orders(self):
        """获取审核工单列表"""
        self.client.get("/api/audit/orders/")

    @task(1)
    def create_audit_order(self):
        """创建审核工单"""
        order_data = {
            "user_id": random.choice(self.user_ids),
            "rule_id": random.choice(self.rule_ids),
            "trigger_data": {"event_type": "perf_test"},
            "audit_level": random.choice(["low", "medium", "high"]),
        }
        self.client.post("/api/audit/order", json=order_data)

    @task(2)
    def generate_mock_events(self):
        """生成模拟事件"""
        event_data = {
            "count": random.randint(10, 50),
            "event_types": ["view", "click", "purchase"],
        }
        self.client.post("/api/mock/events", json=event_data)


class RulesServiceUser(HttpUser):
    """专门测试 Rules 服务"""

    wait_time = between(0.5, 2)

    @task
    def list_rules(self):
        self.client.get("/api/rules/")

    @task
    def evaluate(self):
        self.client.post(
            "/api/rules/evaluate",
            json={"user_id": "perf_user", "purchase_count": 10},
        )


class InsightServiceUser(HttpUser):
    """专门测试 Insight 服务"""

    wait_time = between(1, 2)

    @task
    def get_tags(self):
        self.client.get("/api/insight/user/perf_user/tags")

    @task
    def get_profile(self):
        self.client.get("/api/insight/user/perf_user/profile")


class AuditServiceUser(HttpUser):
    """专门测试 Audit 服务"""

    wait_time = between(1, 3)

    @task
    def list_orders(self):
        self.client.get("/api/audit/orders/")

    @task
    def get_stats(self):
        self.client.get("/api/audit/stats")
