from __future__ import annotations

import argparse

from labtools import __version__, smoke_test
from labtools.cell_culture import (
    ImageJError,
    list_cell_imagej_experiments,
    run_cell_imagej_macro,
    write_cell_imagej_macro,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="BioMedPilot LabTools package.")
    parser.add_argument("--smoke-test", action="store_true", help="Import the public package surface and print a short status summary.")
    subparsers = parser.add_subparsers(dest="command")

    imagej_parser = subparsers.add_parser("cell-imagej", help="Generate or run ImageJ/Fiji macros for cell experiment images.")
    imagej_subparsers = imagej_parser.add_subparsers(dest="imagej_command", required=True)

    imagej_subparsers.add_parser("list", help="List supported cell experiment image workflows.")

    macro_parser = imagej_subparsers.add_parser("macro", help="Write an ImageJ macro without running ImageJ/Fiji.")
    _add_cell_imagej_common_args(macro_parser)
    macro_parser.add_argument("--macro-path", help="Optional macro output path. Defaults to <output-dir>/macros/<experiment>.ijm.")

    run_parser = imagej_subparsers.add_parser("run", help="Write and run an ImageJ/Fiji macro.")
    _add_cell_imagej_common_args(run_parser)
    run_parser.add_argument("--imagej", help="Path to ImageJ/Fiji executable or Fiji.app.")
    run_parser.add_argument("--macro-path", help="Optional macro output path. Defaults to <output-dir>/macros/<experiment>.ijm.")
    run_parser.add_argument("--timeout-seconds", type=int, default=600, help="ImageJ/Fiji process timeout in seconds.")

    args = parser.parse_args()

    if args.smoke_test:
        payload = smoke_test()
        print("labtools smoke test passed")
        print(f"version: {payload['version']}")
        print("modules:")
        for module_name in payload["modules"]:
            print(f"- {module_name}")
        return 0

    if args.command == "cell-imagej":
        return _handle_cell_imagej_command(args)

    parser.print_help()
    return 0


def _add_cell_imagej_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "experiment",
        choices=[spec.experiment_id for spec in list_cell_imagej_experiments()],
        help="Cell experiment image workflow.",
    )
    parser.add_argument("--input-dir", required=True, help="Input image directory.")
    parser.add_argument("--output-dir", required=True, help="Output directory for CSV results and generated macros.")
    parser.add_argument("--param", action="append", default=None, metavar="KEY=VALUE", help="Override ImageJ macro parameters.")


def _handle_cell_imagej_command(args: argparse.Namespace) -> int:
    if args.imagej_command == "list":
        for spec in list_cell_imagej_experiments():
            aliases = f" aliases={','.join(spec.aliases)}" if spec.aliases else ""
            print(f"{spec.experiment_id}: {spec.title}{aliases}")
            print(f"  {spec.description}")
        return 0

    if args.imagej_command == "macro":
        bundle = write_cell_imagej_macro(
            args.experiment,
            args.input_dir,
            args.output_dir,
            macro_path=args.macro_path,
            parameters=_parse_macro_parameters(args.param),
        )
        print(f"macro: {bundle.macro_path}")
        print(f"expected_csv: {bundle.output_csv_path}")
        return 0

    if args.imagej_command == "run":
        try:
            result = run_cell_imagej_macro(
                args.experiment,
                args.input_dir,
                args.output_dir,
                imagej_executable=args.imagej,
                macro_path=args.macro_path,
                parameters=_parse_macro_parameters(args.param),
                timeout_seconds=args.timeout_seconds,
            )
        except ImageJError as exc:
            print(f"ImageJ/Fiji 调用失败：{exc}")
            return 2
        print(f"macro: {result.macro_path}")
        print(f"expected_csv: {result.output_csv_path}")
        print(f"returncode: {result.returncode}")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode

    raise AssertionError(f"Unhandled cell-imagej command: {args.imagej_command}")


def _parse_macro_parameters(raw_values: list[str] | None) -> dict[str, str | int | float | bool]:
    parsed: dict[str, str | int | float | bool] = {}
    for raw_value in raw_values or ():
        if "=" not in raw_value:
            raise SystemExit(f"--param 必须使用 KEY=VALUE 格式：{raw_value}")
        key, value = raw_value.split("=", 1)
        key = key.strip()
        if not key:
            raise SystemExit("--param 的 KEY 不能为空")
        parsed[key] = _parse_macro_parameter_value(value.strip())
    return parsed


def _parse_macro_parameter_value(value: str) -> str | int | float | bool:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


if __name__ == "__main__":
    raise SystemExit(main())
