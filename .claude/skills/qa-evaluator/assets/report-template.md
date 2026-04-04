# 效果评估报告

## 元信息

| 属性 | 值 |
|------|-----|
| **评估时间** | {timestamp} |
| **项目类型** | {project_type} |
| **Git Commit** | {commit_hash} |
| **评估分支** | {branch} |
| **评估范围** | {scope} |

---

## 评分概览

| 维度 | 评分 | 状态 |
|------|------|------|
| 功能正确性 | {functionality_score}/100 | {functionality_status} |
| 性能指标 | {performance_score}/100 | {performance_status} |
| 安全检查 | {security_score}/100 | {security_status} |
| **总分** | **{total_score}/100** | {overall_status} |

---

## 详细评估

### 1. 功能验证

| 检查项 | 预期 | 实际 | 状态 |
|--------|------|------|------|
| {check_1} | {expected_1} | {actual_1} | ✅/❌ |
| {check_2} | {expected_2} | {actual_2} | ✅/❌ |

### 2. 性能指标

| 指标 | 阈值 | 实际值 | 状态 |
|------|------|--------|------|
| {metric_1} | {threshold_1} | {value_1} | ✅/❌ |
| {metric_2} | {threshold_2} | {value_2} | ✅/❌ |

---

## 问题清单

| 级别 | 模块 | 问题描述 | 文件位置 |
|------|------|----------|----------|
| P0 | {module_1} | {issue_1} | {file_1}:{line_1} |
| P1 | {module_2} | {issue_2} | {file_2}:{line_2} |

---

## 改进建议

### 紧急修复 (P0)

1. **{issue_title}**
   - 位置: `{file}:{line}`
   - 建议: {suggestion}

### 性能优化

1. {perf_suggestion}

---

*报告由 qa-evaluator 生成*
*生成时间: {timestamp}*
