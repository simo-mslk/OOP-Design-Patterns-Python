"""Decorator pattern - order pricing refactor.

Problems of the original calculate_total():
- boolean flag explosion: 5 flags today, one more parameter for every new option
- one method does everything (Single Responsibility violated)
- a new option means editing the method (Open/Closed violated)
- the options can't be reused elsewhere (insurance logic is stuck in the method)
- the order of operations is hidden: is the discount applied before or after shipping?
"""
from abc import ABC, abstractmethod


class OrderComponent(ABC):
    @abstractmethod
    def get_cost(self) -> float: ...

    @abstractmethod
    def get_description(self) -> str: ...

    @property
    @abstractmethod
    def base_price(self) -> float:
        """Price of the item itself, needed by options computed on it (insurance)."""


class BaseOrder(OrderComponent):
    def __init__(self, base_price: float):
        if base_price < 0:
            raise ValueError("price can't be negative")
        self._base_price = base_price

    @property
    def base_price(self) -> float:
        return self._base_price

    def get_cost(self) -> float:
        return self._base_price

    def get_description(self) -> str:
        return f"Base price: {self._base_price:.2f}€"


class OrderDecorator(OrderComponent):
    """Wraps an order. Subclasses only say how much they change the cost and how to label it."""

    def __init__(self, order: OrderComponent):
        self._wrapped = order

    @property
    def base_price(self) -> float:
        return self._wrapped.base_price

    @abstractmethod
    def adjustment(self) -> float:
        """Amount added to the wrapped cost (negative for a discount)."""

    @abstractmethod
    def label(self) -> str: ...

    def get_cost(self) -> float:
        return self._wrapped.get_cost() + self.adjustment()

    def get_description(self) -> str:
        amount = self.adjustment()
        sign = "+" if amount >= 0 else "-"
        return f"{self._wrapped.get_description()}\n{self.label()}: {sign}{abs(amount):.2f}€"


class ExpressShippingDecorator(OrderDecorator):
    PRICE = 15.00

    def adjustment(self) -> float:
        return self.PRICE

    def label(self) -> str:
        return "Express shipping"


class InsuranceDecorator(OrderDecorator):
    RATE = 0.05

    def adjustment(self) -> float:
        # 5% of the item price (like the original code), wherever it is in the chain
        return self.base_price * self.RATE

    def label(self) -> str:
        return "Insurance (5%)"


class GiftWrapDecorator(OrderDecorator):
    PRICE = 5.00

    def adjustment(self) -> float:
        return self.PRICE

    def label(self) -> str:
        return "Gift wrap"


class DiscountDecorator(OrderDecorator):
    def __init__(self, order: OrderComponent, percent: float):
        super().__init__(order)
        if not 0 < percent < 100:
            raise ValueError("percent must be between 0 and 100")
        self.percent = percent

    def adjustment(self) -> float:
        # applied on everything wrapped so far: the position in the chain matters
        return -self._wrapped.get_cost() * self.percent / 100

    def label(self) -> str:
        return f"Discount ({self.percent:g}%)"


class PremiumMemberDecorator(DiscountDecorator):
    """A premium member is just a fixed 10% discount: reuse DiscountDecorator."""

    def __init__(self, order: OrderComponent):
        super().__init__(order, percent=10)

    def label(self) -> str:
        return "Premium member (10%)"


def print_order(order: OrderComponent) -> None:
    print(order.get_description())
    print(f"TOTAL: {order.get_cost():.2f}€")


if __name__ == "__main__":
    # Simple order
    print_order(BaseOrder(100.00))
    print("\n---\n")

    # Build order with decorators - readable and flexible.
    # The wrapping order IS the order of operations: shipping, insurance and gift wrap
    # are added first, then the 15% discount, then the premium 10% on what is left.
    order = BaseOrder(100.00)
    order = ExpressShippingDecorator(order)
    order = InsuranceDecorator(order)
    order = GiftWrapDecorator(order)
    order = DiscountDecorator(order, percent=15)
    order = PremiumMemberDecorator(order)
    print_order(order)                      # (100 + 15 + 5 + 5) * 0.85 * 0.90 = 95.625

    print("\n---\n")
    # Same options, discount first: the customer pays more for shipping/wrap
    other = GiftWrapDecorator(ExpressShippingDecorator(DiscountDecorator(BaseOrder(100.00), percent=15)))
    print_order(other)                      # 100 * 0.85 + 15 + 5 = 105.00
