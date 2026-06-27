from pathlib import Path

import pytest

from lithic.tools.shell import CommandError, _is_destructive, run


def test_run_echo() -> None:
    result = run(["echo", "hello"], Path.cwd())
    assert "hello" in result


def test_run_failing_command() -> None:
    with pytest.raises(CommandError):
        run(["python", "-c", "exit(1)"], Path.cwd())


def test_run_destructive_rm() -> None:
    with pytest.raises(CommandError, match="destructive"):
        run(["rm", "-rf", "/"], Path.cwd())


def test_run_destructive_rm_exe() -> None:
    with pytest.raises(CommandError, match="destructive"):
        run(["rm.exe", "-rf", "/"], Path.cwd())


def test_run_destructive_rd() -> None:
    with pytest.raises(CommandError, match="destructive"):
        run(["rd", "/s", "/q", "."], Path.cwd())


def test_run_destructive_deltree() -> None:
    with pytest.raises(CommandError, match="destructive"):
        run(["deltree", "."], Path.cwd())


def test_run_destructive_git_reset() -> None:
    with pytest.raises(CommandError, match="destructive"):
        run(["git", "reset", "--hard"], Path.cwd())


def test_run_destructive_drop_table() -> None:
    with pytest.raises(CommandError, match="destructive"):
        run(["drop", "table", "users"], Path.cwd())


def test_run_safe_command_passes() -> None:
    result = run(["git", "status", "--short"], Path.cwd())
    assert isinstance(result, str)


@pytest.mark.parametrize(
    "command",
    [
        ["git", "branch", "-D", "main"],
        ["git", "push", "--force"],
        ["fsutil", "file", "setzerodata", "target"],
        ["cmd", "/c", "del", "/s", "target"],
        ["python", "-c", "import shutil; shutil.rmtree('target')"],
    ],
)
def test_is_destructive_catches_multi_token_forms(command: list[str]) -> None:
    assert _is_destructive(command) is True


def test_is_destructive_allows_regular_git_checkout() -> None:
    assert _is_destructive(["git", "checkout", "feature-branch"]) is False
