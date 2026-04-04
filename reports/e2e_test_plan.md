# BehaviorSense 端到端测试计划

## 测试目标

对 BehaviorSense 系统的每个微服务进行端到端测试，确保功能符合 wiki 知识库的要求。

## 微服务清单

| 服务 | 端口 | 技术栈 | 测试状态 |
|------|------|--------|----------|
| behavior-core | - | Python | 待测试 |
| behavior-mock | 8001 | FastAPI | 待测试 |
| behavior-stream | - | Faust | 待测试 |
| behavior-rules | 8002 | FastAPI | 待测试 |
| behavior-insight | 8003 | FastAPI | 待测试 |
| behavior-audit | 8004 | FastAPI | 待测试 |

---

## 1. behavior-core 核心库测试

### 1.1 数据模型测试
- [ ] UserBehavior 模型验证
- [ ] EventType 枚举完整性
- [ ] StandardEvent 模型验证
- [ ] Pydantic 验证规则

### 1.2 配置管理测试
- [ ] Settings 加载正确性
- [ ] 环境变量覆盖
- [ ] 数据库连接配置

### 1.3 安全模块测试
- [ ] JWT 生成和验证
- [ ] 密码哈希
- [ ] 认证中间件

### 1.4 中间件测试
- [ ] 限流中间件
- [ ] 链路追踪
- [ ] 请求日志

---

## 2. behavior-mock 服务测试

### 2.1 API 端点测试
- [ ] POST /api/mock/generate - 生成用户行为
- [ ] POST /api/mock/scenario/start - 启动场景模拟
- [ ] POST /api/mock/scenario/{scenarioId}/stop - 停止场景

### 2.2 功能测试
- [ ] 事件生成器正确性
- [ ] 多事件类型支持 (VIEW, CLICK, SEARCH, PURCHASE, COMMENT, LOGIN, LOGOUT)
- [ ] 批量生成功能
- [ ] 流式生成功能
- [ ] Pulsar 生产者连接和发送

### 2.3 场景模拟测试
- [ ] flash_sale 场景
- [ ] 异常流量场景
- [ ] 可配置生成速率

---

## 3. behavior-stream 流处理测试

### 3.1 流处理功能
- [ ] Faust 应用启动
- [ ] Topic 订阅正确性
- [ ] 事件消费和处理

### 3.2 聚合功能
- [ ] 窗口聚合 (1分钟窗口)
- [ ] 用户统计更新
- [ ] 事件计数正确性

### 3.3 模式检测
- [ ] 登录失败检测 (10分钟5次)
- [ ] 高活跃度检测
- [ ] 异常行为识别

---

## 4. behavior-rules 规则引擎测试

### 4.1 API 端点测试
- [ ] POST /api/rules - 创建规则
- [ ] GET /api/rules/{ruleId} - 查询规则
- [ ] PUT /api/rules/{ruleId} - 更新规则
- [ ] DELETE /api/rules/{ruleId} - 删除规则
- [ ] GET /api/rules - 规则列表

### 4.2 规则引擎功能
- [ ] 规则解析 (AST)
- [ ] 规则评估正确性
- [ ] 规则优先级
- [ ] 安全 eval 执行

### 4.3 动作执行测试
- [ ] TAG_USER 动作
- [ ] TRIGGER_AUDIT 动作
- [ ] SEND_NOTIFICATION 动作
- [ ] 热加载规则

---

## 5. behavior-insight 洞察服务测试

### 5.1 API 端点测试
- [ ] GET /api/insight/user/{userId}/tags - 查询用户标签
- [ ] GET /api/insight/user/{userId}/profile - 查询用户画像
- [ ] POST /api/insight/user/tags/batch - 批量查询标签
- [ ] PUT /api/insight/user/{userId}/tag - 更新标签
- [ ] GET /api/insight/tags/statistics - 标签统计

### 5.2 标签管理功能
- [ ] Redis 存储正确性
- [ ] 标签更新通知
- [ ] 标签体系完整性

### 5.3 用户画像功能
- [ ] 基础属性标签
- [ ] 行为特征标签
- [ ] 统计指标标签
- [ ] 预测标签

---

## 6. behavior-audit 审核服务测试

### 6.1 API 端点测试
- [ ] POST /api/audit/order - 创建审核工单
- [ ] GET /api/audit/order/{orderId} - 查询工单
- [ ] PUT /api/audit/order/{orderId}/review - 提交审核结果
- [ ] GET /api/audit/orders - 审核列表
- [ ] GET /api/audit/orders/todo - 待办审核

### 6.2 审核流程测试
- [ ] 状态机转换正确性 (PENDING → IN_REVIEW → APPROVED/REJECTED → CLOSED)
- [ ] 工单创建
- [ ] 审核提交
- [ ] 分配机制

---

## 7. 集成测试

### 7.1 端到端数据流
- [ ] Mock → Pulsar → Stream → Rules → Insight 完整链路
- [ ] 规则触发 → 审核工单创建
- [ ] 标签更新 → 用户画像更新

### 7.2 消息队列测试
- [ ] Pulsar 连接
- [ ] Topic 订阅/发布
- [ ] 消息持久化

### 7.3 数据库测试
- [ ] PostgreSQL 连接
- [ ] Redis 缓存
- [ ] ClickHouse 分析查询

---

## 测试策略

### 并行测试执行
使用多个 SubAgent 并行测试不同的微服务：
1. Agent 1: Core + Mock 服务测试
2. Agent 2: Stream + Rules 服务测试
3. Agent 3: Insight + Audit 服务测试
4. Agent 4: 集成测试

### 测试工具
- pytest 单元测试
- httpx 异步 HTTP 测试
- testcontainers 容器化测试
- Faker 测试数据生成

---

## 测试报告

测试完成后生成汇总报告，包含：
- 每个服务的测试覆盖率
- 功能符合度评分
- 发现的问题列表
- 改进建议
