from db import Float32Vector


class TestFloat32Vector:
    def test_a_vector_survives_the_round_trip(self):
        column = Float32Vector()
        stored = column.process_bind_param([0.5, -1.25, 3.0], None)
        assert column.process_result_value(stored, None) == [0.5, -1.25, 3.0]

    def test_it_is_stored_as_four_bytes_per_dimension(self):
        assert len(Float32Vector().process_bind_param([0.0] * 1024, None)) == 4096

    def test_precision_is_float32(self):
        column = Float32Vector()
        restored = column.process_result_value(column.process_bind_param([0.1], None), None)[0]
        assert restored != 0.1 and abs(restored - 0.1) < 1e-7

    def test_none_passes_through_both_ways(self):
        assert Float32Vector().process_bind_param(None, None) is None
        assert Float32Vector().process_result_value(None, None) is None
