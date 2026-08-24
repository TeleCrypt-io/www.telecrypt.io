#!/usr/bin/env python3
"""Behavioral tests for bounded-command.py."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


HELPER = Path(__file__).with_name("bounded-command.py")


def run_helper(work: Path, *child_args: str, **limits: int) -> tuple[subprocess.CompletedProcess[str], int, int]:
    stdout = work / "stdout"
    stderr = work / "stderr"
    work.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            sys.executable,
            str(HELPER),
            "--stdout",
            str(stdout),
            "--stderr",
            str(stderr),
            "--max-stdout-bytes",
            str(limits.get("max_stdout", 65536)),
            "--max-stderr-bytes",
            str(limits.get("max_stderr", 65536)),
            "--timeout-seconds",
            "10",
            "--cwd",
            str(work),
            "--",
            sys.executable,
            "-c",
            *child_args,
        ],
        check=False,
        text=True,
    )
    return result, stdout.stat().st_size, stderr.stat().st_size


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        result, stdout_size, stderr_size = run_helper(
            work,
            "from pathlib import Path; Path('work.bin').write_bytes(b'x' * 131072); print('ok')",
        )
        assert result.returncode == 0, result
        assert (work / "work.bin").stat().st_size == 131072
        assert stdout_size <= 65536
        assert stderr_size == 0

        result, stdout_size, _ = run_helper(
            work,
            "import sys; sys.stdout.buffer.write(b'x' * 65537)",
        )
        assert result.returncode == 125, result
        assert stdout_size == 65536
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
