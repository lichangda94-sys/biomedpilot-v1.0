from __future__ import annotations

from pathlib import Path

IMAGE_ANALYSIS_ENGINE_REQUIREMENT_IMAGEJ = "imagej"
IMAGE_ANALYSIS_ENGINE_REQUIREMENT_FIJI = "fiji"
IMAGE_ANALYSIS_ENGINE_REQUIREMENTS = (
    IMAGE_ANALYSIS_ENGINE_REQUIREMENT_IMAGEJ,
    IMAGE_ANALYSIS_ENGINE_REQUIREMENT_FIJI,
)


def build_imagej_fiji_macro_command(
    executable: str | Path,
    *,
    macro_path: str | Path,
    argument: str | Path = "",
    headless: bool = True,
    java_home: str | Path = "",
) -> list[str]:
    executable_path = Path(executable)
    if executable_path.suffix.lower() == ".jar":
        command = [_java_executable(java_home), "-jar", str(executable_path)]
        if headless:
            command.extend(["-batch", str(macro_path)])
        else:
            command.extend(["-macro", str(macro_path)])
        if str(argument):
            command.append(str(argument))
        return command

    command = [str(executable_path)]
    if str(java_home):
        command.append(f"--java-home={java_home}")
    if headless:
        command.append("--headless")
    command.extend(["-macro", str(macro_path)])
    if str(argument):
        command.append(str(argument))
    return command


def _java_executable(java_home: str | Path = "") -> str:
    if str(java_home):
        return str(Path(java_home) / "bin" / "java")
    return "java"
