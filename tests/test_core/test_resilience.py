"""
弹性模式测试
"""
import asyncio
import pytest
from behavior_core.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
    RetryConfig,
    with_circuit_breaker,
    with_retry,
)


class TestRetryConfig:
    def test_default_config(self):
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0

    def test_delay_calculation(self):
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=False)
        assert config.get_delay(0) == 1.0
        assert config.get_delay(1) == 2.0
        assert config.get_delay(2) == 4.0

    def test_max_delay_cap(self):
        config = RetryConfig(base_delay=1.0, max_delay=5.0, jitter=False)
        assert config.get_delay(10) == 5.0


class TestCircuitBreaker:
    def test_initial_state_closed(self):
        breaker = CircuitBreaker()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.can_execute() is True

    def test_opens_after_threshold(self):
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker(config)

        for _ in range(3):
            breaker.record_failure()

        assert breaker.state == CircuitState.OPEN
        assert breaker.can_execute() is False

    def test_transitions_to_half_open(self):
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.1)
        breaker = CircuitBreaker(config)

        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

        # Wait for recovery
        import time
        time.sleep(0.2)

        assert breaker.can_execute() is True
        assert breaker.state == CircuitState.HALF_OPEN

    def test_closes_after_success_in_half_open(self):
        config = CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=0.1,
            success_threshold=2,
        )
        breaker = CircuitBreaker(config)

        breaker.record_failure()
        import time
        time.sleep(0.2)
        breaker.can_execute()  # Transition to half-open

        breaker.record_success()
        breaker.record_success()

        assert breaker.state == CircuitState.CLOSED

    def test_reopens_on_failure_in_half_open(self):
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.1)
        breaker = CircuitBreaker(config)

        breaker.record_failure()
        import time
        time.sleep(0.2)
        breaker.can_execute()  # Transition to half-open

        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

    def test_get_stats(self):
        breaker = CircuitBreaker()
        stats = breaker.get_stats()
        assert "state" in stats
        assert "failure_count" in stats


class TestWithRetryDecorator:
    @pytest.mark.asyncio
    async def test_success_no_retry(self):
        call_count = 0

        @with_retry(RetryConfig(max_retries=3))
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await success_func()
        assert result == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        call_count = 0

        @with_retry(RetryConfig(max_retries=3, base_delay=0.01))
        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "ok"

        result = await failing_then_success()
        assert result == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_exhausts_retries(self):
        @with_retry(RetryConfig(max_retries=2, base_delay=0.01))
        async def always_fail():
            raise ValueError("always fails")

        with pytest.raises(ValueError):
            await always_fail()


class TestWithCircuitBreakerDecorator:
    @pytest.mark.asyncio
    async def test_allows_when_closed(self):
        breaker = CircuitBreaker()

        @with_circuit_breaker(breaker)
        async def success_func():
            return "ok"

        result = await success_func()
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_blocks_when_open(self):
        config = CircuitBreakerConfig(failure_threshold=1)
        breaker = CircuitBreaker(config)
        breaker.record_failure()

        @with_circuit_breaker(breaker)
        async def success_func():
            return "ok"

        with pytest.raises(CircuitOpenError):
            await success_func()

    @pytest.mark.asyncio
    async def test_fallback_when_open(self):
        config = CircuitBreakerConfig(failure_threshold=1)
        breaker = CircuitBreaker(config)
        breaker.record_failure()

        def fallback():
            return "fallback"

        @with_circuit_breaker(breaker, fallback=fallback)
        async def success_func():
            return "ok"

        result = await success_func()
        assert result == "fallback"
