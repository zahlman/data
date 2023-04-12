from enum import Enum


little = lambda x: int.from_bytes(x, 'little')
big = lambda x: int.from_bytes(x, 'big')


class Field(Enum):
    # size, format code, endian
    # names alluding to underlying format codes
    # integers
    b = (1, 'b', '?')
    B = (1, 'B', '?')
    h = (2, 'h', '?')
    H = (2, 'H', '?')
    # Normalize to always use the same code internally.
    i = (4, 'i', '?')
    I = (4, 'I', '?')
    l = (4, 'i', '?')
    L = (4, 'I', '?')
    q = (8, 'q', '?')
    Q = (8, 'Q', '?')
    # booleans
    _ = (1, '?', '?')
    # floats
    e = (2, 'e', '?')
    f = (4, 'f', '?')
    d = (8, 'd', '?')
    # text
    x = (1, 'x', '?') # a byte whose value will be discarded.
    s = (1, 's', '?') # "arrays" of bytes will become a single `bytes` object.
    c = (1, 's', '?') # a single byte, either way.
    # deliberately not supporting "Pascal strings".
    # The "native pointer" type also doesn't have a standard size.
    # names directly indicating type properties
    # Integers
    s1 = (1, 'b', '<')
    S1 = (1, 'b', '>')
    u1 = (1, 'B', '<')
    U1 = (1, 'B', '>')
    s2 = (2, 'h', '<')
    S2 = (2, 'h', '>')
    u2 = (2, 'H', '<')
    U2 = (2, 'H', '>')
    s4 = (4, 'i', '<')
    S4 = (4, 'i', '>')
    u4 = (4, 'I', '<')
    U4 = (4, 'I', '>')
    s8 = (8, 'q', '<')
    S8 = (8, 'q', '>')
    u8 = (8, 'Q', '<')
    U8 = (8, 'Q', '>')
    # For non-numeric types, no endianness applies;
    # offer uppercase and lowercase aliases for convenience anyway.
    # booleans
    b1 = (1, '?', '?')
    B1 = (1, '?', '?')
    # floats
    f2 = (2, 'e', '?')
    F2 = (2, 'e', '?')
    f4 = (4, 'f', '?')
    F4 = (4, 'f', '?')
    f8 = (8, 'd', '?')
    F8 = (8, 'd', '?')
    # text
    p1 = (1, 'x', '?')
    P1 = (1, 'x', '?')
    t1 = (1, 's', '?')
    T1 = (1, 's', '?')


globals().update(Field.__members__)
