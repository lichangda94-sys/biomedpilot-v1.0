from __future__ import annotations

import sys

import pytest

QtWidgets = pytest.importorskip("PySide6.QtWidgets")
QApplication = QtWidgets.QApplication

from app.bioinformatics.pages.geo_import_page import GeoImportPage, initial_geo_import_state


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication(sys.argv)
    return app


def test_bioinformatics_data_source_scope_has_no_literature_copy() -> None:
    state = initial_geo_import_state()

    assert state.description == "检索范围：GEO/GSE、TCGA/GDC、GTEx、本地数据。"
    assert "PubMed" not in state.description
    assert "Meta" not in state.description
    assert "CNKI" not in state.description


def test_geo_import_page_shows_disease_aware_tables(qt_app) -> None:
    page = GeoImportPage(project_id="ui-test")
    page._query_input.setText("脑胶质瘤")
    page._create_plan()

    assert "脑胶质瘤" in page._summary_label.text()
    assert page._geo_query_table.rowCount() > 0
    assert page._tcga_table.rowCount() >= 2
    assert page._gtex_table.rowCount() >= 1
    assert page._source_candidate_table.rowCount() >= 3
    assert page._tcga_table.item(0, 0).text() != "TCGA"
    page_text = " ".join(
        [
            page._summary_label.text(),
            page._status_label.text(),
            page._geo_query_table.item(0, 0).text(),
        ]
    )
    assert "PubMed" not in page_text
    assert "Meta" not in page_text
