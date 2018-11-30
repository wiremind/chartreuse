# -*- coding: utf-8 -*-

import shlex
import subprocess


def run_command(command):
    """
    Run command, print stdout/stderr, check that command exited correctly, return stdout/err
    """
    print("Running %s" % command)
    process = subprocess.Popen(
        shlex.split(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    out, err = process.communicate()
    if out:
        print(out)
    if err:
        print(err)
    if process.returncode:
        raise subprocess.CalledProcessError(process.returncode, command)
    return (out, err)
