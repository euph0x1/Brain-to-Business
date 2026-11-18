"""Pydantic models: every pipeline step returns one of these (never free text)."""
from pydantic import BaseModel, Field, field_validator

CRITERIA = [
    "Problem severity",
    "Market size",
    "Competition level",
    "MVP ease",
    "Monetization clarity",
    "Founder effort/fit",
]


def _clamp(v: int) -> int:
    return max(1, min(10, int(v)))


class Clarified(BaseModel):
    problem: str
    solution: str
    one_liner: str
    assumptions: list[str]
    follow_up_questions: list[str] = Field(
        description="0-2 questions that would sharpen the idea; empty list if the idea is clear"
    )


class Competitor(BaseModel):
    name: str
    what_they_do: str
    url: str = Field(description="URL from the search results, or empty string if unknown")
    weakness: str = Field(description="A gap or weakness a new entrant could exploit")


class Research(BaseModel):
    competitors: list[Competitor]
    market_notes: str


class Segment(BaseModel):
    name: str
    pain_level: int = Field(description="Integer from 1 to 10")
    where_to_find_them: str

    @field_validator("pain_level")
    @classmethod
    def _c(cls, v):
        return _clamp(v)


class Customers(BaseModel):
    segments: list[Segment]


class RevenueModel(BaseModel):
    name: str
    how_it_works: str
    pricing_logic: str


class Revenue(BaseModel):
    models: list[RevenueModel]


class Score(BaseModel):
    criterion: str
    score: int = Field(description="Integer from 1 to 10")
    reason: str = Field(description="One sentence justification")

    @field_validator("score")
    @classmethod
    def _c(cls, v):
        return _clamp(v)


class Evaluation(BaseModel):
    scores: list[Score]
    verdict: str
    risks: list[str]


class RoadmapStep(BaseModel):
    week: str
    goal: str
    tasks: list[str]
    success_metric: str


class Roadmap(BaseModel):
    first_validation_test: str
    steps: list[RoadmapStep]
    tech_stack: str


class Brief(BaseModel):
    """The complete startup brief produced for one idea."""

    raw_idea: str
    clarified: Clarified
    research: Research
    grounded: bool  # True if competitor research used real web search results
    customers: Customers
    revenue: Revenue
    evaluation: Evaluation
    roadmap: Roadmap

    @property
    def overall(self) -> float:
        s = [x.score for x in self.evaluation.scores]
        return round(sum(s) / len(s), 1) if s else 0.0
