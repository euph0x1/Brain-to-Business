"""Brain-to-Business web UI.  Run with:  streamlit run app.py"""
import pandas as pd
import streamlit as st

from b2b import config, pipeline, report, storage
from b2b.llm import LLMError

st.set_page_config(page_title="Brain-to-Business", page_icon="💡", layout="wide")

# ---------- session state ----------
for key, default in {
    "stage": "input",  # input -> confirm -> done
    "raw": "",
    "clarified": None,
    "brief": None,
    "brief_id": None,
}.items():
    st.session_state.setdefault(key, default)


def reset():
    for k in ("raw", "clarified", "brief", "brief_id"):
        st.session_state[k] = "" if k == "raw" else None
    st.session_state.stage = "input"


def run_analysis(raw, clarified):
    """Run the full pipeline with live progress, then save and show the result."""
    with st.status("Analyzing your idea...", expanded=True) as status:
        brief = pipeline.analyze(
            raw, clarified, on_step=lambda n: st.write(f"{pipeline.STEP_LABELS[n]}...")
        )
        status.update(label="Done!", state="complete", expanded=False)
    st.session_state.brief = brief
    st.session_state.brief_id = storage.save(brief)
    st.session_state.stage = "done"


# ---------- sidebar ----------
with st.sidebar:
    st.title("💡 Brain-to-Business")
    st.caption(f"Model: `{config.MODEL}`")
    if st.button("➕ New idea", use_container_width=True):
        reset()
        st.rerun()
    st.divider()
    st.subheader("Saved ideas")
    history = storage.list_ideas()
    if not history:
        st.caption("Nothing yet. Your analyzed ideas appear here.")
    for item in history:
        label = f"{item['overall']}/10 · {item['title'][:42]}"
        if st.button(label, key=f"hist_{item['id']}", use_container_width=True):
            st.session_state.brief = storage.load(item["id"])
            st.session_state.brief_id = item["id"]
            st.session_state.stage = "done"
            st.rerun()


# ---------- result view ----------
def show_brief(b):
    c = b.clarified
    left, right = st.columns([4, 1])
    left.header(c.one_liner)
    right.metric("Overall score", f"{b.overall}/10")
    st.info(f"**Verdict:** {b.evaluation.verdict}")

    tabs = st.tabs(["Overview", "Competitors", "Customers", "Revenue", "Evaluation", "MVP roadmap"])

    with tabs[0]:
        st.markdown(f"**Problem:** {c.problem}")
        st.markdown(f"**Solution:** {c.solution}")
        st.markdown("**Key assumptions to test**")
        for a in c.assumptions:
            st.markdown(f"- {a}")

    with tabs[1]:
        st.caption(
            "Based on live web search." if b.grounded
            else "No live search results; based on model knowledge. Verify these yourself."
        )
        for comp in b.research.competitors:
            title = f"[{comp.name}]({comp.url})" if comp.url else comp.name
            st.markdown(f"**{title}**: {comp.what_they_do}")
            st.markdown(f"*Gap you could exploit:* {comp.weakness}")
        st.write(b.research.market_notes)

    with tabs[2]:
        for s in b.customers.segments:
            st.markdown(f"**{s.name}** · pain {s.pain_level}/10")
            st.progress(s.pain_level / 10)
            st.caption(f"Where to find them: {s.where_to_find_them}")

    with tabs[3]:
        for m in b.revenue.models:
            st.markdown(f"**{m.name}**")
            st.write(m.how_it_works)
            st.caption(f"Pricing logic: {m.pricing_logic}")

    with tabs[4]:
        df = pd.DataFrame(
            [{"Criterion": s.criterion, "Score": s.score, "Why": s.reason} for s in b.evaluation.scores]
        )
        st.bar_chart(df.set_index("Criterion")["Score"])
        st.dataframe(df, hide_index=True, use_container_width=True)
        st.markdown("**Top risks**")
        for r in b.evaluation.risks:
            st.markdown(f"- {r}")

    with tabs[5]:
        st.success(f"**Start here (no code needed):** {b.roadmap.first_validation_test}")
        for st_ in b.roadmap.steps:
            with st.expander(f"{st_.week}: {st_.goal}"):
                for t in st_.tasks:
                    st.markdown(f"- {t}")
                st.caption(f"Success metric: {st_.success_metric}")
        st.markdown(f"**Suggested stack:** {b.roadmap.tech_stack}")

    st.download_button(
        "⬇️ Download report (.md)",
        report.render(b),
        file_name=f"idea-{st.session_state.brief_id or 'new'}.md",
        mime="text/markdown",
    )

    with st.expander("🔄 Refine this idea"):
        fb = st.text_input("What should change?", placeholder="e.g. target students in India instead")
        if st.button("Re-run with this change") and fb.strip():
            try:
                with st.status("Refining...", expanded=True) as status:
                    nb = pipeline.refine(
                        b, fb, on_step=lambda n: st.write(f"{pipeline.STEP_LABELS[n]}...")
                    )
                    status.update(label="Done!", state="complete", expanded=False)
                st.session_state.brief = nb
                st.session_state.brief_id = storage.save(nb)
                st.rerun()
            except LLMError as e:
                st.error(str(e))


# ---------- compare view ----------
def show_compare():
    ideas = storage.list_ideas()
    if len(ideas) < 2:
        st.info("Analyze at least two ideas to compare them.")
        return
    labels = {f"#{i['id']} · {i['title'][:60]}": i["id"] for i in ideas}
    names = list(labels)
    c1, c2 = st.columns(2)
    a_name = c1.selectbox("Idea A", names, index=0)
    b_name = c2.selectbox("Idea B", names, index=1)
    a, b = storage.load(labels[a_name]), storage.load(labels[b_name])
    sa, sb = report.score_map(a), report.score_map(b)
    df = pd.DataFrame({f"A (#{labels[a_name]})": sa, f"B (#{labels[b_name]})": sb})
    st.bar_chart(df)
    st.dataframe(df, use_container_width=True)
    m1, m2 = st.columns(2)
    m1.metric("A overall", f"{a.overall}/10")
    m2.metric("B overall", f"{b.overall}/10")
    m1.caption(a.evaluation.verdict)
    m2.caption(b.evaluation.verdict)


# ---------- main ----------
tab_idea, tab_compare = st.tabs(["💡 Idea", "⚖️ Compare ideas"])

with tab_compare:
    show_compare()

with tab_idea:
    try:
        if st.session_state.stage == "input":
            st.subheader("What's on your mind?")
            st.caption("A random thought, an everyday annoyance, a half-baked idea. Messy is fine.")
            raw = st.text_area(
                "Your idea",
                height=150,
                label_visibility="collapsed",
                placeholder="e.g. Students overpay for textbooks while other students' books just sit on shelves...",
            )
            if st.button("Analyze my idea", type="primary") and raw.strip():
                with st.spinner("Understanding your idea..."):
                    st.session_state.clarified = pipeline.clarify(raw.strip())
                st.session_state.raw = raw.strip()
                st.session_state.stage = "confirm"
                st.rerun()

        elif st.session_state.stage == "confirm":
            cl = st.session_state.clarified
            st.subheader("Did I understand you correctly?")
            st.markdown(f"**Pitch:** {cl.one_liner}")
            st.markdown(f"**Problem:** {cl.problem}")
            st.markdown(f"**Solution:** {cl.solution}")
            if cl.follow_up_questions:
                st.markdown("**Questions that would sharpen this:**")
                for q in cl.follow_up_questions:
                    st.markdown(f"- {q}")
            fix = st.text_input("Not quite? Tell me what to change (optional)")
            c1, c2 = st.columns(2)
            if c1.button("✅ Looks right, run full analysis", type="primary"):
                run_analysis(st.session_state.raw, cl)
                st.rerun()
            if c2.button("✏️ Re-clarify with my correction") and fix.strip():
                with st.spinner("Updating..."):
                    st.session_state.clarified = pipeline.clarify(
                        st.session_state.raw, feedback=fix.strip(), previous=cl
                    )
                st.rerun()

        else:  # done
            show_brief(st.session_state.brief)

    except LLMError as e:
        st.error(str(e))
