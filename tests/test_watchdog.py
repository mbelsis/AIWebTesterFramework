"""
Tests for the Watchdog system — configuration, state comparison, and stats.
Does not require a running browser.
"""

import pytest
from dataclasses import asdict
from utils.watchdog import (
    WatchdogState, WatchdogConfig, WatchdogStats,
    RecoveryStrategy, StateIndicator, Watchdog, create_watchdog,
)


class TestWatchdogState:
    def test_has_changed_detects_dom_hash_change(self):
        s1 = WatchdogState(timestamp=1.0, dom_hash="aaa", request_count=0, pixel_signature="px1")
        s2 = WatchdogState(timestamp=2.0, dom_hash="bbb", request_count=0, pixel_signature="px1")
        changes = s1.has_changed(s2)
        assert changes["dom_hash"] is True
        assert changes["request_count"] is False
        assert changes["pixel_signature"] is False

    def test_has_changed_detects_request_count_change(self):
        s1 = WatchdogState(timestamp=1.0, dom_hash="aaa", request_count=5)
        s2 = WatchdogState(timestamp=2.0, dom_hash="aaa", request_count=10)
        changes = s1.has_changed(s2)
        assert changes["request_count"] is True

    def test_any_changed_with_all_indicators(self):
        s1 = WatchdogState(timestamp=1.0, dom_hash="aaa", request_count=0, pixel_signature="px1")
        s2 = WatchdogState(timestamp=2.0, dom_hash="aaa", request_count=0, pixel_signature="px1")
        assert not s1.any_changed(s2)  # Nothing changed

    def test_any_changed_with_specific_indicators(self):
        s1 = WatchdogState(timestamp=1.0, dom_hash="aaa", request_count=0, pixel_signature="px1")
        s2 = WatchdogState(timestamp=2.0, dom_hash="bbb", request_count=0, pixel_signature="px1")
        assert s1.any_changed(s2, [StateIndicator.DOM_HASH])
        assert not s1.any_changed(s2, [StateIndicator.REQUEST_COUNT])

    def test_identical_states_no_change(self):
        s = WatchdogState(timestamp=1.0, dom_hash="x", request_count=5, pixel_signature="p")
        assert not s.any_changed(s)


class TestWatchdogConfig:
    def test_defaults(self):
        cfg = WatchdogConfig()
        assert cfg.enabled is True
        assert cfg.timeout_seconds == 12.0
        assert cfg.max_recovery_attempts == 3
        assert cfg.check_interval == 2.0
        assert len(cfg.recovery_strategies) > 0
        assert len(cfg.state_indicators) == 3

    def test_custom_values(self):
        cfg = WatchdogConfig(
            timeout_seconds=30.0,
            max_recovery_attempts=5,
            recovery_strategies=[RecoveryStrategy.PAGE_RELOAD],
        )
        assert cfg.timeout_seconds == 30.0
        assert cfg.max_recovery_attempts == 5
        assert len(cfg.recovery_strategies) == 1


class TestWatchdogStats:
    def test_defaults(self):
        stats = WatchdogStats()
        assert stats.total_checks == 0
        assert stats.stuck_detections == 0
        assert stats.recovery_attempts == 0
        assert stats.successful_recoveries == 0
        assert stats.failed_recoveries == 0
        assert isinstance(stats.recovery_strategy_stats, dict)

    def test_strategy_stats_initialized(self):
        stats = WatchdogStats()
        for strategy in RecoveryStrategy:
            assert strategy.value in stats.recovery_strategy_stats


class TestWatchdogInit:
    def test_create_watchdog_with_defaults(self):
        wd = create_watchdog()
        assert wd.config.enabled is True
        assert wd.is_monitoring() is False
        assert wd.get_current_state() is None

    def test_create_watchdog_with_sink(self):
        sink = object()
        wd = create_watchdog(sink=sink)
        assert wd.sink is sink

    def test_track_network_request(self):
        wd = create_watchdog()
        assert wd._request_count == 0
        wd.track_network_request("request")
        assert wd._request_count == 1
        wd.track_network_request("response")
        assert wd._request_count == 2

    def test_reset_stats(self):
        wd = create_watchdog()
        wd.stats.total_checks = 100
        wd.stats.stuck_detections = 5
        wd.reset_stats()
        assert wd.stats.total_checks == 0
        assert wd.stats.stuck_detections == 0
