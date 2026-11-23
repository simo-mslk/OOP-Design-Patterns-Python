"""OOP problems - part 2: inheritance.

Statement: https://gist.github.com/bdallard/b2f2c910e3a9b564a30c86991c97b4fc
"""
from __future__ import annotations


# --------------------------------------------------------------------------
# Problem 1 - Vehicle, Car, Bicycle (method overriding)
# --------------------------------------------------------------------------
class Vehicle:
    def drive(self) -> str:
        return "Driving a vehicle"


class Car(Vehicle):
    def drive(self) -> str:          # overrides Vehicle.drive
        return "Driving a car"


class Bicycle(Vehicle):
    def drive(self) -> str:
        return "Riding a bicycle"


# --------------------------------------------------------------------------
# Problem 2 - Person, Student, Employee
# --------------------------------------------------------------------------
class Person:
    def __init__(self, name: str, age: int, address: str):
        self.name = name
        self.age = age
        self.address = address

    def introduce(self) -> str:
        return f"Hello, my name is {self.name}, I am {self.age} years old and I live in {self.address}."


class Student(Person):
    def __init__(self, name: str, age: int, address: str, field_of_study: str):
        super().__init__(name, age, address)     # the parent sets name/age/address
        self.field_of_study = field_of_study

    def introduce(self) -> str:
        # reuse the parent's sentence and add the student part
        return super().introduce() + f" I am a student in {self.field_of_study}."


class Employee(Person):
    def __init__(self, name: str, age: int, address: str, company: str):
        super().__init__(name, age, address)
        self.company = company

    def introduce(self) -> str:
        return super().introduce() + f" I am working for {self.company}."


# --------------------------------------------------------------------------
# Problem 3 - BankAccount and SavingsAccount
# --------------------------------------------------------------------------
class BankAccount:
    def __init__(self, account_number: str, balance: float = 0.0):
        if balance < 0:
            raise ValueError("initial balance can't be negative")
        self.account_number = account_number
        self._balance = balance      # "protected": only changed through the methods

    @property
    def balance(self) -> float:
        """Read-only from outside: account.balance = 1e6 raises AttributeError."""
        return self._balance

    @staticmethod
    def _check_amount(amount: float) -> None:
        if amount <= 0:
            raise ValueError("amount must be strictly positive")

    def deposit(self, amount: float) -> float:
        self._check_amount(amount)
        self._balance += amount
        return self._balance

    def withdraw(self, amount: float) -> float:
        self._check_amount(amount)
        if amount > self._balance:
            raise ValueError(f"insufficient funds on {self.account_number}")
        self._balance -= amount
        return self._balance

    def transfer(self, destination: BankAccount, amount: float) -> bool:
        """Send `amount` to `destination`: False if the balance is too low, True otherwise."""
        self._check_amount(amount)
        if amount > self._balance:
            return False
        self.withdraw(amount)
        destination.deposit(amount)
        return True

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.account_number!r}, balance={self._balance:.2f})"


class SavingsAccount(BankAccount):
    def __init__(self, account_number: str, balance: float = 0.0, interest_rate: float = 0.03):
        super().__init__(account_number, balance)
        if not 0 <= interest_rate <= 1:
            raise ValueError("interest_rate is a fraction, e.g. 0.03 for 3%")
        self.interest_rate = interest_rate

    def add_interest(self) -> float:
        """Credit one period of interest and return the amount added."""
        interest = round(self._balance * self.interest_rate, 2)
        self._balance += interest
        return interest

    def check_balance(self) -> float:
        return self._balance


if __name__ == "__main__":
    # Polymorphism: same call, the right method is chosen at runtime
    for vehicle in [Vehicle(), Car(), Bicycle()]:
        print(f"{type(vehicle).__name__:8} -> {vehicle.drive()}")

    people = [
        Person("Simo", 21, "Cergy"),
        Student("Yasmine", 19, "Casablanca", "Data Science"),
        Employee("Karim", 32, "Paris", "Capgemini"),
    ]
    for person in people:
        print(person.introduce())

    current = BankAccount("FR76-0001", 300)
    livret = SavingsAccount("FR76-0002", 2000, interest_rate=0.03)
    print(current.transfer(livret, 120))     # True
    print(current.transfer(livret, 1000))    # False: only 180 left
    print("interest:", livret.add_interest())  # 63.6
    print(current, livret, sep="\n")
