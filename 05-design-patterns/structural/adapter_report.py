"""Adapter pattern - plug the legacy XML report generator into the JSON dashboard.

Problems of the original code:
- incompatible interfaces: the legacy library returns XML, the dashboard wants JSON
- the conversion is repeated in every show_*_report() function
- and it is not even a real conversion: json.dumps(report_data) re-uses the original
  dict, the XML produced by the legacy system is thrown away
- we can't change the legacy class (external library)
- business code (which report to show) is mixed with format code (XML -> JSON)
"""
import json
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod


# Legacy reporting system (can't modify - external library)
class LegacyReportGenerator:
    def generate_report(self, data: dict) -> str:
        """Returns XML format - old system"""
        xml = "<report>\n"
        for key, value in data.items():
            xml += f"  <{key}>{value}</{key}>\n"
        xml += "</report>"
        return xml


# New analytics dashboard expects JSON
class AnalyticsDashboard:
    def display(self, json_data: str):
        data = json.loads(json_data)
        print("=== Analytics Dashboard ===")
        for key, value in data.items():
            print(f"  {key}: {value}")


# ---------------------------------------------------------------- target ---
class ReportGeneratorInterface(ABC):
    """What the new code expects from any report generator."""

    @abstractmethod
    def generate(self, data: dict) -> str:
        """Return the report as a JSON string."""


# --------------------------------------------------------------- adapter ---
class LegacyReportAdapter(ReportGeneratorInterface):
    """Object adapter: HAS a LegacyReportGenerator and translates its output."""

    def __init__(self, legacy_generator: LegacyReportGenerator):
        self._adaptee = legacy_generator

    def generate(self, data: dict) -> str:
        xml_report = self._adaptee.generate_report(data)     # 1. ask the old system
        return json.dumps(self.xml_to_dict(xml_report))      # 2. translate the answer

    @staticmethod
    def xml_to_dict(xml_report: str) -> dict:
        root = ET.fromstring(xml_report)
        return {element.tag: LegacyReportAdapter._restore_type(element.text) for element in root}

    @staticmethod
    def _restore_type(text):
        """XML only stores text: "1234" -> 1234, "121.55" -> 121.55, "Paris" stays a string."""
        text = (text or "").strip()
        try:
            return json.loads(text)        # numbers (and true/false/null) come back typed
        except json.JSONDecodeError:
            return text


# ---------------------------------------------------- business code only ---
def show_report(generator: ReportGeneratorInterface, dashboard: AnalyticsDashboard, data: dict) -> None:
    """Knows nothing about XML: it just asks for JSON."""
    dashboard.display(generator.generate(data))


def show_sales_report(generator, dashboard):
    show_report(generator, dashboard, {"total_sales": 150000, "orders": 1234, "avg_order": 121.55})


def show_inventory_report(generator, dashboard):
    show_report(generator, dashboard, {"total_items": 5000, "low_stock": 45, "out_of_stock": 12})


if __name__ == "__main__":
    # Adapter wraps the legacy system
    report_generator = LegacyReportAdapter(LegacyReportGenerator())
    dashboard = AnalyticsDashboard()

    # Dashboard doesn't know it's talking to a legacy system
    json_report = report_generator.generate({"total_sales": 150000, "orders": 1234})
    dashboard.display(json_report)

    show_sales_report(report_generator, dashboard)
    show_inventory_report(report_generator, dashboard)
