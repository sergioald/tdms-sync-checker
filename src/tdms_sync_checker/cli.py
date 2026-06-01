from __future__ import annotations

import argparse
from pathlib import Path

from .core import run_analysis


def main():
    parser = argparse.ArgumentParser(description="General TDMS Synchronisation Checker")
    parser.add_argument("--input", required=True, help="TDMS file or folder containing TDMS files")
    parser.add_argument("--output", required=True, help="Output folder")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)

    _, excel_path, html_path, _ = run_analysis(input_path, output_dir)

    print("Analysis complete.")
    print(f"Output folder: {output_dir}")
    print(f"Excel report: {excel_path}")
    print(f"HTML report: {html_path}")


if __name__ == "__main__":
    main()
