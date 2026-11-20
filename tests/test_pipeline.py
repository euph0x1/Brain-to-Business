from b2b import pipeline, report, storage, tools
from b2b.schemas import CRITERIA


def make_brief(raw="textbooks are expensive"):
    return pipeline.analyze(raw, pipeline.clarify(raw))


def test_analyze_builds_complete_brief_and_reports_progress():
    seen = []
    raw = "textbooks are expensive"
    b = pipeline.analyze(raw, pipeline.clarify(raw), on_step=seen.append)
    assert seen == ["research", "customers", "revenue", "evaluation", "roadmap"]
    assert b.grounded is True
    assert [s.criterion for s in b.evaluation.scores] == CRITERIA  # names normalised
    assert b.customers.segments[0].pain_level == 10  # 15 clamped to 10
    assert 1 <= b.overall <= 10


def test_falls_back_when_search_returns_nothing(monkeypatch):
    monkeypatch.setattr(tools, "gather", lambda q: [])
    assert make_brief().grounded is False


def test_search_can_be_disabled(monkeypatch):
    def boom(q):
        raise AssertionError("search should not run")
    monkeypatch.setattr(tools, "gather", boom)
    raw = "x"
    b = pipeline.analyze(raw, pipeline.clarify(raw), enable_search=False)
    assert b.grounded is False


def test_refine_applies_feedback():
    b = pipeline.refine(make_brief(), "target students in India")
    assert "refined" in b.clarified.one_liner
    assert "Refinement" in b.raw_idea


def test_storage_roundtrip_list_delete():
    b = make_brief()
    i = storage.save(b)
    assert storage.load(i) == b
    assert storage.list_ideas()[0]["id"] == i
    storage.delete(i)
    assert storage.load(i) is None
    assert storage.list_ideas() == []


def test_report_and_compare():
    a, b = make_brief(), pipeline.refine(make_brief(), "x")
    md = report.render(a)
    assert "Campus textbook swap" in md and "Verdict" in md and "MVP roadmap" in md
    table = report.compare(a, b, "A", "B")
    assert "Problem severity" in table and "Overall" in table


def test_web_search_failure_returns_empty(monkeypatch):
    import builtins
    real = builtins.__import__

    def bad(name, *a, **k):
        if name in ("ddgs", "duckduckgo_search"):
            raise ImportError
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", bad)
    assert tools.web_search("anything") == []
