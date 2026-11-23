import json
import threading

import pytest

from builder_employee import DeveloperBuilder, Employee, EmployeeBuilder, InternBuilder
from factory_payment import (BankTransferProcessor, CreditCardProcessor, PaymentFactory,
                             PaymentProcessor, PayPalProcessor)
import singleton_config
from singleton_config import ConfigManager

CARD = {"card_number": "1234567890123456", "cvv": "123"}


# ------------------------------------------------------------- factory ---
@pytest.mark.parametrize("name, expected_class", [
    ("credit_card", CreditCardProcessor),
    ("bank_transfer", BankTransferProcessor),
    ("paypal", PayPalProcessor),
])
def test_factory_maps_names_to_classes(name, expected_class):
    assert isinstance(PaymentFactory().get_processor(name), expected_class)


@pytest.mark.parametrize("method, details, fee", [
    ("credit_card", CARD, 2.90),
    ("bank_transfer", {"iban": "FR7630006000011234567890189"}, 1.50),
    ("paypal", {"email": "a@b.fr"}, 3.70),
])
def test_same_results_as_the_original_function(method, details, fee):
    result = PaymentFactory().get_processor(method).process(100.0, details)
    assert result == {"success": True, "method": method, "amount": 100.0 + fee, "fee": fee}


def test_invalid_details_and_unknown_method():
    factory = PaymentFactory()
    assert factory.get_processor("credit_card").process(100, {"card_number": "12"}) == {
        "success": False, "error": "Invalid card number or CVV"}
    with pytest.raises(ValueError, match="Unknown payment type"):
        factory.get_processor("bitcoin-cash")


def test_new_method_registered_without_editing_the_factory():
    @PaymentFactory.register("gift_card")
    class GiftCardProcessor(PaymentProcessor):
        def validate(self, details):
            return details.get("code", "").startswith("GC-")

        def fee(self, amount):
            return 0

    result = PaymentFactory().get_processor("gift_card").process(50, {"code": "GC-42"})
    assert result["success"] and result["method"] == "gift_card"
    del PaymentFactory._registry["gift_card"]     # don't leak into other tests


# ------------------------------------------------------------- builder ---
def test_fluent_builder_from_the_statement():
    employee = (EmployeeBuilder()
                .with_name("John", "Doe")
                .with_email("john.doe@company.com")
                .with_job("Engineering", "Senior Developer", 75000)
                .with_equipment(laptop=True, parking=False)
                .with_access(vpn=True, admin=True)
                .build())
    assert isinstance(employee, Employee)
    assert employee.has_admin_rights and employee.has_laptop and not employee.has_parking


def test_presets():
    dev = DeveloperBuilder("John", "Doe", "john.doe@company.com").build()
    intern = InternBuilder("Jane", "Smith", "jane.smith@company.com", "Marketing").reporting_to(42).build()
    assert (dev.department, dev.has_vpn_access, dev.has_admin_rights) == ("Engineering", True, True)
    assert (intern.contract_type, intern.has_admin_rights, intern.manager_id) == ("internship", False, 42)


def test_product_is_immutable():
    dev = DeveloperBuilder("J", "D", "j@d.com").build()
    with pytest.raises(AttributeError):
        dev.salary = 1_000_000


@pytest.mark.parametrize("broken_builder, message", [
    (lambda: EmployeeBuilder().with_email("a@b.com").with_job("IT", "Dev", 1), "first_name"),
    (lambda: DeveloperBuilder("J", "D", "not-an-email"), "email"),
    (lambda: DeveloperBuilder("J", "D", "j@d.com", salary=-1), "negative"),
    (lambda: InternBuilder("J", "D", "j@d.com", "IT").with_access(admin=True), "intern"),
    (lambda: DeveloperBuilder("J", "D", "j@d.com").with_equipment(laptop=False), "laptop"),
    (lambda: DeveloperBuilder("J", "D", "j@d.com").with_contract("freelance"), "contract"),
])
def test_validation_happens_in_build(broken_builder, message):
    with pytest.raises(ValueError, match=message):
        broken_builder().build()


# ----------------------------------------------------------- singleton ---
@pytest.fixture
def config_file(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"database": {"host": "db.test", "port": 6543}, "app": {"debug": True}}))
    ConfigManager._reset_for_tests()
    yield path
    ConfigManager._reset_for_tests()


def test_one_instance_one_file_read(config_file):
    first = ConfigManager(config_file)
    assert ConfigManager.get_instance() is first is ConfigManager()
    assert first.load_count == 1


def test_dotted_get_and_default(config_file):
    config = ConfigManager(config_file)
    assert config.get("database.host") == "db.test"
    assert config.get("database.port") == 6543
    assert config.get("database.user", "admin") == "admin"
    assert config.get("app.debug.level") is None       # going "inside" a bool


def test_changes_are_shared(config_file):
    ConfigManager(config_file).set("app.debug", False)
    assert ConfigManager.get_instance().get("app.debug") is False


def test_thread_safe_creation(config_file, monkeypatch):
    monkeypatch.setattr(singleton_config, "CONFIG_FILE", config_file)
    instances = []                    # 20 threads race to create the first instance
    threads = [threading.Thread(target=lambda: instances.append(ConfigManager.get_instance()))
               for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len({id(i) for i in instances}) == 1
