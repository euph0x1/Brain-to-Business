import sys
from pathlib import Path

import main as cli
from b2b import storage


def test_cli_end_to_end(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["main.py", "--yes", "textbooks are pricey"])
    cli.main()
    out = capsys.readouterr().out
    assert "Saved as idea #1" in out
    assert len(storage.list_ideas()) == 1

    monkeypatch.setattr(sys, "argv", ["main.py", "--list"])
    cli.main()
    assert "Campus textbook swap" in capsys.readouterr().out

    monkeypatch.setattr(sys, "argv", ["main.py", "--refine", "1", "target India", "--no-search"])
    cli.main()
    monkeypatch.setattr(sys, "argv", ["main.py", "--compare", "1", "2"])
    cli.main()
    assert "Overall" in capsys.readouterr().out


def test_streamlit_app_full_flow():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(Path(__file__).parent.parent / "app.py"), default_timeout=30).run()
    assert not at.exception
    at.text_area[0].set_value("textbooks are expensive").run()
    next(b for b in at.button if b.label == "Analyze my idea").click().run()
    assert not at.exception, at.exception
    assert any("Did I understand" in s.value for s in at.subheader)
    next(b for b in at.button if "Looks right" in b.label).click().run()
    assert not at.exception, at.exception
    assert any("Campus textbook swap" in h.value for h in at.header)
    assert at.metric[0].value.endswith("/10")
