import logging
import shlex
import subprocess

logger = logging.getLogger(__name__)


def run_command(command: list | str, return_result: bool = False, **kw_args) -> tuple[str, str, int]:
    """
    Run command, print stdout/stderr, check that command exited correctly, return stdout/err
    """
    logger.debug(f"Running {command}")

    interpreted_command: list[str]
    if isinstance(command, str):
        interpreted_command = shlex.split(command)
    else:
        interpreted_command = command

    process = subprocess.Popen(
        interpreted_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        **kw_args,
    )

    if return_result:
        out, err = process.communicate()
        return (out, err, process.returncode)

    if process.stdout:
        for line in iter(process.stdout.readline, ""):
            logger.info(line.strip())
    process.wait()

    if process.returncode:
        raise subprocess.CalledProcessError(process.returncode, command)

    return "", "", 0
