from enum import Enum
from struct import Struct


def _normalize(x):
    return x if (x.shape == () and not isinstance(x, Atom)) else Components((x,))


def _add(x, y):
    # each is either a Components or Atom,
    # and may be scalar or array.
    xn = _normalize(x)
    yn = _normalize(y)
    return Components(xn.parts + yn.parts, xn.names + yn.names)


class Components:
    # "parts" are either other Components, or Atoms.
    def __init__(self, parts, names=None, shape=()):
        self._parts = parts
        if names is None:
            self._names = (None,) * len(parts)
        elif len(names) != len(parts):
            raise ValueError('name count must match field count')
        else:
            self._names = tuple(names)
        self._shape = shape


    def group(self, name=None):
        return Components((self,), (name,))


    def named(self, name):
        if len(self.parts) != 1:
            raise ValueError("can't apply single name to multiple fields")
        return Components(self.parts, (name,), self._shape)


    def with_names(self, names):
        return Components(self.parts, names, self._shape)


    @property
    def size(self):
        result = sum(p.size for p in self.parts)
        for dimension in self._shape:
            result *= dimension
        return result


    @property
    def parts(self):
        return self._parts


    @property
    def names(self):
        return self._names


    @property
    def shape(self):
        return self._shape


    def __add__(self, other):
        return _add(self, other)


    def __mul__(self, count):
        return Components(self.parts, self.names, self.shape + (count,))


    @property
    def shapestr(self):
        return ''.join(f'[{s}]' for s in self.shape)


    def _indented(self, amount):
        joiner = '\n' + ' ' * amount
        inames = (
            str(i) if name is None else name for i, name in enumerate(self.names)
        )
        return self.shapestr + joiner + joiner.join(
            f"{name}: {part._indented(amount + len(name) + 2)}"
            if isinstance(part, Components)
            else f'{name}: {part!r}'
            for name, part in zip(inames, self.parts)
        )


    def __repr__(self):
        return self._indented(0)


class Atom:
    def __init__(self, typecode, shape=()):
        self._typecode = typecode
        self._shape = shape


    @property
    def shape(self):
        return self._shape


    @property
    def shapestr(self):
        return ''.join(f'[{s}]' for s in self.shape)


    @property
    def size(self):
        result = {
            'b': 1, 'B': 1, 'h': 2, 'H': 2, 'i': 4, 'I': 4, 'q': 8, 'Q': 8,
            '?': 1, 'x': 1, 's': 1, 'e': 2, 'f': 4, 'd': 8
            # TODO
        }[self._typecode]
        for dimension in self._shape:
            result *= dimension
        return result


    def __repr__(self):
        return f'{self._typecode}{self.shapestr}'


    def __add__(self, other):
        return _add(self, other)


    def __mul__(self, other):
        return Atom(self._typecode, self.shape + (other,))


class Structure:
    def __init__(self, components, endian='|', offset=0, padding=0):
        self._offset = offset
        self._padding = padding
        # a single Components or Atom, representing the struct members.
        self._components = components
        self._endian = endian


    @property
    def size(self):
        return self._offset + self._padding + self._components.size


    def group(self, name=None):
        return Structure(self._components.group(name), self._endian)


    def named(self, name):
        return Structure(self._components.named(name), self._endian)


    def with_names(self, names):
        return Structure(self._components.with_names(names), self._endian)


    def __add__(self, other):
        try:
            endian = {
                '>|': '>', '<|': '<',
                '||': '|', '>>': '>', '<<': '<',
                '|>': '>', '|<': '<'
            }[self._endian + other._endian]
        except KeyError:
            raise ValueError('endian conflict') from None
        return Structure(self._components + other._components, endian)


    def __mul__(self, count):
        return Structure(self._components * count, self._endian)


    def __repr__(self):
        return f'{self._endian}\n{self._components!r}'


class Field(Structure, Enum):
    # size, format code, endian
    # names alluding to underlying format codes
    # integers
    b = (1, 'b', '|')
    B = (1, 'B', '|')
    h = (2, 'h', '|')
    H = (2, 'H', '|')
    # Normalize to always use the same code internally.
    i = (4, 'i', '|')
    I = (4, 'I', '|')
    l = (4, 'i', '|')
    L = (4, 'I', '|')
    q = (8, 'q', '|')
    Q = (8, 'Q', '|')
    # booleans
    _ = (1, '?', '|')
    # floats
    e = (2, 'e', '|')
    f = (4, 'f', '|')
    d = (8, 'd', '|')
    # text
    x = (1, 'x', '|') # a byte whose value will be discarded.
    s = (1, 's', '|') # "arrays" of bytes will become a single `bytes` object.
    c = (1, 's', '|') # a single byte, either way.
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
    # For non-numeric types, no endianness applies inherently, but these types
    # will imply an endianness for the overall struct/array containing them.
    # booleans
    b1 = (1, '?', '<')
    B1 = (1, '?', '>')
    # floats
    f2 = (2, 'e', '<')
    F2 = (2, 'e', '>')
    f4 = (4, 'f', '<')
    F4 = (4, 'f', '>')
    f8 = (8, 'd', '<')
    F8 = (8, 'd', '>')
    # text
    p1 = (1, 'x', '<')
    P1 = (1, 'x', '>')
    t1 = (1, 's', '<')
    T1 = (1, 's', '>')


    def __init__(self, size, code, endian):
        super().__init__(Atom(code), endian)
        assert self.size == size


globals().update(Field.__members__)
