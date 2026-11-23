"""Template Method pattern - data ETL pipelines refactor.

Problems to identify (my answers):
1. Validation logic: repeated 3 times (only the 2 required keys change).
2. Cleanup logic: repeated 3 times, exactly the same lines.
3. Add logging to all pipelines: edit the 3 run() methods, and the next pipeline
   someone writes will probably forget it.
4. Workflow order changes (e.g. validate BEFORE transform): same thing, 3 places to edit,
   and nothing forces a pipeline to keep the right order or not skip a step.
5. Duplication: in each ~45-line run(), only extract + transform (~10 lines) are really
   specific. About 3/4 of the code is copied, so roughly 70 duplicated lines in total.
"""
from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import List, Sequence

Records = List[dict]


class DataPipeline(ABC):
    """Skeleton of every ETL job. Subclasses fill in the blanks, never the order."""

    label = "Generic"                     # used in the messages ("CSV file", "API"...)
    required_fields: Sequence[str] = ()
    latency = 0.5                         # fake network/disk time (set to 0 in the tests)

    def __init__(self, source: str):
        self.source = source
        self.data: Records | None = None
        self.steps_done: List[str] = []   # small audit trail, filled by _step()

    # ------------------------------------------------ the template method ---
    def run(self) -> str:
        """Final workflow, the same for everybody. Subclasses should not override it."""
        self.on_start()
        self._step("connect", self.connect)
        self._step("extract", self._extract_step)
        self._step("transform", self._transform_step)
        self._step("validate", self.validate)
        self._step("load", self.load)
        self._step("cleanup", self.cleanup)
        self.on_finish()
        return f"{self.name()} Pipeline finished"

    def _step(self, name: str, action) -> None:
        # One place to add logging, timing, retries... for ALL pipelines (question 3)
        action()
        self.steps_done.append(name)

    def _extract_step(self) -> None:
        print(f"Extracting data from {self.name()}...")
        self.data = self.extract()
        print(f"Extracted {len(self.data)} records")

    def _transform_step(self) -> None:
        print(f"Transforming {self.name()} data...")
        self.data = [self.transform_record(dict(record)) for record in self.data]
        print("Transformation complete")

    # ---------------------------------------------- abstract steps (required) ---
    @abstractmethod
    def extract(self) -> Records:
        """Read the raw records from the source."""

    @abstractmethod
    def transform_record(self, record: dict) -> dict:
        """Clean / enrich ONE record."""

    # -------------------------------------------- common steps (written once) ---
    def name(self) -> str:
        return self.label.split()[0]

    def connect(self) -> None:
        print(f"Connecting to {self.label}: {self.source}")
        time.sleep(self.latency)
        print(f"{self.name()} connection established")

    def validate(self) -> None:
        print("Validating data...")
        for record in self.data:
            missing = [field for field in self.required_fields if field not in record]
            if missing:
                raise ValueError(f"Invalid record structure, missing {missing}: {record}")
        print("Validation passed")

    def load(self) -> None:
        print("Loading data to destination...")
        time.sleep(self.latency)
        print(f"Loaded {len(self.data)} records successfully")

    def cleanup(self) -> None:
        print("Cleaning up resources...")
        self.data = None
        print("Cleanup complete")

    # ------------------------------------------- hooks (optional, empty here) ---
    def on_start(self) -> None:
        """Called before the first step."""

    def on_finish(self) -> None:
        """Called after the last step."""


class CSVPipeline(DataPipeline):
    label = "CSV file"
    required_fields = ("id", "name")

    def extract(self) -> Records:
        return [{"id": 1, "name": "Alice", "age": 30}, {"id": 2, "name": "Bob", "age": 25}]

    def transform_record(self, record: dict) -> dict:
        record["age"] = int(record["age"])
        record["name"] = record["name"].upper()
        return record


class APIPipeline(DataPipeline):
    label = "API"
    required_fields = ("user_id", "username")

    def extract(self) -> Records:
        return [{"user_id": 101, "username": "charlie", "score": 85},
                {"user_id": 102, "username": "diana", "score": 92}]

    def transform_record(self, record: dict) -> dict:
        record["score"] = int(record["score"])
        record["username"] = record["username"].lower()
        record["grade"] = "A" if record["score"] >= 90 else "B"
        return record


class DatabasePipeline(DataPipeline):
    label = "database"
    required_fields = ("product_id", "price")

    def name(self) -> str:
        return "Database"

    def extract(self) -> Records:
        return [{"product_id": 501, "product_name": "Laptop", "price": 1200},
                {"product_id": 502, "product_name": "Mouse", "price": 25}]

    def transform_record(self, record: dict) -> dict:
        record["price"] = float(record["price"])
        record["product_name"] = record["product_name"].title()
        record["tax"] = record["price"] * 0.2
        return record


# ---- Validation of the design: a 4th source, only the specific parts are written
class XMLPipeline(DataPipeline):
    label = "XML file"
    required_fields = ("order_id", "customer", "amount")

    RAW = """<orders>
      <order id="9001"><customer>simo</customer><amount>49.90</amount><currency>EUR</currency></order>
      <order id="9002"><customer>yasmine</customer><amount>120</amount><currency>EUR</currency></order>
    </orders>"""

    def extract(self) -> Records:
        root = ET.fromstring(self.RAW)
        return [{"order_id": order.get("id"), **{child.tag: child.text for child in order}}
                for order in root.iter("order")]

    def transform_record(self, record: dict) -> dict:
        return {"order_id": int(record["order_id"]),
                "customer": record["customer"].title(),
                "amount": round(float(record["amount"]), 2),
                "currency": record["currency"]}

    # hooks used only by this pipeline
    def on_start(self) -> None:
        print(f"[hook] checking that {self.source} is well-formed XML")
        ET.fromstring(self.RAW)

    def on_finish(self) -> None:
        print(f"[hook] moving {self.source} to archive/")


if __name__ == "__main__":
    for title, pipeline in [
        ("CSV", CSVPipeline("data/users.csv")),
        ("API", APIPipeline("https://api.example.com/users")),
        ("DATABASE", DatabasePipeline("postgresql://localhost/mydb")),
        ("XML (NEW!)", XMLPipeline("data/orders.xml")),
    ]:
        print(f"RUNNING {title} PIPELINE")
        print("=" * 70)
        result = pipeline.run()
        print(f"\n{result}\n")
