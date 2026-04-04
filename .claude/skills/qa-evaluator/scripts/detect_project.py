#!/usr/bin/env python3
"""
项目类型检测脚本
分析项目结构，判断是前端、后端还是全栈项目
"""

import os
import sys
import json
import glob
from pathlib import Path
from typing import Dict, List, Tuple


def load_detection_rules(rules_path: str) -> Dict:
    """加载检测规则"""
    import yaml
    with open(rules_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def check_files(root: str, patterns: List[str]) -> int:
    """检查文件是否存在"""
    score = 0
    for pattern in patterns:
        matches = glob.glob(os.path.join(root, pattern), recursive=False)
        if matches:
            score += 1
    return score


def check_patterns(root: str, patterns: List[str]) -> int:
    """检查文件模式"""
    score = 0
    for pattern in patterns:
        matches = glob.glob(os.path.join(root, pattern), recursive=True)
        if matches:
            score += 1
    return score


def check_dirs(root: str, dirs: List[str]) -> int:
    """检查目录是否存在"""
    score = 0
    for d in dirs:
        if os.path.isdir(os.path.join(root, d)):
            score += 1
    return score


def detect_project_type(root: str, rules: Dict) -> Tuple[str, float]:
    """
    检测项目类型
    返回: (项目类型, 置信度)
    """
    detection_rules = rules.get('detection_rules', {})
    config = rules.get('detection_config', {})
    weights = config.get('weights', {})

    scores = {}

    for project_type, rule in detection_rules.items():
        score = 0

        # 检查文件
        if 'has_files' in rule:
            file_score = check_files(root, rule['has_files'])
            score += file_score * weights.get('has_files', 1.0)

        # 检查模式
        if 'has_patterns' in rule:
            pattern_score = check_patterns(root, rule['has_patterns'])
            score += pattern_score * weights.get('has_patterns', 1.0)

        # 检查目录
        if 'has_dirs' in rule:
            dir_score = check_dirs(root, rule['has_dirs'])
            score += dir_score * weights.get('has_dirs', 1.0)

        # 检查排除项
        if 'excludes' in rule:
            exclude_score = check_dirs(root, rule['excludes'])
            score -= exclude_score * abs(weights.get('excludes', 1.0))

        # 检查最小分数
        min_score = rule.get('min_score', 1)
        if score >= min_score:
            scores[project_type] = score

    if not scores:
        return 'backend', 0.5  # 默认后端

    # 返回得分最高的类型
    best_type = max(scores, key=scores.get)
    return best_type, scores[best_type]


def main():
    """主函数"""
    if len(sys.argv) < 2:
        root = os.getcwd()
    else:
        root = sys.argv[1]

    # 规则文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    rules_path = os.path.join(script_dir, '..', 'references', 'detection.yaml')

    if not os.path.exists(rules_path):
        print(json.dumps({'error': 'Rules file not found'}))
        sys.exit(1)

    rules = load_detection_rules(rules_path)
    project_type, confidence = detect_project_type(root, rules)

    result = {
        'project_type': project_type,
        'confidence': confidence,
        'root': root,
        'label': rules.get('type_labels', {}).get(project_type, project_type)
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
