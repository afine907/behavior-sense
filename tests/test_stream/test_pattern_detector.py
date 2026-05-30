"""Tests for pattern detector"""
import pytest
from behavior_stream.pattern_detector import PatternDetector


class TestPatternDetector:
    def setup_method(self):
        self.detector = PatternDetector()

    def test_no_pattern_short_sequence(self):
        matches = self.detector.detect("agent1", {"event_type": "tool_call", "tool_name": "search"})
        assert len(matches) == 0

    def test_loop_detection(self):
        event = {"event_type": "tool_call", "tool_name": "search"}
        # Create loop pattern
        for _ in range(6):
            self.detector.detect("agent1", event)

        matches = self.detector.detect("agent1", event)
        assert any(m.pattern_name == "loop" for m in matches)

    def test_alternation_detection(self):
        event_a = {"event_type": "tool_call", "tool_name": "search"}
        event_b = {"event_type": "tool_call", "tool_name": "write"}

        self.detector.detect("agent1", event_a)
        self.detector.detect("agent1", event_b)
        self.detector.detect("agent1", event_a)
        matches = self.detector.detect("agent1", event_b)

        assert any(m.pattern_name == "alternation" for m in matches)
