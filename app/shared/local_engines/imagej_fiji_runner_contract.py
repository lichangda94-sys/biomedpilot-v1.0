from __future__ import annotations

from pathlib import Path


def build_imagej_fiji_macro_command(
    executable: str | Path,
    *,
    macro_path: str | Path,
    argument: str | Path = "",
    headless: bool = True,
) -> list[str]:
    command = [str(executable)]
    if headless:
        command.append("--headless")
    command.extend(["-macro", str(macro_path)])
    if str(argument):
        command.append(str(argument))
    return command
