"""ABCD Records - Python version of the Level 2 class diagram in abcd_records.md."""
from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from collections import deque
from datetime import date
from enum import Enum
from typing import Deque, List, Optional, Tuple


class LineStatus(Enum):
    IN_STOCK = "in stock"
    BACKORDERED = "backordered"


class OrderStatus(Enum):
    PROCESSED = "processed"
    PAID = "paid"


# -------------------------------------------------------------- customers ---
class Customer(ABC):
    def __init__(self, name: str, address: str):
        self.name = name
        self.address = address


class NonMember(Customer):
    pass


class MembershipApplication:
    def __init__(self, applicant: NonMember):
        self.applicant = applicant
        self.sent_on = date.today()
        self.accepted = False


class Member(Customer, ABC):
    _numbers = itertools.count(1001)

    def __init__(self, name: str, address: str):
        super().__init__(name, address)
        self.member_number = f"M{next(Member._numbers)}"
        self.joined_on = date.today()
        self.orders: List[Order] = []

    @abstractmethod
    def discount_rate(self) -> float: ...

    @abstractmethod
    def can_order_unavailable(self) -> bool: ...

    @abstractmethod
    def has_priority(self) -> bool: ...


class RoyalMember(Member):
    def discount_rate(self) -> float:
        return 0.15

    def can_order_unavailable(self) -> bool:
        return True

    def has_priority(self) -> bool:
        return True


class RegularMember(Member):
    def discount_rate(self) -> float:
        return 0.05

    def can_order_unavailable(self) -> bool:
        return False

    def has_priority(self) -> bool:
        return False


# ------------------------------------------------------------------ items ---
class Item(ABC):
    def __init__(self, catalog_number: str, title: str, artist: str,
                 unit_price: float, quantity_in_stock: int = 0):
        self.catalog_number = catalog_number
        self.title = title
        self.artist = artist
        self.unit_price = unit_price
        self.quantity_in_stock = quantity_in_stock

    def is_available(self, quantity: int) -> bool:
        return self.quantity_in_stock >= quantity

    def reserve(self, quantity: int) -> None:
        if not self.is_available(quantity):
            raise ValueError(f"only {self.quantity_in_stock} '{self.title}' left")
        self.quantity_in_stock -= quantity

    def restock(self, quantity: int) -> None:
        self.quantity_in_stock += quantity

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.title!r})"


class CD(Item):
    def __init__(self, *args, number_of_tracks: int = 10, **kwargs):
        super().__init__(*args, **kwargs)
        self.number_of_tracks = number_of_tracks


class Tape(Item):
    def __init__(self, *args, length_minutes: int = 60, **kwargs):
        super().__init__(*args, **kwargs)
        self.length_minutes = length_minutes


# ----------------------------------------------------------------- orders ---
class OrderLine:
    def __init__(self, item: Item, quantity: int, status: LineStatus):
        self.item = item
        self.quantity = quantity
        self.status = status

    def amount(self) -> float:
        return self.item.unit_price * self.quantity


class Order:
    _numbers = itertools.count(1)

    def __init__(self, member: Member):
        self.order_number = next(Order._numbers)
        self.member = member
        self.order_date = date.today()
        self.status = OrderStatus.PROCESSED
        self.lines: List[OrderLine] = []          # composition

    def add_line(self, item: Item, quantity: int, status: LineStatus) -> OrderLine:
        line = OrderLine(item, quantity, status)
        self.lines.append(line)
        return line

    def gross_amount(self) -> float:
        return sum(line.amount() for line in self.lines)

    def discount(self) -> float:
        return round(self.gross_amount() * self.member.discount_rate(), 2)

    def total(self) -> float:
        return round(self.gross_amount() - self.discount(), 2)


class Invoice:
    _numbers = itertools.count(1)

    def __init__(self, order: Order):
        self.invoice_number = next(Invoice._numbers)
        self.order = order
        self.amount_due = order.total()
        self.paid = False

    def render(self) -> str:
        rows = [f"INVOICE #{self.invoice_number} - order {self.order.order_number} - {self.order.member.name}"]
        rows += [f"  {l.quantity} x {l.item.title:<22} {l.amount():7.2f}  ({l.status.value})"
                 for l in self.order.lines]
        rows.append(f"  discount {self.order.member.discount_rate():.0%}: -{self.order.discount():.2f}")
        rows.append(f"  TOTAL DUE: {self.amount_due:.2f} EUR")
        return "\n".join(rows)


class ShippingList:
    def __init__(self, order: Order):
        self.order = order
        self.lines = [l for l in order.lines if l.status is LineStatus.IN_STOCK]
        self.priority = order.member.has_priority()

    def render(self) -> str:
        flag = "PRIORITY " if self.priority else ""
        items = ", ".join(f"{l.quantity} x {l.item.title}" for l in self.lines) or "nothing yet"
        return f"{flag}SHIPPING to {self.order.member.address}: {items}"


# --------------------------------------------------------------- payments ---
class Payment(ABC):
    def __init__(self, amount: float):
        if amount <= 0:
            raise ValueError("amount must be positive")
        self.amount = amount
        self.received_on = date.today()

    @abstractmethod
    def describe(self) -> str: ...


class Cash(Payment):
    def describe(self) -> str:
        return f"cash {self.amount:.2f} EUR"


class Check(Payment):
    def __init__(self, amount: float, check_number: str, bank_name: str):
        super().__init__(amount)
        self.check_number = check_number
        self.bank_name = bank_name

    def describe(self) -> str:
        return f"check {self.check_number} ({self.bank_name}) {self.amount:.2f} EUR"


class BankDraft(Payment):
    def __init__(self, amount: float, draft_number: str, issuing_bank: str):
        super().__init__(amount)
        self.draft_number = draft_number
        self.issuing_bank = issuing_bank

    def describe(self) -> str:
        return f"bank draft {self.draft_number} ({self.issuing_bank}) {self.amount:.2f} EUR"


# ---------------------------------------------------------- staff & files ---
class DailyRecordsFile:
    def __init__(self, day: Optional[date] = None):
        self.day = day or date.today()
        self.orders: List[Order] = []

    def record(self, order: Order) -> None:
        self.orders.append(order)

    def export(self) -> str:
        """One CSV line per order, what the company would archive every evening."""
        header = "order,member,total,status"
        rows = [f"{o.order_number},{o.member.member_number},{o.total():.2f},{o.status.value}"
                for o in self.orders]
        return "\n".join([header, *rows])


class ReorderList:
    """Backordered lines (Royal privilege) waiting for the supplier, first come first served."""

    def __init__(self):
        self._queue: Deque[OrderLine] = deque()

    def add(self, line: OrderLine) -> None:
        self._queue.append(line)

    def pending(self) -> List[OrderLine]:
        return list(self._queue)

    def receive_delivery(self, item: Item, quantity: int) -> List[OrderLine]:
        """Supplier delivery: restock, then serve the waiting lines for this item in order."""
        item.restock(quantity)
        served = []
        for line in list(self._queue):
            if line.item is item and item.is_available(line.quantity):
                item.reserve(line.quantity)
                line.status = LineStatus.IN_STOCK
                self._queue.remove(line)
                served.append(line)
        return served


class OrderProcessingClerk:
    def __init__(self, records: DailyRecordsFile, reorders: Optional[ReorderList] = None):
        self.records = records
        self.reorders = reorders or ReorderList()

    def verify_membership(self, customer: Customer) -> bool:
        return isinstance(customer, Member)

    def send_membership_application(self, customer: NonMember) -> MembershipApplication:
        return MembershipApplication(customer)

    def process_order(self, member: Member,
                      wishlist: List[Tuple[Item, int]]) -> Tuple[Order, Invoice, ShippingList]:
        if not self.verify_membership(member):
            raise PermissionError("only members can order")
        order = Order(member)
        for item, quantity in wishlist:
            if item.is_available(quantity):
                item.reserve(quantity)
                order.add_line(item, quantity, LineStatus.IN_STOCK)
            elif member.can_order_unavailable():
                line = order.add_line(item, quantity, LineStatus.BACKORDERED)
                self.reorders.add(line)
            # a regular member can't order an unavailable item: the line is dropped
        if not order.lines:
            raise ValueError("none of the requested items can be ordered")
        member.orders.append(order)
        self.records.record(order)
        return order, Invoice(order), ShippingList(order)


class CollectionDepartmentClerk:
    def collect(self, invoice: Invoice, payment: Payment) -> str:
        if invoice.paid:
            raise ValueError("invoice already paid")
        if payment.amount < invoice.amount_due:
            raise ValueError(f"{payment.amount:.2f} does not cover {invoice.amount_due:.2f}")
        invoice.paid = True
        invoice.order.status = OrderStatus.PAID
        return "received " + payment.describe()


if __name__ == "__main__":
    records = DailyRecordsFile()
    order_clerk = OrderProcessingClerk(records)
    collection_clerk = CollectionDepartmentClerk()

    thriller = CD("CD-0042", "Thriller", "Michael Jackson", 14.0, quantity_in_stock=5)
    kind_of_blue = CD("CD-0107", "Kind of Blue", "Miles Davis", 16.0, quantity_in_stock=0)

    # Scenario: a Royal member orders 2 CDs (one unavailable) and pays by check
    royal = RoyalMember("Simo", "12 rue des Arts, Cergy")
    order, invoice, shipping = order_clerk.process_order(royal, [(thriller, 1), (kind_of_blue, 1)])
    print(invoice.render())       # (14 + 16) * 0.85 = 25.50
    print(shipping.render())      # only Thriller now, priority
    print(collection_clerk.collect(invoice, Check(invoice.amount_due, "0007731", "Attijariwafa")))
    print("waiting for the supplier:", [l.item.title for l in order_clerk.reorders.pending()])
    shipped_later = order_clerk.reorders.receive_delivery(kind_of_blue, 3)
    print("after the delivery, shipped:", [l.item.title for l in shipped_later])

    # A non-member gets an application form instead of an order
    visitor = NonMember("Ines", "Lyon")
    if not order_clerk.verify_membership(visitor):
        form = order_clerk.send_membership_application(visitor)
        print(f"application form sent to {form.applicant.name} on {form.sent_on}")

    print(records.export())
