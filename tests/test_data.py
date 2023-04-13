# System under test.
import data
# Third-party.
import pytest


types_and_sizes = (
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
)


types = tuple(t for t, s in types_and_sizes)


def _compatible_endian(first, second):
    e1, e2 = first.endian, second.endian
    return e1 == e2 or e1 == '|' or e2 == '|'


endians = ('big-endian', 'little-endian', 'unknown-endian')


@pytest.mark.parametrize('value, size', types_and_sizes)
def test_atomic(value, size):
    """It is a valid matcher for a single value.
    It has the correct size value.
    It stringifies to a single line which indicates an endianness
    and that it is atomic."""
    assert isinstance(value, data.Structure)
    assert isinstance(value, data.Field)
    assert value.size == size
    assert value.offset == 0
    assert value.padding == 0
    s = str(value)
    assert '\n' not in s
    assert s.startswith(endians)
    assert 'atomic' in s


@pytest.mark.parametrize('first', types)
@pytest.mark.parametrize('second', types)
def test_bad_pairs(first, second):
    """Adding two incompatible atomic values raises ValueError."""
    if not _compatible_endian(first, second):
        with pytest.raises(ValueError):
            matcher = first + second


@pytest.mark.parametrize('first', types)
@pytest.mark.parametrize('second', types)
def test_good_pairs(first, second):
    """Adding two compatible atomic values creates a structure matcher."""
    if not _compatible_endian(first, second):
        return
    matcher = first + second
    assert isinstance(matcher, data.Structure)
    assert matcher.size == first.size + second.size
    assert matcher.offset == 0
    assert matcher.padding == 0
    lines = str(matcher).splitlines()
    assert len(lines) == 3
    assert lines[0].startswith(endians)
    assert 'structure' in lines[0]
    # We need the underlying Atom for testing, but it probably shouldn't
    # be exposed as a property.
    assert lines[1].startswith('0:')
    assert str(first._components) in lines[1]
    assert lines[2].startswith('1:')
    assert str(second._components) in lines[2]
