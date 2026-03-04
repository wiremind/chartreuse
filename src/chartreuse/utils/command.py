import subprocess


def run_command(
    command: str,
    *,
    cwd: str | None = None,
    return_result: bool = False,
) -> tuple[str, str | None, int] | None:
    result = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        check=not return_result,
        capture_output=return_result,
        text=True,
    )

    if return_result:
        return result.stdout, result.stderr, result.returncode

    return None
