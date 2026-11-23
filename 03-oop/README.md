# 03 - OOP problems

Statement: https://gist.github.com/bdallard/b2f2c910e3a9b564a30c86991c97b4fc (slide 67)

| File | Content |
|---|---|
| [`operator_overloading.py`](operator_overloading.py) | P1 `ComplexNumber` (`+`, `-`), P2 `Person` (`>` on age), P4 `Vector3D` (`*` = dot product), P5 `Circle` (the 6 comparisons), P6 `Point2D` (compared by distance to the origin), P7 `Matrix` (`*` = matrix product) |
| [`inheritance.py`](inheritance.py) | P1 `Vehicle` → `Car` / `Bicycle`, P2 `Person` → `Student` / `Employee`, P3 `BankAccount` → `SavingsAccount` |
| [`test_oop.py`](test_oop.py) | 22 pytest tests |

```bash
python3 operator_overloading.py
python3 inheritance.py
python3 -m pytest
```

## What I learned / choices

- **Dunder methods**: `a + b` is really `a.__add__(b)`. If `__add__` returns `NotImplemented`, Python tries `b.__radd__(a)`, and only then raises `TypeError`. That's why I return `NotImplemented` (and not `False` or an exception) when the other object has the wrong type, and why `2 + ComplexNumber(1, 1)` works thanks to `__radd__`.
- **Reflected comparisons**: I only wrote `__gt__` for `Person`, but `p1 < p2` still works because Python tries `p2.__gt__(p1)`.
- **`__eq__` and `__hash__`**: when a class defines `__eq__`, Python sets `__hash__` to `None` unless you define it. My objects are mutable (the radius can change), so I leave them unhashable on purpose.
- **Floats**: `Point2D` compares distances with `math.isclose`, otherwise `Point2D(0.1 + 0.2, 0) == Point2D(0.3, 0)` would be `False`.
- **Matrix product**: cell `(i, j)` = row `i` of A "dot" column `j` of B. The columns come from `zip(*rows)` (transpose). Shapes are checked: `(n×m) * (m×p)` only.
- **Inheritance**: `super().__init__(...)` lets the parent set the shared attributes, and `super().introduce()` reuses the parent sentence instead of copying it.
- **Encapsulation**: the balance is stored in `_balance` and exposed with a read-only `@property`, so it can only change through `deposit`, `withdraw`, `transfer` and `add_interest`.
