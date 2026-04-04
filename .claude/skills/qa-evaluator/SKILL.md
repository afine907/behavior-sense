---
name: qa-evaluator
description: |
  全栈效果评估Skill，用于验证Claude Code编码Agent产出的代码质量。支持前端、后端、全栈三种项目类型的自动化评估。

  触发场景:
  - 用户想评估代码实现效果：如"评估这个功能"、"验证API是否正常"
  - 用户完成编码后需要验证：如"帮我检查一下代码效果"
  - Git commit 后自动触发评估
  - 用户显式调用：/qa-evaluator

  评估能力:
  - 前端: UI渲染、交互流程、响应式布局、无障碍访问
  - 后端: API功能、数据流完整性、性能指标、安全检查
  - 全栈: 端到端流程、前后端数据一致性、用户场景测试
license: MIT
---

# QA Evaluator

执行自动化效果评估，验证代码实现质量，生成评估报告供迭代修复。

## 评估流程

1. **检测项目类型** - 分析项目结构判断 frontend/backend/fullstack
2. **加载检查清单** - 读取对应的评估检查项
3. **执行评估检查** - 使用 MCP 工具执行验证
4. **生成评估报告** - 输出到 `reports/qa/`

## 项目类型检测

自动检测逻辑：

| 类型 | 特征文件 | 特征目录 |
|------|----------|----------|
| frontend | package.json, *.tsx, *.vue | src/, public/, components/ |
| backend | requirements.txt, pyproject.toml, go.mod | api/, controllers/, services/ |
| fullstack | 同时具备前后端特征 | frontend/, backend/, client/, server/ |

手动指定：`/qa-evaluator frontend` 或 `/qa-evaluator backend`

## 评估执行

### 前端项目

使用 Playwright MCP 执行：

```
1. 页面渲染检查
   - FCP < 1.5s, LCP < 2.5s, CLS < 0.1
   - 无空白页面

2. UI交互测试
   - 表单提交响应
   - 导航跳转正确

3. 响应式布局
   - 移动端 375px
   - 桌面端 1440px

4. 无障碍访问
   - 色彩对比度 WCAG AA
   - 键盘导航
```

### 后端项目

使用 PostgreSQL MCP + HTTP 工具执行：

```
1. API功能验证
   - 健康检查 /health
   - CRUD操作正确性
   - 错误处理完整性

2. 数据流验证
   - 数据库写入检查
   - 缓存同步验证
   - 消息队列状态

3. 性能指标
   - API P99延迟 < 500ms
   - 数据库查询 < 100ms

4. 安全检查
   - SQL注入防护
   - 认证授权
   - 敏感数据脱敏
```

### 全栈项目

执行前端 + 后端评估，并增加：

```
1. 端到端流程
   - 用户登录流程
   - 数据提交流程
   - 删除数据流程

2. 数据一致性
   - 前后端数据同步
   - 后端数据库同步
   - 缓存数据库同步
```

## 详细配置

评估检查项详细配置见：
- [frontend.yaml](references/frontend.yaml) - 前端检查清单
- [backend.yaml](references/backend.yaml) - 后端检查清单
- [fullstack.yaml](references/fullstack.yaml) - 全栈检查清单
- [detection.yaml](references/detection.yaml) - 项目类型检测规则

## 报告生成

评估完成后生成报告到 `reports/qa/YYYYMMDD_HHMMSS_report.md`

报告模板见 [report-template.md](assets/report-template.md)

## 评估脚本

- `scripts/evaluate.sh` - 执行评估的主脚本
- `scripts/check_health.sh` - 服务健康检查
- `scripts/detect_project.py` - 项目类型检测

## 依赖

**MCP Servers**（在 `.claude/mcp.json` 中配置）：
- `playwright` - 浏览器交互、前端评估
- `postgres` - 数据库验证
- `filesystem` - 报告写入

**工具**：
- Bash - API调用、健康检查
- Read/Glob/Grep - 代码分析
- WebFetch - HTTP请求测试

## 示例用法

```bash
# 自动检测项目类型并评估
/qa-evaluator

# 评估后端项目
/qa-evaluator backend

# 快速评估（仅核心功能）
/qa-evaluator --scope quick

# 评估指定commit
/qa-evaluator --commit abc123
```

## 输出示例

```
# 效果评估报告

## 评分概览
| 维度 | 评分 | 状态 |
|------|------|------|
| 功能正确性 | 85/100 | ⚠️ |
| 性能指标 | 90/100 | ✅ |
| **总分** | **87/100** | ⚠️ |

## 问题清单
| 级别 | 模块 | 问题描述 |
|------|------|----------|
| P0 | API | /api/events 返回500 |
| P1 | 性能 | P99延迟过高 |
```
