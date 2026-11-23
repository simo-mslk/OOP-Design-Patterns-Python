"""Tests: the code follows the diagrams and the business rules of both exercises."""
import pytest

import abcd_records as abcd
import hospital as h


# ================================================================ hospital ===
@pytest.fixture
def platform():
    admin = h.Organizer("Admin", "admin")
    patient, pwd = admin.register("patient", "Simo", email="s@example.com")
    doctor, _ = admin.register("doctor", "Dr B", speciality="GP")
    return admin, patient, pwd, doctor


def treat(admin, patient, doctor, description="fever", fee=30.0, **kw):
    """Run the workflow until the prescription is sent to the patient."""
    problem = patient.post_problem(description)
    consultation = admin.arrange_consultation(problem, doctor)
    prescription = doctor.write_prescription(consultation, "rest", fee, **kw)
    admin.send_prescription(prescription)
    return problem, prescription


def test_registration_and_login(platform):
    admin, patient, pwd, doctor = platform
    assert patient.login(pwd) and not patient.login("wrong")
    assert set(admin.members) == {patient.user_id, doctor.user_id}
    with pytest.raises(ValueError):
        admin.register("pharmacist", "X")


def test_full_workflow_with_statuses(platform):
    admin, patient, _, doctor = platform
    problem = patient.post_problem("back pain")
    assert problem.status is h.ProblemStatus.PENDING
    consultation = admin.arrange_consultation(problem, doctor)
    assert problem.status is h.ProblemStatus.IN_REVIEW

    prescription = doctor.write_prescription(consultation, "stretching", 25)
    admin.send_prescription(prescription)
    payment = patient.pay(prescription, h.Cash())
    assert payment.status is h.PaymentStatus.PAID
    assert problem.status is h.ProblemStatus.RESOLVED

    admin.forward_payment(payment)
    assert payment.status is h.PaymentStatus.FORWARDED and doctor.balance == 25


def test_payment_integrity(platform):
    admin, patient, _, doctor = platform
    problem = patient.post_problem("cough")
    consultation = admin.arrange_consultation(problem, doctor)
    prescription = doctor.write_prescription(consultation, "syrup", 20)
    with pytest.raises(ValueError):          # not sent yet
        patient.pay(prescription, h.Cash())
    admin.send_prescription(prescription)
    payment = patient.pay(prescription, h.Check("123", "BNP"))
    with pytest.raises(ValueError):          # paid twice
        patient.pay(prescription, h.Cash())
    admin.forward_payment(payment)
    with pytest.raises(ValueError):          # forwarded twice
        admin.forward_payment(payment)
    assert doctor.balance == 20


def test_only_the_assigned_doctor_can_prescribe(platform):
    admin, patient, _, doctor = platform
    other, _ = admin.register("doctor", "Dr C", speciality="ENT")
    consultation = admin.arrange_consultation(patient.post_problem("ear"), doctor)
    with pytest.raises(PermissionError):
        other.write_prescription(consultation, "drops", 10)


def test_second_opinion_and_history(platform):
    admin, patient, _, doctor = platform
    specialist, _ = admin.register("doctor", "Dr D", speciality="Cardiology")
    problem, first = treat(admin, patient, doctor, "chest pain")
    second_opinion = admin.arrange_consultation(problem, specialist)
    second = specialist.write_prescription(second_opinion, "ECG", 50)
    assert [c.doctor for c in problem.consultations] == [doctor, specialist]
    assert second.previous is first


def test_renewal_creates_a_linked_prescription(platform):
    admin, patient, _, doctor = platform
    _, original = treat(admin, patient, doctor, renewals=1)
    refill = original.renew()
    assert refill.renewal_of is original and refill is not original
    with pytest.raises(ValueError):
        original.renew()


@pytest.mark.parametrize("method", [h.Cash(), h.Check("1", "LCL"), h.CreditCard("1234 5678 9012 3456")])
def test_every_payment_method_is_polymorphic(method):
    assert "10.00" in method.charge(10)


def test_card_number_is_never_stored():
    card = h.CreditCard("1234567812345678")
    assert card.masked().endswith("5678")
    assert "12345678" not in str(vars(card))


# ============================================================ ABCD Records ===
@pytest.fixture
def shop():
    clerk = abcd.OrderProcessingClerk(abcd.DailyRecordsFile())
    in_stock = abcd.CD("1", "Thriller", "MJ", 14.0, quantity_in_stock=2)
    out_of_stock = abcd.CD("2", "Kind of Blue", "Miles Davis", 16.0, quantity_in_stock=0)
    return clerk, in_stock, out_of_stock


def test_royal_scenario_two_cds_one_unavailable_paid_by_check(shop):
    clerk, thriller, blue = shop
    royal = abcd.RoyalMember("Simo", "Cergy")

    order, invoice, shipping = clerk.process_order(royal, [(thriller, 1), (blue, 1)])

    assert [l.status for l in order.lines] == [abcd.LineStatus.IN_STOCK, abcd.LineStatus.BACKORDERED]
    assert invoice.amount_due == pytest.approx(25.5)          # 30 - 15%
    assert [l.item for l in shipping.lines] == [thriller] and shipping.priority
    assert thriller.quantity_in_stock == 1
    receipt = abcd.CollectionDepartmentClerk().collect(invoice, abcd.Check(25.5, "77", "CIH"))
    assert "check 77" in receipt and order.status is abcd.OrderStatus.PAID
    assert clerk.records.orders == [order]


def test_regular_member_cannot_backorder(shop):
    clerk, thriller, blue = shop
    regular = abcd.RegularMember("Ali", "Rabat")
    order, invoice, _ = clerk.process_order(regular, [(thriller, 1), (blue, 1)])
    assert [l.item for l in order.lines] == [thriller]
    assert invoice.amount_due == pytest.approx(13.3)          # 14 - 5%
    with pytest.raises(ValueError):
        clerk.process_order(regular, [(blue, 1)])


def test_non_member_gets_an_application(shop):
    clerk, thriller, _ = shop
    visitor = abcd.NonMember("Ines", "Lyon")
    assert clerk.verify_membership(visitor) is False
    assert clerk.send_membership_application(visitor).applicant is visitor
    with pytest.raises(PermissionError):
        clerk.process_order(visitor, [(thriller, 1)])


def test_backorders_are_shipped_when_the_supplier_delivers(shop):
    clerk, _, blue = shop
    first, _, _ = clerk.process_order(abcd.RoyalMember("R1", "x"), [(blue, 1)])
    second, _, _ = clerk.process_order(abcd.RoyalMember("R2", "y"), [(blue, 2)])
    assert len(clerk.reorders.pending()) == 2

    served = clerk.reorders.receive_delivery(blue, 2)       # only 2 CDs arrive

    assert served == first.lines                            # first come, first served
    assert served[0].status is abcd.LineStatus.IN_STOCK
    assert clerk.reorders.pending() == second.lines and blue.quantity_in_stock == 1


@pytest.mark.parametrize("payment", [abcd.Cash(30), abcd.Check(30, "1", "BMCE"), abcd.BankDraft(30, "D9", "SG")])
def test_all_payment_types_accepted(shop, payment):
    clerk, thriller, _ = shop
    _, invoice, _ = clerk.process_order(abcd.RegularMember("A", "B"), [(thriller, 2)])
    assert abcd.CollectionDepartmentClerk().collect(invoice, payment).startswith("received")


def test_payment_too_low_is_rejected(shop):
    clerk, thriller, _ = shop
    _, invoice, _ = clerk.process_order(abcd.RegularMember("A", "B"), [(thriller, 1)])
    with pytest.raises(ValueError):
        abcd.CollectionDepartmentClerk().collect(invoice, abcd.Cash(1))
    assert not invoice.paid


def test_daily_records_export(shop):
    clerk, thriller, _ = shop
    member = abcd.RegularMember("A", "B")
    clerk.process_order(member, [(thriller, 1)])
    lines = clerk.records.export().splitlines()
    assert lines[0] == "order,member,total,status" and member.member_number in lines[1]
