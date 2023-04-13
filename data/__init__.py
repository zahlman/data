from enum import Enum
from struct import Struct


class _ArrayElement:
    def __init__(self, shape=()):
        self._shape = shape


    def __add__(self, other):
        x = self._normalize()
        y = other._normalize()
        return x.__class__(x.parts + y.parts, x.names + y.names)


    @property
    def size(self):
        result = self.element_size
        for dimension in self.shape:
            result *= dimension
        return result


    @property
    def shape(self):
        return self._shape


    @property
    def shapestr(self):
        return ''.join(f'[{s}]' for s in self.shape)


class Components(_ArrayElement):
    # "parts" are either other Components, or Atoms.
    def __init__(self, parts, names=None, shape=()):
        super().__init__(shape)
        self._parts = parts
        if names is None:
            self._names = (None,) * len(parts)
        elif len(names) != len(parts):
            raise ValueError('name count must match field count')
        else:
            self._names = tuple(names)


    def _normalize(self):
        return self if self._shape == () else Components((self,))


    def group(self, name=None):
        return Components((self,), (name,))


    def named(self, name):
        if len(self.parts) != 1:
            raise ValueError("can't apply single name to multiple fields")
        return Components(self.parts, (name,), self._shape)


    def with_names(self, names):
        return Components(self.parts, names, self._shape)


    @property
    def element_size(self):
        return sum(p.size for p in self.parts)


    @property
    def parts(self):
        return self._parts


    @property
    def names(self):
        return self._names


    def __mul__(self, count):
        return Components(self.parts, self.names, self.shape + (count,))


    def _fields(self, amount, include_shapestr=True):
        if include_shapestr:
            yield self.shapestr
        inames = [
            str(i) if name is None else name
            for i, name in enumerate(self.names)
        ]
        width = max(len(name) for name in inames)
        for name, part in zip(inames, self.parts):
            name = str(i) if name is None else name
            yield f'{name:{width}}: {part._indented(amount + width + 2)}'


    def _indented(self, amount, include_shapestr=True):
        joiner = '\n' + (' ' * amount)
        return joiner.join(self._fields(amount, include_shapestr))


    def __str__(self):
        return self._indented(0)


class Atom(_ArrayElement):
    def __init__(self, typecode, shape=()):
        super().__init__(shape)
        self._typecode = typecode


    def _normalize(self):
        return Components((self,))


    @property
    def element_size(self):
        return {
            'b': 1, 'B': 1, 'h': 2, 'H': 2, 'i': 4, 'I': 4, 'q': 8, 'Q': 8,
            '?': 1, 'x': 1, 's': 1, 'e': 2, 'f': 4, 'd': 8
        }[self._typecode]


    def _indented(self, _):
        return str(self)


    def __str__(self):
        typename = {
            'b': 'unsigned byte', 'B': 'signed byte',
            'h': 'unsigned 2-bytes', 'H': 'signed 2-bytes',
            'i': 'unsigned 4-bytes', 'I': 'signed 4-bytes',
            'q': 'unsigned 8-bytes', 'Q': 'signed 8-bytes',
            '?': 'bool', 'x': '<ignored>', 's': 'text',
            'e': 'half-float', 'f': 'float', 'd': 'double'
        }[self._typecode]
        return f'{typename}{self.shapestr}'


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
    def data_size(self):
        return self._components.size


    @property
    def size(self):
        return self._offset + self._padding + self.data_size


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


    def __str__(self):
        edesc = {'|': 'unknown', '<': 'little', '>': 'big'}[self._endian]
        endian = f'{edesc}-endian matcher for'
        embed_info = f'(offset={self._offset}, padding={self._padding})'
        if isinstance(self._components, Atom):
            return f'{endian} {self._components!r} (atomic) {embed_info}'
        shape_label = self._components.shapestr
        field_text = self._components._indented(0, False)
        return f'{endian} structure{shape_label} {embed_info}:\n{field_text}'


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
