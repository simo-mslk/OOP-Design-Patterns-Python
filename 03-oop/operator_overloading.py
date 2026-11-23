"""OOP problems - part 1: operator overloading.

Statement: https://gist.github.com/bdallard/b2f2c910e3a9b564a30c86991c97b4fc
(the statement has no problem 3, it goes from 2 to 4)

Rule I used everywhere: if the other operand is not a type I know how to handle,
return NotImplemented. Python then tries the reflected method of the other object
and finally raises a clean TypeError.
"""
from __future__ import annotations

import math
from numbers import Real


# --------------------------------------------------------------------------
# Problem 1 - complex numbers: + and -
# --------------------------------------------------------------------------
class ComplexNumber:
    def __init__(self, real: float = 0.0, imag: float = 0.0):
        self.real = real
        self.imag = imag

    @staticmethod
    def _convert(value):
        """Accept another ComplexNumber or a plain real number (5 == 5 + 0i)."""
        if isinstance(value, ComplexNumber):
            return value
        if isinstance(value, Real):
            return ComplexNumber(value, 0)
        return None

    def __add__(self, other):
        other = self._convert(other)
        if other is None:
            return NotImplemented
        return ComplexNumber(self.real + other.real, self.imag + other.imag)

    __radd__ = __add__          # 3 + z works too (addition is commutative)

    def __sub__(self, other):
        other = self._convert(other)
        if other is None:
            return NotImplemented
        return ComplexNumber(self.real - other.real, self.imag - other.imag)

    def __rsub__(self, other):  # 3 - z  ->  ComplexNumber(3) - z
        other = self._convert(other)
        if other is None:
            return NotImplemented
        return other - self

    def __eq__(self, other):
        other = self._convert(other)
        if other is None:
            return NotImplemented
        return (self.real, self.imag) == (other.real, other.imag)

    def __repr__(self):
        return f"ComplexNumber({self.real}, {self.imag})"

    def __str__(self):
        sign = "-" if self.imag < 0 else "+"
        return f"({self.real} {sign} {abs(self.imag)}i)"


# --------------------------------------------------------------------------
# Problem 2 - persons compared by age with >
# --------------------------------------------------------------------------
class Person:
    def __init__(self, name: str, age: int, gender: str):
        self.name = name
        self.age = age
        self.gender = gender

    def __gt__(self, other):
        if not isinstance(other, Person):
            return NotImplemented
        return self.age > other.age
    # No __lt__ needed: for p1 < p2 Python falls back on p2.__gt__(p1)

    def __repr__(self):
        return f"Person(name={self.name!r}, age={self.age})"


# --------------------------------------------------------------------------
# Problem 4 - 3D vectors: * is the dot product
# --------------------------------------------------------------------------
class Vector3D:
    def __init__(self, x: float, y: float, z: float):
        self.x, self.y, self.z = x, y, z

    def __iter__(self):
        return iter((self.x, self.y, self.z))

    def __mul__(self, other):
        if isinstance(other, Vector3D):
            # dot product: x1*x2 + y1*y2 + z1*z2
            return sum(a * b for a, b in zip(self, other))
        if isinstance(other, Real):
            # extra: vector * number scales the vector
            return Vector3D(*(a * other for a in self))
        return NotImplemented

    def __rmul__(self, other):  # 2 * v
        return self * other if isinstance(other, Real) else NotImplemented

    def __eq__(self, other):
        if not isinstance(other, Vector3D):
            return NotImplemented
        return tuple(self) == tuple(other)

    def __repr__(self):
        return f"Vector3D({self.x}, {self.y}, {self.z})"


# --------------------------------------------------------------------------
# Problem 5 - every comparison operator on circles (based on the radius)
# --------------------------------------------------------------------------
class Circle:
    def __init__(self, radius: float):
        if radius < 0:
            raise ValueError("radius must be >= 0")
        self.radius = radius

    def area(self) -> float:
        return math.pi * self.radius ** 2

    def __eq__(self, other):
        return self.radius == other.radius if isinstance(other, Circle) else NotImplemented

    def __ne__(self, other):
        return self.radius != other.radius if isinstance(other, Circle) else NotImplemented

    def __lt__(self, other):
        return self.radius < other.radius if isinstance(other, Circle) else NotImplemented

    def __le__(self, other):
        return self.radius <= other.radius if isinstance(other, Circle) else NotImplemented

    def __gt__(self, other):
        return self.radius > other.radius if isinstance(other, Circle) else NotImplemented

    def __ge__(self, other):
        return self.radius >= other.radius if isinstance(other, Circle) else NotImplemented

    __hash__ = None   # mutable object with a custom __eq__ -> not hashable

    def __repr__(self):
        return f"Circle(r={self.radius})"


# --------------------------------------------------------------------------
# Problem 6 - 2D points compared by their distance to the origin
# --------------------------------------------------------------------------
class Point2D:
    def __init__(self, x: float, y: float):
        self.x, self.y = x, y

    @property
    def norm(self) -> float:
        """Euclidean distance to (0, 0): sqrt(x² + y²)."""
        return math.hypot(self.x, self.y)

    # The 6 operators all compare the same key, written once in _compare
    def _compare(self, other, op):
        if not isinstance(other, Point2D):
            return NotImplemented
        return op(self.norm, other.norm)

    def __eq__(self, other):
        return self._compare(other, lambda a, b: math.isclose(a, b))

    def __ne__(self, other):
        result = self.__eq__(other)
        return result if result is NotImplemented else not result

    def __lt__(self, other):
        return self._compare(other, lambda a, b: a < b and not math.isclose(a, b))

    def __le__(self, other):
        return self._compare(other, lambda a, b: a < b or math.isclose(a, b))

    def __gt__(self, other):
        return self._compare(other, lambda a, b: a > b and not math.isclose(a, b))

    def __ge__(self, other):
        return self._compare(other, lambda a, b: a > b or math.isclose(a, b))

    __hash__ = None

    def __repr__(self):
        return f"Point2D({self.x}, {self.y})"


# --------------------------------------------------------------------------
# Problem 7 - matrix multiplication with *
# --------------------------------------------------------------------------
class Matrix:
    def __init__(self, rows):
        rows = [list(row) for row in rows]
        if not rows or not rows[0]:
            raise ValueError("a matrix needs at least one value")
        if len({len(row) for row in rows}) != 1:
            raise ValueError("all the rows must have the same length")
        self.rows = rows

    @property
    def n_rows(self) -> int:
        return len(self.rows)

    @property
    def n_cols(self) -> int:
        return len(self.rows[0])

    def columns(self):
        return [list(col) for col in zip(*self.rows)]   # transpose

    def __mul__(self, other):
        if isinstance(other, Real):                       # scalar * every value
            return Matrix([[value * other for value in row] for row in self.rows])
        if not isinstance(other, Matrix):
            return NotImplemented
        if self.n_cols != other.n_rows:
            raise ValueError(
                f"shapes {self.n_rows}x{self.n_cols} and {other.n_rows}x{other.n_cols} don't match"
            )
        # cell (i, j) = row i of self "dot" column j of other
        return Matrix([[sum(a * b for a, b in zip(row, col)) for col in other.columns()]
                       for row in self.rows])

    def __rmul__(self, other):
        return self * other if isinstance(other, Real) else NotImplemented

    __matmul__ = __mul__   # A @ B also works, like in numpy

    def __eq__(self, other):
        return self.rows == other.rows if isinstance(other, Matrix) else NotImplemented

    def __repr__(self):
        return f"Matrix({self.rows})"

    def __str__(self):
        return "\n".join("[ " + "  ".join(f"{v:>4}" for v in row) + " ]" for row in self.rows)


if __name__ == "__main__":
    z1, z2 = ComplexNumber(2, 3), ComplexNumber(1, -4)
    print(f"{z1} + {z2} = {z1 + z2}")        # (3 - 1i)
    print(f"{z1} - {z2} = {z1 - z2}")        # (1 + 7i)

    simo, yasmine = Person("Simo", 21, "M"), Person("Yasmine", 19, "F")
    print("Simo older than Yasmine?", simo > yasmine)       # True
    print("Simo younger than Yasmine?", simo < yasmine)     # False (uses __gt__)

    print("dot product:", Vector3D(1, 0, 2) * Vector3D(3, 5, -1))   # 1

    small, big = Circle(1.5), Circle(4)
    print(small < big, small <= big, small > big, small >= big, small == big, small != big)

    print(Point2D(3, 4) == Point2D(0, 5), Point2D(1, 1) < Point2D(-2, 0))   # True True

    a = Matrix([[1, 2, 3], [4, 5, 6]])       # 2x3
    b = Matrix([[7, 8], [9, 10], [11, 12]])  # 3x2
    print(a * b)                             # 2x2: [[58, 64], [139, 154]]
