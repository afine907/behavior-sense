"""
AI Agent行为模式检测器
"""
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PatternMatch:
    """模式匹配结果"""
    pattern_name: str
    agent_id: str
    confidence: float  # 0.0-1.0
    details: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class PatternDetector:
    """行为模式检测器"""

    def __init__(self):
        self._agent_sequences: dict[str, deque] = defaultdict(lambda: deque(maxlen=50))

    def detect(self, agent_id: str, event: dict[str, Any]) -> list[PatternMatch]:
        """检测行为模式"""
        matches = []

        # Add to sequence
        event_type = event.get("event_type", "unknown")
        tool_name = event.get("tool_name")
        action = f"{event_type}:{tool_name or ''}"
        self._agent_sequences[agent_id].append(action)

        sequence = list(self._agent_sequences[agent_id])

        # Detect patterns
        if self._detect_loop(sequence):
            matches.append(PatternMatch(
                pattern_name="loop",
                agent_id=agent_id,
                confidence=0.9,
                details={"sequence_length": len(sequence)},
            ))

        if self._detect_alternation(sequence):
            matches.append(PatternMatch(
                pattern_name="alternation",
                agent_id=agent_id,
                confidence=0.7,
                details={"pattern": "A-B-A-B"},
            ))

        if self._detect_escalation(agent_id, event):
            matches.append(PatternMatch(
                pattern_name="escalation",
                agent_id=agent_id,
                confidence=0.8,
                details={"type": "resource_usage"},
            ))

        return matches

    def _detect_loop(self, sequence: list[str]) -> bool:
        """检测循环模式"""
        if len(sequence) < 6:
            return False

        # Check for repeating subsequence
        for pattern_len in range(2, min(6, len(sequence) // 2)):
            pattern = sequence[-pattern_len:]
            prev = sequence[-pattern_len * 2:-pattern_len]
            if pattern == prev:
                return True

        return False

    def _detect_alternation(self, sequence: list[str]) -> bool:
        """检测交替模式 (A-B-A-B)"""
        if len(sequence) < 4:
            return False

        last_four = sequence[-4:]
        return (last_four[0] == last_four[2] and
                last_four[1] == last_four[3] and
                last_four[0] != last_four[1])

    def _detect_escalation(self, agent_id: str, event: dict) -> bool:
        """检测资源使用升级模式"""
        # Simple: check if costs are increasing
        history = self._agent_sequences.get(agent_id, [])
        if len(history) < 5:
            return False

        # Check if recent events have increasing latency
        latencies = []
        for e in list(history)[-5:]:
            # This is simplified - in real implementation, store actual values
            pass

        return False
