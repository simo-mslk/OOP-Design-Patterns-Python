"""Builder pattern - HR employee onboarding refactor.

Code smells of the original create_employee() (17 parameters):
- position dependency: forget one None and every following argument is shifted
- cognitive load: create_employee(..., False, True, True, True, ...) can't be read
- hidden logic: nothing guarantees that a developer gets a laptop + VPN, or that an
  intern never gets admin rights; it depends on who writes the call
- validation is done AFTER building the dict, mixed with the construction
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class Employee:
    """The product. frozen=True: once built, a record can't be modified by accident."""
    first_name: str
    last_name: str
    email: str
    department: str
    position: str
    salary: float
    start_date: date
    manager_id: Optional[int] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    has_parking: bool = False
    has_laptop: bool = False
    has_vpn_access: bool = False
    has_admin_rights: bool = False
    office_location: Optional[str] = None
    contract_type: str = "permanent"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


CONTRACT_TYPES = {"permanent", "fixed-term", "internship", "apprenticeship"}


class EmployeeBuilder:
    """Fluent builder: every with_* method stores a value and returns self."""

    def __init__(self) -> None:
        self._fields: dict = {"start_date": date.today()}

    # --- identity -----------------------------------------------------------
    def with_name(self, first_name: str, last_name: str) -> EmployeeBuilder:
        self._fields["first_name"] = first_name.strip()
        self._fields["last_name"] = last_name.strip()
        return self

    def with_email(self, email: str) -> EmployeeBuilder:
        self._fields["email"] = email.strip().lower()
        return self

    def with_contact(self, phone: Optional[str] = None, address: Optional[str] = None,
                     emergency_contact: Optional[str] = None) -> EmployeeBuilder:
        self._fields.update(phone=phone, address=address, emergency_contact=emergency_contact)
        return self

    # --- job ----------------------------------------------------------------
    def with_job(self, department: str, position: str, salary: float) -> EmployeeBuilder:
        self._fields.update(department=department, position=position, salary=salary)
        return self

    def starting_on(self, start_date: str) -> EmployeeBuilder:
        self._fields["start_date"] = date.fromisoformat(start_date)   # "2024-01-15"
        return self

    def reporting_to(self, manager_id: int) -> EmployeeBuilder:
        self._fields["manager_id"] = manager_id
        return self

    def with_contract(self, contract_type: str) -> EmployeeBuilder:
        self._fields["contract_type"] = contract_type
        return self

    # --- equipment & access -------------------------------------------------
    def with_equipment(self, laptop: bool = False, parking: bool = False) -> EmployeeBuilder:
        self._fields.update(has_laptop=laptop, has_parking=parking)
        return self

    def with_access(self, vpn: bool = False, admin: bool = False) -> EmployeeBuilder:
        self._fields.update(has_vpn_access=vpn, has_admin_rights=admin)
        return self

    def in_office(self, location: str) -> EmployeeBuilder:
        self._fields["office_location"] = location
        return self

    # --- final step ---------------------------------------------------------
    def _validate(self) -> None:
        f = self._fields
        missing = [k for k in ("first_name", "last_name", "email", "department", "position", "salary")
                   if not f.get(k) and f.get(k) != 0]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        if "@" not in f["email"] or "." not in f["email"].split("@")[-1]:
            raise ValueError("Valid email is required")
        if f["salary"] < 0:
            raise ValueError("Salary cannot be negative")
        if f.get("contract_type", "permanent") not in CONTRACT_TYPES:
            raise ValueError(f"Unknown contract type {f['contract_type']!r}")
        # Business rules that the 17-parameter function could not enforce
        if f.get("has_admin_rights") and f.get("contract_type") == "internship":
            raise ValueError("An intern can't have admin rights")
        if f.get("has_vpn_access") and not f.get("has_laptop"):
            raise ValueError("VPN access needs a company laptop")

    def build(self) -> Employee:
        self._validate()
        return Employee(**self._fields)


# Presets = builders that already know the usual configuration of a role.
# They are still builders, so a preset can be adjusted before build().
class DeveloperBuilder(EmployeeBuilder):
    def __init__(self, first_name: str, last_name: str, email: str,
                 position: str = "Software Developer", salary: float = 55_000):
        super().__init__()
        (self.with_name(first_name, last_name)
             .with_email(email)
             .with_job("Engineering", position, salary)
             .with_equipment(laptop=True)
             .with_access(vpn=True, admin=True)
             .in_office("Paris HQ"))


class InternBuilder(EmployeeBuilder):
    def __init__(self, first_name: str, last_name: str, email: str, department: str):
        super().__init__()
        (self.with_name(first_name, last_name)
             .with_email(email)
             .with_job(department, "Intern", 15_000)
             .with_equipment(laptop=True)
             .with_access(vpn=False, admin=False)
             .with_contract("internship")
             .in_office("Paris HQ"))


if __name__ == "__main__":
    employee = (
        EmployeeBuilder()
        .with_name("John", "Doe")
        .with_email("john.doe@company.com")
        .with_job("Engineering", "Senior Developer", 75000)
        .starting_on("2024-01-15")
        .with_contact(phone="+33612345678")
        .with_equipment(laptop=True, parking=False)
        .with_access(vpn=True, admin=True)
        .in_office("Paris HQ")
        .build()
    )
    print(employee)

    dev = DeveloperBuilder("John", "Doe", "john.doe@company.com").build()
    intern = (InternBuilder("Jane", "Smith", "jane.smith@company.com", "Marketing")
              .starting_on("2024-02-01")
              .reporting_to(42)
              .build())
    print(dev.full_name, dev.has_admin_rights, dev.has_vpn_access)
    print(intern.full_name, intern.contract_type, intern.manager_id)

    try:
        InternBuilder("Bad", "Idea", "bad@company.com", "IT").with_access(admin=True).build()
    except ValueError as error:
        print("refused:", error)
