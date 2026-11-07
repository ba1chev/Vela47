import pytest
from datetime import datetime, timedelta, timezone

from db import UtcDateTime

PLUS_TWO = timezone(timedelta(hours = 2))


class TestUtcDateTime:
    def test_an_aware_value_is_stored_as_utc(self):
        stored = UtcDateTime().process_bind_param(datetime(2026, 1, 1, 12, tzinfo = PLUS_TWO), None)
        assert stored == datetime(2026, 1, 1, 10, tzinfo = timezone.utc)
        assert stored.utcoffset() == timedelta(0)

    def test_a_naive_value_is_refused_rather_than_guessed(self):
        with pytest.raises(ValueError):
            UtcDateTime().process_bind_param(datetime(2026, 1, 1, 12), None)

    def test_a_naive_value_read_back_is_marked_utc(self):
        read = UtcDateTime().process_result_value(datetime(2026, 1, 1, 10), None)
        assert read.tzinfo is timezone.utc

    def test_an_aware_value_read_back_is_converted_to_utc(self):
        read = UtcDateTime().process_result_value(datetime(2026, 1, 1, 12, tzinfo = PLUS_TWO), None)
        assert read == datetime(2026, 1, 1, 10, tzinfo = timezone.utc)
        assert read.utcoffset() == timedelta(0)

    def test_none_passes_through_both_ways(self):
        assert UtcDateTime().process_bind_param(None, None) is None
        assert UtcDateTime().process_result_value(None, None) is None
