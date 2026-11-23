"""Strategy pattern - multi-format report generator refactor.

Problems to identify (my answers):
1. New format (XML, Markdown)? I must edit generate_report() AND save_report(): two
   if/elif chains to keep in sync, and an unknown format silently returns a string
   "Unknown format" (and save_report then writes nothing at all).
2. Principle violated: Open/Closed (the class must be modified to be extended),
   and Single Responsibility (one class knows every format + file writing).
3. Testability: bad. To test the CSV output I go through a method that contains the
   code of all the formats; I can't test or mock one format alone.
4. Change format at runtime: only by passing magic strings around; a typo ("exel")
   is only found when the code runs.
5. Duplication: the format name is tested twice, and the 4 `with open(...)` blocks
   are the same except for the extension.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from html import escape
from pathlib import Path
from typing import List, Optional

Rows = List[dict]


# ---------------------------------------------------------------- strategy ---
class FormatStrategy(ABC):
    """Contract shared by every format."""

    extension: str = "txt"

    @abstractmethod
    def render(self, data: Rows) -> str:
        """Turn the rows into the text of the report."""


class PDFFormatStrategy(FormatStrategy):
    extension = "pdf"

    def render(self, data: Rows) -> str:
        border = "=" * 50
        body = "".join(f"| {row['name']:20} | {row['value']:10} |\n" for row in data)
        return f"PDF REPORT\n{border}\n{body}{border}\nEnd of PDF Report"


class ExcelFormatStrategy(FormatStrategy):
    extension = "xlsx"

    def render(self, data: Rows) -> str:
        line = "-" * 50
        body = "".join(f"{row['name']}\t{row['value']}\n" for row in data)
        return f"EXCEL REPORT\n{line}\nName\tValue\n{body}{line}\n"


class CSVFormatStrategy(FormatStrategy):
    extension = "csv"

    def render(self, data: Rows) -> str:
        return "name,value\n" + "".join(f"{row['name']},{row['value']}\n" for row in data)


class JSONFormatStrategy(FormatStrategy):
    extension = "json"

    def render(self, data: Rows) -> str:
        return json.dumps(data, indent=2)


# --- added later, WITHOUT touching any class above --------------------------
class HTMLFormatStrategy(FormatStrategy):
    extension = "html"

    def render(self, data: Rows) -> str:
        rows = "".join(
            f"    <tr><td>{escape(str(row['name']))}</td><td>{escape(str(row['value']))}</td></tr>\n"
            for row in data
        )
        return ("<table>\n    <tr><th>Name</th><th>Value</th></tr>\n"
                f"{rows}</table>")


class MarkdownFormatStrategy(FormatStrategy):
    extension = "md"

    def render(self, data: Rows) -> str:
        rows = "".join(f"| {row['name']} | {row['value']} |\n" for row in data)
        return "| Name | Value |\n|---|---:|\n" + rows


# ----------------------------------------------------------------- context ---
class ReportGenerator:
    """Keeps the data, delegates the formatting to whatever strategy is plugged in."""

    def __init__(self, data: Rows, strategy: Optional[FormatStrategy] = None):
        self.data = data
        self._strategy = strategy

    def set_strategy(self, strategy: FormatStrategy) -> None:
        self._strategy = strategy

    def _current(self) -> FormatStrategy:
        if self._strategy is None:
            raise RuntimeError("choose a format first with set_strategy()")
        return self._strategy

    def generate_report(self) -> str:
        return self._current().render(self.data)

    def save_report(self, filename: str, folder: str = ".") -> Path:
        """One single save method: the extension comes from the strategy."""
        path = Path(folder) / f"{filename}.{self._current().extension}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.generate_report(), encoding="utf-8")
        return path


if __name__ == "__main__":
    data = [
        {"name": "Sales Q1", "value": 15000},
        {"name": "Sales Q2", "value": 18000},
        {"name": "Sales Q3", "value": 22000},
        {"name": "Sales Q4", "value": 25000},
    ]

    # Create report generator
    generator = ReportGenerator(data)

    # Generate PDF report
    print("=== PDF FORMAT ===")
    generator.set_strategy(PDFFormatStrategy())
    print(generator.generate_report())

    print("\n" + "=" * 60 + "\n")

    # Switch to CSV format dynamically
    print("=== CSV FORMAT ===")
    generator.set_strategy(CSVFormatStrategy())
    print(generator.generate_report())

    print("\n" + "=" * 60 + "\n")

    # Switch to JSON format
    print("=== JSON FORMAT ===")
    generator.set_strategy(JSONFormatStrategy())
    print(generator.generate_report())

    print("\n" + "=" * 60 + "\n")

    # NEW: HTML format added without modifying existing code
    print("=== HTML FORMAT (NEW!) ===")
    generator.set_strategy(HTMLFormatStrategy())
    print(generator.generate_report())

    # Save reports
    print("\n" + "=" * 60 + "\n")
    generator.set_strategy(CSVFormatStrategy())
    print("saved to", generator.save_report("sales_report", folder="output"))
