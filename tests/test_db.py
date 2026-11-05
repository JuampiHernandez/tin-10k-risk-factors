import os
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.skipif("DATABASE_URL" not in os.environ, reason="set DATABASE_URL to run the database test")


def run(script):
    return subprocess.run([sys.executable, str(ROOT / "src" / script)], capture_output=True, text=True, check=True).stdout


def test_load_is_repeatable_and_queries_return_cited_rows():
    first = run("load.py")
    second = run("load.py")
    assert first.splitlines()[-1] == second.splitlines()[-1]
    out = run("search.py")
    assert "export controls" in out.lower().replace("<b>", "").replace("</b>", "")
    assert "https://www.sec.gov/Archives/" in out
    assert "sec-gov/filings/sections" in out
