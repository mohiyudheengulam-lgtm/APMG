import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "okf_walkthrough", Path(__file__).parents[1] / "scripts" / "okf_walkthrough.py"
)
walkthrough = importlib.util.module_from_spec(spec)
spec.loader.exec_module(walkthrough)


def test_resolve_source_accepts_package_name(monkeypatch, tmp_path):
    packages = tmp_path / "packages"
    package = packages / "PKG-001"
    package.mkdir(parents=True)
    (package / "invoice.pdf").touch()
    monkeypatch.setattr(walkthrough, "PACKAGES", packages)

    assert walkthrough.resolve_source("PKG-001") == package


def test_resolve_source_rejects_missing_folder(monkeypatch, tmp_path):
    monkeypatch.setattr(walkthrough, "PACKAGES", tmp_path / "packages")

    with pytest.raises(SystemExit, match="Package folder not found"):
        walkthrough.resolve_source("missing")


def test_resolve_source_rejects_folder_without_pdfs(tmp_path):
    package = tmp_path / "empty"
    package.mkdir()

    with pytest.raises(SystemExit, match="No PDF files found"):
        walkthrough.resolve_source(str(package))
