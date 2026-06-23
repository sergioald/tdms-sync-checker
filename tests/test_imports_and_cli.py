from __future__ import annotations

import sys

import pytest


def test_package_imports():
    import tdms_sync_checker

    assert hasattr(tdms_sync_checker, "__version__")


def test_core_and_gui_modules_import():
    import tdms_sync_checker.core
    import tdms_sync_checker.gui

    assert tdms_sync_checker.core is not None
    assert tdms_sync_checker.gui is not None


def test_cli_help_runs_without_tdms_input(monkeypatch, capsys):
    from tdms_sync_checker.cli import main

    monkeypatch.setattr(sys, "argv", ["tdms-sync-checker", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    captured = capsys.readouterr()

    assert exc_info.value.code == 0
    assert "General TDMS Synchronisation Checker" in captured.out
    assert "--input" in captured.out
    assert "--output" in captured.out
