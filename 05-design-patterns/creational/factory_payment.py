"""Factory pattern - payment system refactor.

What is wrong with the original process_payment():
1. Open/Closed is violated: every new method (Apple Pay, crypto...) means editing the
   same if/elif chain, and a typo there can break the whole checkout.
2. Single Responsibility is violated: one function validates, computes fees and
   builds the response for every payment method.
3. Can't test one method alone, and the "Simulate processing" code is copy-pasted 3 times.
"""
from abc import ABC, abstractmethod
from typing import Callable, Dict, Type


class PaymentProcessor(ABC):
    """Interface: every processor 'promises' validate() and process()."""

    name: str = "abstract"

    @abstractmethod
    def validate(self, details: dict) -> bool:
        """Return True if the details are valid for this method."""

    @abstractmethod
    def fee(self, amount: float) -> float:
        """Fee charged by this method for `amount`."""

    def error_message(self) -> str:
        return f"Invalid {self.name} details"

    # Shared algorithm, written once for every method
    def process(self, amount: float, details: dict) -> dict:
        if amount <= 0:
            return {"success": False, "error": "Amount must be positive"}
        if not self.validate(details):
            return {"success": False, "error": self.error_message()}
        fee = round(self.fee(amount), 2)
        return {"success": True, "method": self.name, "amount": round(amount + fee, 2), "fee": fee}


class PaymentFactory:
    """Turns a string like "paypal" into the right processor object."""

    _registry: Dict[str, Type[PaymentProcessor]] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[Type[PaymentProcessor]], Type[PaymentProcessor]]:
        """Class decorator: @PaymentFactory.register("paypal") adds a processor to the factory.

        A new payment method is a new class + one decorator line: the factory itself
        is never edited again.
        """
        def decorator(processor_cls: Type[PaymentProcessor]) -> Type[PaymentProcessor]:
            processor_cls.name = name
            cls._registry[name] = processor_cls
            return processor_cls
        return decorator

    @classmethod
    def available_methods(cls) -> list:
        return sorted(cls._registry)

    def get_processor(self, payment_type: str) -> PaymentProcessor:
        processor_cls = self._registry.get(payment_type)
        if processor_cls is None:
            raise ValueError(f"Unknown payment type: {payment_type!r} "
                             f"(available: {', '.join(self.available_methods())})")
        return processor_cls()


@PaymentFactory.register("credit_card")
class CreditCardProcessor(PaymentProcessor):
    def validate(self, details: dict) -> bool:
        card = str(details.get("card_number", ""))
        cvv = str(details.get("cvv", ""))
        return len(card) == 16 and card.isdigit() and len(cvv) == 3 and cvv.isdigit()

    def error_message(self) -> str:
        return "Invalid card number or CVV"

    def fee(self, amount: float) -> float:
        return amount * 0.029                # 2.9 %


@PaymentFactory.register("bank_transfer")
class BankTransferProcessor(PaymentProcessor):
    def validate(self, details: dict) -> bool:
        return len(str(details.get("iban", ""))) >= 15

    def error_message(self) -> str:
        return "Invalid IBAN"

    def fee(self, amount: float) -> float:
        return 1.50                          # flat fee


@PaymentFactory.register("paypal")
class PayPalProcessor(PaymentProcessor):
    def validate(self, details: dict) -> bool:
        return "@" in str(details.get("email", ""))

    def error_message(self) -> str:
        return "Invalid PayPal email"

    def fee(self, amount: float) -> float:
        return amount * 0.034 + 0.30         # 3.4 % + 0.30 EUR


# ---- Extension test: the business wants crypto -> new class, nothing else touched
@PaymentFactory.register("crypto")
class CryptoProcessor(PaymentProcessor):
    def validate(self, details: dict) -> bool:
        wallet = str(details.get("wallet", ""))
        return wallet.startswith("0x") and len(wallet) == 42

    def error_message(self) -> str:
        return "Invalid wallet address"

    def fee(self, amount: float) -> float:
        return max(amount * 0.01, 2.0)       # 1 %, at least 2 EUR


if __name__ == "__main__":
    factory = PaymentFactory()

    processor = factory.get_processor("credit_card")
    print(processor.process(100.0, {"card_number": "1234567890123456", "cvv": "123"}))

    print(factory.get_processor("bank_transfer").process(100.0, {"iban": "FR7630006000011234567890189",
                                                                 "bic": "BNPAFRPP"}))
    print(factory.get_processor("paypal").process(100.0, {"email": "simo@example.com"}))
    print(factory.get_processor("crypto").process(100.0, {"wallet": "0x" + "ab" * 20}))
    print(factory.get_processor("paypal").process(100.0, {"email": "not-an-email"}))

    try:
        factory.get_processor("cheque")
    except ValueError as error:
        print(error)
