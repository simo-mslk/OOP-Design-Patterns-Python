# Exercise 1 - Hospital Management System 🏥

Statement: https://gist.github.com/bdallard/2d2407c4de4c182afca6d3ec7235e9eb (slide 68) · Code: [`hospital.py`](hospital.py)

Workflow to model: patient posts a problem → organizer arranges a consultation → doctor gives a prescription → organizer sends it to the patient → patient pays (check, cash or card) → organizer forwards the money to the doctor. The organizer is also the administrator (creates members, ids, passwords).

## Basic architecture - Task 1: class diagram

Who talks to whom: the patient only deals with the organizer (posts problems, receives prescriptions, pays), the organizer deals with the doctors, and the doctor treats patients through the organizer.

```mermaid
classDiagram
    class Patient {
        -patient_id: int
        -name: str
        -password: str
        -email: str
        +post_problem(description)
        +view_prescriptions() list
        +pay(amount, method)
    }
    class Organizer {
        -organizer_id: int
        -name: str
        -password: str
        +create_member(role, name) int
        +arrange_consultation(problem, doctor)
        +send_prescription(patient)
        +forward_payment(doctor, amount)
    }
    class Doctor {
        -doctor_id: int
        -name: str
        -password: str
        -speciality: str
        +review_problem(problem)
        +write_prescription(problem) str
        +receive_payment(amount)
    }

    Organizer "1" -- "0..*" Patient : registers and serves
    Organizer "1" -- "1..*" Doctor : coordinates
    Doctor "0..*" -- "0..*" Patient : treats
```

## Develop the system - Task 2: extended class diagram

Six classes: Patient, Doctor, Organizer + HealthProblem, Prescription, Payment.

- **Composition** `Patient *-- HealthProblem`: a problem is part of the patient's file and has no meaning without the patient.
- **Composition** `HealthProblem *-- Prescription`: a prescription is the answer to one problem.
- **Inheritance** for the payment types (`CheckPayment`, `CashPayment`, `CreditCardPayment`), because each type has its own data (check number, card number).

```mermaid
classDiagram
    class Patient {
        -patient_id: int
        -name: str
        -password: str
        +post_problem(description) HealthProblem
        +pay(prescription, payment)
    }
    class Doctor {
        -doctor_id: int
        -name: str
        -speciality: str
        +write_prescription(problem, text, fee) Prescription
        +receive_payment(amount)
    }
    class Organizer {
        -organizer_id: int
        -name: str
        +arrange_consultation(problem, doctor)
        +send_prescription(prescription)
        +forward_payment(payment)
    }
    class HealthProblem {
        -problem_id: int
        -description: str
        -status: str
    }
    class Prescription {
        -prescription_id: int
        -text: str
        -fee: float
    }
    class Payment {
        <<abstract>>
        -amount: float
        +process() str*
    }
    class CheckPayment {
        -check_number: str
    }
    class CashPayment
    class CreditCardPayment {
        -card_number: str
    }

    Payment <|-- CheckPayment
    Payment <|-- CashPayment
    Payment <|-- CreditCardPayment
    Patient "1" *-- "0..*" HealthProblem : owns
    HealthProblem "1" *-- "0..1" Prescription : answered by
    Doctor "1" --> "0..*" Prescription : writes
    Organizer "1" --> "0..*" HealthProblem : handles
    Patient "1" --> "0..*" Payment : makes
    Payment "0..1" --> "1" Prescription : pays for
```

### Task 2: sequence diagram - one patient submits a problem, gets a prescription and pays

```mermaid
sequenceDiagram
    autonumber
    actor P as Patient
    participant HP as HealthProblem
    actor O as Organizer
    actor D as Doctor
    participant Pay as CreditCardPayment

    P->>HP: post_problem("back pain")
    HP-->>O: new problem to handle
    O->>D: arrange_consultation(problem)
    D->>D: review the problem
    D-->>O: write_prescription(problem, text, fee)
    O->>P: send_prescription(prescription)
    P->>Pay: pay(prescription, card)
    Pay-->>P: receipt
    O->>D: forward_payment(payment)
    D-->>O: payment received
```

## Advanced - Task 3

Refinements I added:

- `User` abstract superclass with the shared attributes (`id`, `name`, password hash) and `login()` / `logout()`.
- **Strategy with composition** for payments: a `Payment` is the record (amount, status, timestamps) and it *has* a `PaymentMethod` (`Check`, `Cash`, `CreditCard`). Each method implements `charge()` differently, so the code that handles a payment never does `if method == "check"`.
- `ProblemStatus` (PENDING → IN_REVIEW → RESOLVED) and `PaymentStatus` (PENDING → PAID → FORWARDED) enums.
- Timestamps on problems, prescriptions and payments, and `renewal_of` on a prescription to point to a past prescription.
- `Consultation` between `HealthProblem` and `Doctor` so one problem can be seen by several doctors (question 1).

```mermaid
classDiagram
    class User {
        <<abstract>>
        #user_id: int
        #name: str
        #password_hash: str
        #is_logged_in: bool
        +login(password) bool
        +logout()
        +role()* str
    }
    class Patient {
        -problems: list~HealthProblem~
        +post_problem(description) HealthProblem
        +prescriptions() list~Prescription~
        +pay(prescription, method) Payment
    }
    class Doctor {
        -speciality: str
        -balance: float
        +write_prescription(consultation, text, fee) Prescription
        +receive_payment(amount)
    }
    class Organizer {
        -members: dict~int, User~
        +register(role, name, ...) tuple
        +arrange_consultation(problem, doctor) Consultation
        +send_prescription(prescription)
        +forward_payment(payment)
    }
    class HealthProblem {
        -problem_id: int
        -description: str
        -status: ProblemStatus
        -created_at: datetime
        -updated_at: datetime
        +move_to(status)
    }
    class Consultation {
        -consultation_id: int
        -date: datetime
        -notes: str
    }
    class Prescription {
        -prescription_id: int
        -text: str
        -fee: float
        -issued_at: datetime
        -sent_at: datetime
        -renewals_left: int
        -renewal_of: Prescription
        +renew() Prescription
    }
    class Payment {
        -payment_id: int
        -amount: float
        -status: PaymentStatus
        -paid_at: datetime
        -forwarded_at: datetime
    }
    class PaymentMethod {
        <<abstract>>
        +charge(amount)* str
    }
    class Check {
        -check_number: str
        -bank: str
    }
    class Cash
    class CreditCard {
        -card_number: str
        +masked() str
    }
    class ProblemStatus {
        <<enumeration>>
        PENDING
        IN_REVIEW
        RESOLVED
    }
    class PaymentStatus {
        <<enumeration>>
        PENDING
        PAID
        FORWARDED
    }

    User <|-- Patient
    User <|-- Doctor
    User <|-- Organizer
    PaymentMethod <|-- Check
    PaymentMethod <|-- Cash
    PaymentMethod <|-- CreditCard

    Organizer "1" o-- "0..*" User : manages
    Patient "1" *-- "0..*" HealthProblem : owns
    HealthProblem "1" *-- "0..*" Consultation : discussed in
    Consultation "0..*" --> "1" Doctor : with
    Consultation "1" *-- "0..1" Prescription : results in
    Prescription "0..1" --> "0..1" Prescription : renewal_of
    Payment "0..1" --> "1" Prescription : pays for
    Payment "1" --> "1" PaymentMethod : uses
    HealthProblem --> ProblemStatus
    Payment --> PaymentStatus
```

### System sequence diagrams

In a system sequence diagram the system is a black box: only the actors and `:System`, with the messages they exchange.

#### 1. Patient registration (the organizer creates a new member)

```mermaid
sequenceDiagram
    actor O as Organizer
    participant S as :System
    actor P as New patient

    O->>S: login(name, password)
    S-->>O: welcome
    O->>S: register("patient", name, email)
    S->>S: create id + temporary password, store the hash
    S-->>O: patient_id, temporary password
    O-->>P: sends id and temporary password
    P->>S: login(patient_id, temporary password)
    S-->>P: welcome
```

#### 2. Consultation flow (problem submitted → prescription delivered)

```mermaid
sequenceDiagram
    actor P as Patient
    participant S as :System
    actor O as Organizer
    actor D as Doctor

    P->>S: post_problem(description)
    S-->>P: problem_id, status PENDING
    O->>S: arrange_consultation(problem_id, doctor_id)
    S-->>D: new consultation
    S-->>P: status IN_REVIEW
    D->>S: write_prescription(consultation_id, text, fee)
    S-->>O: prescription ready
    O->>S: send_prescription(prescription_id)
    S-->>P: prescription + amount to pay
```

#### 3. Payment processing (patient pays, organizer forwards to the doctor)

```mermaid
sequenceDiagram
    actor P as Patient
    participant S as :System
    actor O as Organizer
    actor D as Doctor

    P->>S: pay(prescription_id, method)
    alt amount and method are valid
        S-->>P: receipt, payment PAID, problem RESOLVED
        O->>S: forward_payment(payment_id)
        S-->>D: amount credited
        S-->>O: payment FORWARDED
    else refused (wrong amount, bad card, already paid)
        S-->>P: error, nothing is charged
    end
```

## Questions to consider

1. **A patient consulting multiple doctors?** Different problems can already go to different doctors. For the same problem (second opinion, specialist), I put a `Consultation` class between `HealthProblem` and `Doctor`: one problem has `0..*` consultations and each consultation is with one doctor, so it is a many-to-many relation with its own data (date, notes, prescription).
2. **Should prescriptions be reusable?** A prescription should not be edited once it is sent (it's a medical and billing record). For a treatment that must be repeated, the doctor sets `renewals_left`, and `renew()` creates a **new** prescription that points to the old one with `renewal_of`. We get reuse and a complete history.
3. **Which design pattern for the payment system?** **Strategy**: `Payment` delegates to a `PaymentMethod` object and each method (`Check`, `Cash`, `CreditCard`) implements `charge()`. Adding PayPal = one new class, nothing else changes (Open/Closed). A small **Factory** can build the right method from the form value ("check", "cash", "card").
4. **Data integrity when payments are processed?**
   - a status machine: a payment can only go PENDING → PAID → FORWARDED, so it can't be paid twice or forwarded before being paid
   - the amount is checked against the prescription fee before charging
   - in a real database, "mark as paid" and "credit the doctor" run in one **transaction** (both or nothing)
   - an idempotency key / unique constraint on (prescription, payment) so a double click does not create two payments
   - timestamps for every step (audit trail), and card numbers are never stored in clear (only the last 4 digits)
