import pytest

from app import operations


@pytest.mark.parametrize(
    "a, b, expected",
    [(2, 3, 5), (-1, 1, 0), (0.1, 0.2, 0.3), (1e10, 1e10, 2e10)],
)
def test_add(a, b, expected):
    assert operations.add(a, b) == pytest.approx(expected)


@pytest.mark.parametrize("a, b, expected", [(5, 3, 2), (3, 5, -2), (-2, -2, 0)])
def test_subtract(a, b, expected):
    assert operations.subtract(a, b) == expected


@pytest.mark.parametrize("a, b, expected", [(4, 3, 12), (-2, 3, -6), (7, 0, 0), (2.5, 2, 5.0)])
def test_multiply(a, b, expected):
    assert operations.multiply(a, b) == expected


@pytest.mark.parametrize("a, b, expected", [(10, 2, 5), (7, 2, 3.5), (-9, 3, -3), (0, 5, 0)])
def test_divide(a, b, expected):
    assert operations.divide(a, b) == expected


def test_divide_by_zero_raises():
    with pytest.raises(ZeroDivisionError, match="divide by zero"):
        operations.divide(1, 0)
