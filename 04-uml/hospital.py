"""Hospital Management System - Python version of the Task 3 diagram in hospital.md."""
from __future__ import annotations

import hashlib
import itertools
import secrets
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class ProblemStatus(Enum):
    PENDING = "pending"
    IN_REVIEW = "in-review"
    RESOLVED = "resolved"


class PaymentStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    FORWARDED = "forwarded"


# Allowed status changes: anything else is a bug (or an attack)
PROBLEM_FLOW = {
    ProblemStatus.PENDING: {ProblemStatus.IN_REVIEW},
    ProblemStatus.IN_REVIEW: {ProblemStatus.RESOLVED},
    ProblemStatus.RESOLVED: set(),
}


# ------------------------------------------------------------------ users ---
class User(ABC):
    _next_id = itertools.count(1)

    def __init__(self, name: str, password: str):
        self.user_id = next(User._next_id)
        self.name = name
        self._salt = secrets.token_hex(8)
        self._password_hash = self._hash(password)
        self.is_logged_in = False

    def _hash(self, password: str) -> str:
        return hashlib.sha256((self._salt + password).encode()).hexdigest()

    def login(self, password: str) -> bool:
        self.is_logged_in = secrets.compare_digest(self._hash(password), self._password_hash)
        return self.is_logged_in

    def logout(self) -> None:
        self.is_logged_in = False

    @abstractmethod
    def role(self) -> str: ...

    def __repr__(self) -> str:
        return f"<{self.role()} #{self.user_id} {self.name}>"


class Patient(User):
    def __init__(self, name: str, password: str, email: str = ""):
        super().__init__(name, password)
        self.email = email
        self.problems: List[HealthProblem] = []

    def role(self) -> str:
        return "patient"

    def post_problem(self, description: str) -> HealthProblem:
        problem = HealthProblem(self, description)
        self.problems.append(problem)
        return problem

    def prescriptions(self) -> List[Prescription]:
        """Every prescription ever written for this patient, oldest first."""
        return sorted(
            (c.prescription for p in self.problems for c in p.consultations if c.prescription),
            key=lambda pr: pr.issued_at,
        )

    def pay(self, prescription: Prescription, method: PaymentMethod) -> Payment:
        if prescription.patient is not self:
            raise PermissionError("this prescription belongs to another patient")
        if prescription.sent_at is None:
            raise ValueError("the prescription has not been sent to you yet")
        if prescription.payment is not None:
            raise ValueError("this prescription is already paid")
        payment = Payment(prescription, method)
        payment.process()
        prescription.problem.move_to(ProblemStatus.RESOLVED)
        return payment


class Doctor(User):
    def __init__(self, name: str, password: str, speciality: str):
        super().__init__(name, password)
        self.speciality = speciality
        self.balance = 0.0

    def role(self) -> str:
        return "doctor"

    def write_prescription(self, consultation: Consultation, text: str, fee: float,
                           renewals: int = 0) -> Prescription:
        if consultation.doctor is not self:
            raise PermissionError("you are not the doctor of this consultation")
        history = consultation.problem.patient.prescriptions()
        prescription = Prescription(consultation, text, fee, renewals_left=renewals)
        prescription.previous = history[-1] if history else None   # link to the patient's last one
        consultation.prescription = prescription
        return prescription

    def receive_payment(self, amount: float) -> None:
        self.balance += amount


class Organizer(User):
    """Coordinates the workflow and is also the administrator of the platform."""

    def __init__(self, name: str, password: str):
        super().__init__(name, password)
        self.members: Dict[int, User] = {}

    def role(self) -> str:
        return "organizer"

    def register(self, role: str, name: str, **info):
        """Create a member and return (member, temporary password) to send to them."""
        temporary_password = secrets.token_urlsafe(8)
        roles = {"patient": Patient, "doctor": Doctor}
        if role not in roles:
            raise ValueError(f"unknown role {role!r}")
        member = roles[role](name, temporary_password, **info)
        self.members[member.user_id] = member
        return member, temporary_password

    def arrange_consultation(self, problem: HealthProblem, doctor: Doctor) -> Consultation:
        consultation = Consultation(problem, doctor)
        problem.consultations.append(consultation)
        if problem.status is ProblemStatus.PENDING:
            problem.move_to(ProblemStatus.IN_REVIEW)
        return consultation

    def send_prescription(self, prescription: Prescription) -> None:
        prescription.sent_at = datetime.now()

    def forward_payment(self, payment: Payment) -> None:
        if payment.status is not PaymentStatus.PAID:
            raise ValueError(f"can't forward a payment that is {payment.status.value}")
        payment.prescription.doctor.receive_payment(payment.amount)
        payment.status = PaymentStatus.FORWARDED
        payment.forwarded_at = datetime.now()


# ---------------------------------------------------------- medical data ---
class HealthProblem:
    _next_id = itertools.count(1)

    def __init__(self, patient: Patient, description: str):
        self.problem_id = next(HealthProblem._next_id)
        self.patient = patient
        self.description = description
        self.status = ProblemStatus.PENDING
        self.created_at = self.updated_at = datetime.now()
        self.consultations: List[Consultation] = []

    def move_to(self, status: ProblemStatus) -> None:
        if status not in PROBLEM_FLOW[self.status]:
            raise ValueError(f"{self.status.value} -> {status.value} is not allowed")
        self.status = status
        self.updated_at = datetime.now()


class Consultation:
    _next_id = itertools.count(1)

    def __init__(self, problem: HealthProblem, doctor: Doctor):
        self.consultation_id = next(Consultation._next_id)
        self.problem = problem
        self.doctor = doctor
        self.date = datetime.now()
        self.notes = ""
        self.prescription: Optional[Prescription] = None


class Prescription:
    _next_id = itertools.count(1)

    def __init__(self, consultation: Consultation, text: str, fee: float,
                 renewals_left: int = 0, renewal_of: Optional[Prescription] = None):
        if fee <= 0:
            raise ValueError("fee must be positive")
        self.prescription_id = next(Prescription._next_id)
        self.consultation = consultation
        self.text = text
        self.fee = fee
        self.renewals_left = renewals_left
        self.renewal_of = renewal_of
        self.previous: Optional[Prescription] = None
        self.issued_at = datetime.now()
        self.sent_at: Optional[datetime] = None
        self.payment: Optional[Payment] = None

    @property
    def problem(self) -> HealthProblem:
        return self.consultation.problem

    @property
    def patient(self) -> Patient:
        return self.problem.patient

    @property
    def doctor(self) -> Doctor:
        return self.consultation.doctor

    def renew(self) -> Prescription:
        """Reuse = a NEW prescription linked to this one (the original never changes)."""
        if self.renewals_left <= 0:
            raise ValueError("no renewal left on this prescription")
        self.renewals_left -= 1
        return Prescription(self.consultation, self.text, self.fee, 0, renewal_of=self)


# ------------------------------------------------- payments (strategy) ---
class PaymentMethod(ABC):
    @abstractmethod
    def charge(self, amount: float) -> str:
        """Take the money with this method and return a receipt line."""


class Check(PaymentMethod):
    def __init__(self, check_number: str, bank: str):
        self.check_number, self.bank = check_number, bank

    def charge(self, amount: float) -> str:
        return f"check n°{self.check_number} ({self.bank}) of {amount:.2f} EUR deposited"


class Cash(PaymentMethod):
    def charge(self, amount: float) -> str:
        return f"{amount:.2f} EUR received in cash"


class CreditCard(PaymentMethod):
    def __init__(self, card_number: str):
        digits = card_number.replace(" ", "")
        if not (digits.isdigit() and len(digits) == 16):
            raise ValueError("a card number has 16 digits")
        self._last4 = digits[-4:]     # never keep the full number

    def masked(self) -> str:
        return "**** **** **** " + self._last4

    def charge(self, amount: float) -> str:
        return f"card {self.masked()} charged {amount:.2f} EUR"


class Payment:
    _next_id = itertools.count(1)

    def __init__(self, prescription: Prescription, method: PaymentMethod):
        self.payment_id = next(Payment._next_id)
        self.prescription = prescription
        self.method = method
        self.amount = prescription.fee
        self.status = PaymentStatus.PENDING
        self.receipt = ""
        self.paid_at: Optional[datetime] = None
        self.forwarded_at: Optional[datetime] = None

    def process(self) -> str:
        if self.status is not PaymentStatus.PENDING:
            raise ValueError("payment already processed")
        self.receipt = self.method.charge(self.amount)   # polymorphic call
        self.status = PaymentStatus.PAID
        self.paid_at = datetime.now()
        self.prescription.payment = self
        return self.receipt


if __name__ == "__main__":
    admin = Organizer("Nadia (organizer)", "admin-pass")
    patient, patient_pwd = admin.register("patient", "Simo", email="simo@example.com")
    doctor, _ = admin.register("doctor", "Dr Benali", speciality="General practice")
    print("new members:", patient, doctor, "| patient can log in:", patient.login(patient_pwd))

    problem = patient.post_problem("Lower back pain for a week")
    consultation = admin.arrange_consultation(problem, doctor)
    print("status:", problem.status.value)

    prescription = doctor.write_prescription(consultation, "Ibuprofen 400mg + stretching", fee=30, renewals=1)
    admin.send_prescription(prescription)
    payment = patient.pay(prescription, CreditCard("4970 1234 5678 9012"))
    print(payment.receipt, "| status:", problem.status.value)

    admin.forward_payment(payment)
    print("payment", payment.status.value, "| doctor balance:", doctor.balance)

    refill = prescription.renew()
    print("renewal of prescription", refill.renewal_of.prescription_id, "| renewals left:", prescription.renewals_left)
