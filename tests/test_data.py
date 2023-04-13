# System under test.
import data
# Third-party.
import pytest


@pytest.mark.parametrize('value, size', (
    (data.b, 1), (data.B, 1),
    (data.h, 2), (data.H, 2),
    (data.i, 4), (data.I, 4), (data.l, 4), (data.L, 4),
    (data.q, 8), (data.Q, 8),
    (data.u1, 1), (data.U1, 1), (data.s1, 1), (data.S1, 1),
    (data.u2, 2), (data.U2, 2), (data.s2, 2), (data.S2, 2),
    (data.u4, 4), (data.U4, 4), (data.s4, 4), (data.S4, 4),
    (data.u8, 8), (data.U8, 8), (data.s8, 8), (data.S8, 8),
    (data._, 1), (data.e, 2), (data.f, 4), (data.d, 8),
    (data.b1, 1), (data.B1, 1),
    (data.f2, 2), (data.F2, 2),
    (data.f4, 4), (data.F4, 4),
    (data.f8, 8), (data.F8, 8),
    (data.x, 1), (data.s, 1), (data.c, 1),
    (data.p1, 1), (data.P1, 1), (data.t1, 1), (data.T1, 1)
))
def test_atomic(value, size):
    """It is a valid matcher for a single value.
    It has the correct size value.
    It stringifies to a single line which indicates an endianness
    and that it is atomic."""
    assert value.size == size
    assert isinstance(value, data.Structure)
    assert isinstance(value, data.Field)
    assert value.offset == 0
    assert value.padding == 0
    s = str(value)
    assert '\n' not in s
    assert s.startswith(('big-endian', 'little-endian', 'unknown-endian'))
    assert 'atomic' in s
