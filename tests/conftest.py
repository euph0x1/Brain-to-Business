"""Shared fixtures: a fake model so tests need no API key or network."""
import pytest

from b2b import config, pipeline, tools
from b2b.schemas import (
    Clarified, Competitor, Customers, Evaluation, Research, Revenue, RevenueModel,
    Roadmap, RoadmapStep, Score, Segment, CRITERIA,
)


def fake_ask(system, user, schema):
    if schema is Clarified:
        tweak = " (refined)" if "User feedback" in user else ""
        return Clarified(
            problem="Students overpay for textbooks" + tweak,
            solution="Campus marketplace for used textbooks",
            one_liner="Campus textbook swap" + tweak,
            assumptions=["Students will trust peers"],
            follow_up_questions=[],
        )
    if schema is Research:
        return Research(
            competitors=[Competitor(name="Chegg", what_they_do="Rentals", url="", weakness="Pricey")],
            market_notes="Crowded but fragmented.",
        )
    if schema is Customers:
        return Customers(segments=[Segment(name="Undergrads", pain_level=15, where_to_find_them="Dorms")])
    if schema is Revenue:
        return Revenue(models=[RevenueModel(name="Promoted listings", how_it_works="Pay to boost", pricing_logic="$2")])
    if schema is Evaluation:
        return Evaluation(
            scores=[Score(criterion=f"made up {i}", score=6 + (i % 3), reason="because") for i in range(6)],
            verdict="Promising but crowded.",
            risks=["Chicken-and-egg", "Seasonality", "Trust"],
        )
    if schema is Roadmap:
        return Roadmap(
            first_validation_test="Interview 10 students",
            steps=[RoadmapStep(week="Week 1", goal="Validate", tasks=["Interview"], success_metric="8/10 say yes")],
            tech_stack="Next.js + Supabase",
        )
    raise AssertionError(f"unexpected schema {schema}")


@pytest.fixture(autouse=True)
def fake_env(monkeypatch, tmp_path):
    monkeypatch.setattr(pipeline, "ask", fake_ask)
    monkeypatch.setattr(config, "CALL_DELAY", 0)
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(config, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(
        tools, "gather", lambda q: [{"title": "t", "url": "https://x.com", "snippet": "s"}]
    )
