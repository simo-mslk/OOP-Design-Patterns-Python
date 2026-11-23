"""Tests for the OOP problems (Arrange / Act / Assert when it is not a one-liner)."""
import pytest

from inheritance import BankAccount, Bicycle, Car, Employee, Person, SavingsAccount, Student, Vehicle
from operator_overloading import Circle, ComplexNumber, Matrix, Point2D, Vector3D
from operator_overloading import Person as AgedPerson


# ----------------------------------------------------------- operators ---
class TestComplexNumber:
    def test_add_and_sub(self):
        z1, z2 = ComplexNumber(2, 3), ComplexNumber(1, -4)
        assert z1 + z2 == ComplexNumber(3, -1)
        assert z1 - z2 == ComplexNumber(1, 7)

    def test_mixed_with_real_numbers(self):
        assert ComplexNumber(1, 1) + 2 == ComplexNumber(3, 1)
        assert 2 + ComplexNumber(1, 1) == ComplexNumber(3, 1)
        assert 5 - ComplexNumber(1, 1) == ComplexNumber(4, -1)

    def test_unknown_type_raises_type_error(self):
        with pytest.raises(TypeError):
            ComplexNumber(1, 1) + "a"

    def test_str(self):
        assert str(ComplexNumber(3, -1)) == "(3 - 1i)"


def test_person_greater_means_older():
    old, young = AgedPerson("A", 40, "F"), AgedPerson("B", 20, "M")
    assert old > young
    assert young < old           # reflected __gt__
    assert not young > old


def test_vector_dot_product_and_scaling():
    assert Vector3D(1, 0, 2) * Vector3D(3, 5, -1) == 1
    assert Vector3D(1, 2, 3) * Vector3D(4, 5, 6) == 32
    assert 2 * Vector3D(1, 2, 3) == Vector3D(2, 4, 6)


def test_circle_all_comparisons():
    small, big, same = Circle(1), Circle(3), Circle(1)
    assert small < big and small <= big and small <= same
    assert big > small and big >= small and small >= same
    assert small == same and small != big
    assert sorted([big, small]) == [small, big]


@pytest.mark.parametrize("p, q, expected", [
    (Point2D(3, 4), Point2D(0, 5), "equal"),        # both at distance 5
    (Point2D(1, 1), Point2D(-2, 0), "smaller"),     # 1.41 < 2
    (Point2D(-6, 8), Point2D(5, 5), "bigger"),      # 10 > 7.07
])
def test_points_compared_by_distance(p, q, expected):
    assert (p == q) is (expected == "equal")
    assert (p < q) is (expected == "smaller")
    assert (p > q) is (expected == "bigger")
    assert (p <= q) is (expected != "bigger")
    assert (p >= q) is (expected != "smaller")


def test_point_equality_tolerates_float_errors():
    assert Point2D(0.1 + 0.2, 0) == Point2D(0.3, 0)


class TestMatrix:
    def test_rectangular_product(self):
        a = Matrix([[1, 2, 3], [4, 5, 6]])
        b = Matrix([[7, 8], [9, 10], [11, 12]])
        assert a * b == Matrix([[58, 64], [139, 154]])
        assert a @ b == a * b

    def test_identity(self):
        m = Matrix([[2, -1], [0, 3]])
        assert m * Matrix([[1, 0], [0, 1]]) == m

    def test_scalar(self):
        assert 3 * Matrix([[1, 2]]) == Matrix([[3, 6]])

    def test_incompatible_shapes(self):
        with pytest.raises(ValueError):
            Matrix([[1, 2]]) * Matrix([[1, 2]])

    def test_ragged_rows_rejected(self):
        with pytest.raises(ValueError):
            Matrix([[1, 2], [3]])


# --------------------------------------------------------- inheritance ---
def test_drive_is_overridden():
    assert [v.drive() for v in (Vehicle(), Car(), Bicycle())] == [
        "Driving a vehicle", "Driving a car", "Riding a bicycle"]
    assert isinstance(Car(), Vehicle)


def test_introductions_extend_the_parent_one():
    student = Student("Yasmine", 19, "Casablanca", "Data Science")
    employee = Employee("Karim", 32, "Paris", "Capgemini")
    base = Person("Yasmine", 19, "Casablanca").introduce()
    assert student.introduce().startswith(base)
    assert "Data Science" in student.introduce()
    assert "Capgemini" in employee.introduce()


class TestBankAccounts:
    def test_deposit_and_withdraw(self):
        account = BankAccount("1", 100)
        assert account.deposit(50) == 150
        assert account.withdraw(30) == 120
        with pytest.raises(ValueError):
            account.withdraw(500)
        with pytest.raises(ValueError):
            account.deposit(-5)

    def test_balance_is_read_only(self):
        with pytest.raises(AttributeError):
            BankAccount("1", 100).balance = 1_000_000

    def test_transfer(self):
        # Arrange
        source, target = BankAccount("A", 300), SavingsAccount("B", 0)
        # Act
        ok = source.transfer(target, 120)
        refused = source.transfer(target, 1000)
        # Assert
        assert ok is True and refused is False
        assert source.balance == 180 and target.check_balance() == 120

    def test_savings_interest(self):
        livret = SavingsAccount("C", 2000, interest_rate=0.03)
        assert livret.add_interest() == pytest.approx(60)
        assert livret.check_balance() == pytest.approx(2060)
        assert isinstance(livret, BankAccount)
