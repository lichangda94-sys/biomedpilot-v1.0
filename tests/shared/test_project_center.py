from __future__ import annotations

from app.shared.project_center.service import ProjectCenter


def test_project_center_create_and_list(tmp_path) -> None:
    center = ProjectCenter(tmp_path / "projects.json")
    created = center.create_project(project_name="demo", project_type="bioinformatics")
    records = center.list_projects()
    assert records == [created]
    assert records[0].project_id.startswith("bio-")
    assert records[0].project_name == "demo"
    assert records[0].project_type == "bioinformatics"
    assert records[0].project_dir
    assert records[0].status == "active"


def test_project_center_reads_recent_and_gets_project(tmp_path) -> None:
    center = ProjectCenter(tmp_path / "projects.json")
    first = center.create_project(project_name="bio demo", project_type="bioinformatics")
    second = center.create_project(project_name="meta demo", project_type="meta_analysis")
    assert center.recent_projects(limit=1) == [second]
    assert center.get_project(first.project_id) == first
    assert center.get_project("missing") is None
