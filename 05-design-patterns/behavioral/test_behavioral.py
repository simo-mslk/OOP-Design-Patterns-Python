import json

import pytest

from strategy_report import (CSVFormatStrategy, ExcelFormatStrategy, FormatStrategy, HTMLFormatStrategy,
                             JSONFormatStrategy, MarkdownFormatStrategy, PDFFormatStrategy, ReportGenerator)
from template_etl import APIPipeline, CSVPipeline, DatabasePipeline, DataPipeline, XMLPipeline

DATA = [{"name": "Sales Q1", "value": 15000}, {"name": "Sales Q2", "value": 18000}]


# ------------------------------------------------------------ strategy ---
# Each format can be tested ALONE now (question 3)
def test_csv_strategy():
    assert CSVFormatStrategy().render(DATA) == "name,value\nSales Q1,15000\nSales Q2,18000\n"


def test_json_strategy():
    assert json.loads(JSONFormatStrategy().render(DATA)) == DATA


def test_pdf_and_excel_keep_the_original_layout():
    assert PDFFormatStrategy().render(DATA).splitlines()[2] == "| Sales Q1             |      15000 |"
    assert "Sales Q2\t18000" in ExcelFormatStrategy().render(DATA)


def test_html_escapes_values():
    html = HTMLFormatStrategy().render([{"name": "<script>", "value": 1}])
    assert "&lt;script&gt;" in html and "<script>" not in html


def test_switch_strategy_at_runtime():
    generator = ReportGenerator(DATA, CSVFormatStrategy())
    first = generator.generate_report()
    generator.set_strategy(MarkdownFormatStrategy())
    assert generator.generate_report() != first
    assert generator.generate_report().startswith("| Name | Value |")


def test_no_strategy_gives_a_clear_error():
    with pytest.raises(RuntimeError, match="set_strategy"):
        ReportGenerator(DATA).generate_report()


@pytest.mark.parametrize("strategy", [PDFFormatStrategy(), ExcelFormatStrategy(), CSVFormatStrategy(),
                                      JSONFormatStrategy(), HTMLFormatStrategy()])
def test_save_uses_the_strategy_extension(tmp_path, strategy):
    path = ReportGenerator(DATA, strategy).save_report("sales", folder=tmp_path)
    assert path.suffix == "." + strategy.extension
    assert path.read_text(encoding="utf-8") == strategy.render(DATA)


def test_plugging_a_brand_new_format():
    class XMLFormatStrategy(FormatStrategy):
        extension = "xml"

        def render(self, data):
            return "<report>" + "".join(f"<row name='{r['name']}'>{r['value']}</row>" for r in data) + "</report>"

    assert ReportGenerator(DATA, XMLFormatStrategy()).generate_report().count("<row") == 2


# ----------------------------------------------------- template method ---
@pytest.fixture(autouse=True)
def no_waiting(monkeypatch):
    monkeypatch.setattr(DataPipeline, "latency", 0)


@pytest.mark.parametrize("pipeline_class, source", [
    (CSVPipeline, "users.csv"), (APIPipeline, "https://api"), (DatabasePipeline, "pg://db"),
    (XMLPipeline, "orders.xml"),
])
def test_every_pipeline_runs_the_same_steps_in_order(pipeline_class, source):
    pipeline = pipeline_class(source)
    result = pipeline.run()
    assert result.endswith("Pipeline finished")
    assert pipeline.steps_done == ["connect", "extract", "transform", "validate", "load", "cleanup"]
    assert pipeline.data is None                      # cleanup always happens


def test_transformations_are_specific(mocker):
    pipeline = APIPipeline("x")
    load = mocker.spy(pipeline, "load")
    captured = {}
    mocker.patch.object(pipeline, "cleanup", side_effect=lambda: captured.update(data=pipeline.data))
    pipeline.run()
    load.assert_called_once()
    assert [r["grade"] for r in captured["data"]] == ["B", "A"]


def test_xml_pipeline_hooks_and_output(capsys, mocker):
    pipeline = XMLPipeline("orders.xml")
    records = [pipeline.transform_record(r) for r in pipeline.extract()]
    assert records[0] == {"order_id": 9001, "customer": "Simo", "amount": 49.9, "currency": "EUR"}
    pipeline.run()
    out = capsys.readouterr().out
    assert out.index("[hook] checking") < out.index("Connecting") < out.index("[hook] moving")


def test_validation_stops_the_pipeline_before_loading():
    class BrokenCSV(CSVPipeline):
        def transform_record(self, record):
            return {"name": record["name"]}           # "id" lost

    pipeline = BrokenCSV("bad.csv")
    with pytest.raises(ValueError, match="missing"):
        pipeline.run()
    assert "load" not in pipeline.steps_done


def test_cannot_create_a_pipeline_without_the_required_steps():
    class Incomplete(DataPipeline):
        def extract(self):
            return []

    with pytest.raises(TypeError):
        Incomplete("x")
