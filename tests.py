import math
from your_filename import very_long_function_name


def test_function_passes():
    """Test with simple integers to ensure the math logic is correct."""
    # (1 + 1 + 1 + 1) * pi = 4 * pi
    expected = 4 * math.pi
    result = very_long_function_name(1, 1, 1, 1)

    # Using math.isclose is best practice for comparing floats
    assert math.isclose(result, expected), f"Expected {expected}, but got {result}"


def test_function_fails():
    """This test is designed to fail to check your GitHub Actions error reporting."""
    result = very_long_function_name(1, 2, 3, 4)
    # This will fail because the actual result is 10 * pi (~31.41), not 100
    assert result == 100, "intentional failure to test GitHub Actions"
