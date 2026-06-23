"""Generate a synthetic TDMS file and run the checker on it."""

from __future__ import annotations

from pathlib import Path

from create_synthetic_tdms import create_synthetic_tdms
from tdms_sync_checker.core import run_analysis


def main() -> None:
    example_dir = Path(__file__).resolve().parent
    tdms_path = create_synthetic_tdms(example_dir / "data" / "synthetic_tdms_reference.tdms")
    output_dir = example_dir / "outputs" / "synthetic_tdms_reference"

    _, excel_path, html_path, summary_text = run_analysis(tdms_path, output_dir)

    print(summary_text)
    print("")
    print(f"Excel report: {excel_path}")
    print(f"HTML report: {html_path}")


if __name__ == "__main__":
    main()
