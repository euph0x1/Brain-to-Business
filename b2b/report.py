"""Render a Brief as Markdown, and compare two briefs."""
from .schemas import Brief


def render(b: Brief) -> str:
    c = b.clarified
    out = [f"# {c.one_liner}\n"]
    out.append(f"**Problem:** {c.problem}\n\n**Solution:** {c.solution}\n")
    out.append("**Key assumptions:**\n" + "\n".join(f"- {a}" for a in c.assumptions))

    src = "from live web search" if b.grounded else "from model knowledge, no live search"
    out.append(f"\n## Competitors ({src})")
    for comp in b.research.competitors:
        link = f" ({comp.url})" if comp.url else ""
        out.append(f"- **{comp.name}**{link}: {comp.what_they_do} *Gap: {comp.weakness}*")
    out.append(f"\n{b.research.market_notes}")

    out.append("\n## Target customers")
    for s in b.customers.segments:
        out.append(f"- **{s.name}** (pain {s.pain_level}/10): {s.where_to_find_them}")

    out.append("\n## Revenue models")
    for m in b.revenue.models:
        out.append(f"- **{m.name}**: {m.how_it_works} *Pricing: {m.pricing_logic}*")

    ev = b.evaluation
    out.append(f"\n## Evaluation (overall {b.overall}/10)")
    for s in ev.scores:
        out.append(f"- **{s.criterion}: {s.score}/10**: {s.reason}")
    out.append(f"\n**Verdict:** {ev.verdict}\n\n**Risks:**")
    out += [f"- {x}" for x in ev.risks]

    rm = b.roadmap
    out.append(f"\n## MVP roadmap\n**First validation test:** {rm.first_validation_test}\n")
    for st in rm.steps:
        out.append(f"### {st.week}: {st.goal}")
        out += [f"- {t}" for t in st.tasks]
        out.append(f"*Success metric: {st.success_metric}*\n")
    out.append(f"**Suggested stack:** {rm.tech_stack}")
    return "\n".join(out)


def score_map(b: Brief) -> dict[str, int]:
    return {s.criterion: s.score for s in b.evaluation.scores}


def compare(a: Brief, b: Brief, name_a: str = "A", name_b: str = "B") -> str:
    """Markdown table comparing two ideas criterion by criterion."""
    sa, sb = score_map(a), score_map(b)
    rows = [f"| Criterion | {name_a} | {name_b} |", "|---|---|---|"]
    for crit in list(dict.fromkeys([*sa, *sb])):
        rows.append(f"| {crit} | {sa.get(crit, '-')} | {sb.get(crit, '-')} |")
    rows.append(f"| **Overall** | **{a.overall}** | **{b.overall}** |")
    winner = name_a if a.overall > b.overall else name_b if b.overall > a.overall else "Tie"
    rows.append(f"\nHigher overall score: **{winner}**")
    return "\n".join(rows)
