import json

import pytest

from adapter_report import (AnalyticsDashboard, LegacyReportAdapter, LegacyReportGenerator,
                            ReportGeneratorInterface, show_report)
from decorator_order import (BaseOrder, DiscountDecorator, ExpressShippingDecorator, GiftWrapDecorator,
                             InsuranceDecorator, OrderComponent, PremiumMemberDecorator)


# ------------------------------------------------------------- adapter ---
@pytest.fixture
def adapter():
    return LegacyReportAdapter(LegacyReportGenerator())


def test_adapter_is_a_report_generator(adapter):
    assert isinstance(adapter, ReportGeneratorInterface)


@pytest.mark.parametrize("data", [
    {"total_sales": 150000, "orders": 1234, "avg_order": 121.55},
    {"total_items": 5000, "low_stock": 45, "out_of_stock": 12},
    {"region": "Casablanca", "growth": -2.5},
])
def test_json_really_comes_from_the_xml(adapter, data):
    assert json.loads(adapter.generate(data)) == data      # types are restored too


def test_adapter_calls_the_legacy_system(mocker):
    legacy = LegacyReportGenerator()
    spy = mocker.spy(legacy, "generate_report")
    LegacyReportAdapter(legacy).generate({"a": 1})
    spy.assert_called_once_with({"a": 1})


def test_dashboard_output(adapter, capsys):
    show_report(adapter, AnalyticsDashboard(), {"orders": 1234})
    assert "orders: 1234" in capsys.readouterr().out


# ----------------------------------------------------------- decorator ---
def original_calculate_total(base, express=False, insurance=False, gift=False, discount=0, premium=False):
    """Copy of the spaghetti logic, used as the reference for the refactor."""
    total = base
    total += 15 if express else 0
    total += base * 0.05 if insurance else 0
    total += 5 if gift else 0
    total -= total * discount / 100 if discount else 0
    total -= total * 0.10 if premium else 0
    return total


def test_full_chain_matches_original_code():
    order = PremiumMemberDecorator(DiscountDecorator(GiftWrapDecorator(InsuranceDecorator(
        ExpressShippingDecorator(BaseOrder(100.00)))), percent=15))
    expected = original_calculate_total(100, True, True, True, 15, True)
    assert order.get_cost() == pytest.approx(expected) == pytest.approx(95.625)


def test_insurance_is_on_the_item_price_wherever_it_is_wrapped():
    early = InsuranceDecorator(BaseOrder(200))
    late = InsuranceDecorator(GiftWrapDecorator(ExpressShippingDecorator(BaseOrder(200))))
    assert early.get_cost() - 200 == pytest.approx(10)
    assert late.get_cost() - 220 == pytest.approx(10)


def test_order_of_decorators_is_the_order_of_operations():
    discount_last = DiscountDecorator(ExpressShippingDecorator(BaseOrder(100)), percent=10)
    discount_first = ExpressShippingDecorator(DiscountDecorator(BaseOrder(100), percent=10))
    assert discount_last.get_cost() == pytest.approx(103.5)
    assert discount_first.get_cost() == pytest.approx(105)


def test_description_lists_every_option():
    order = PremiumMemberDecorator(GiftWrapDecorator(BaseOrder(50)))
    assert order.get_description().splitlines() == [
        "Base price: 50.00€", "Gift wrap: +5.00€", "Premium member (10%): -5.50€"]
    assert isinstance(order, OrderComponent)


def test_invalid_discount():
    with pytest.raises(ValueError):
        DiscountDecorator(BaseOrder(10), percent=150)
