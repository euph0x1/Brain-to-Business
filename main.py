"""Brain-to-Business CLI.

Examples:
  python main.py "students overpay for textbooks"
  python main.py                       # interactive prompt
  python main.py --list                # past ideas
  python main.py --show 3
  python main.py --compare 1 3
  python main.py --refine 3 "target students in India instead"
"""
import argparse
import sys

from b2b import config, pipeline, report, storage
from b2b.llm import LLMError


def _progress(name: str):
    print(f"-> {pipeline.STEP_LABELS[name]}...")


def _finish(brief, idea_id=None):
    idea_id = idea_id or storage.save(brief)
    md = report.render(brief)
    config.REPORTS_DIR.mkdir(exist_ok=True)
    path = config.REPORTS_DIR / f"idea-{idea_id}.md"
    path.write_text(md, encoding="utf-8")
    print("\n" + md)
    print(f"\nSaved as idea #{idea_id}  |  report: {path}")


def cmd_new(args):
    raw = " ".join(args.idea).strip() or input("Describe your idea or thought:\n> ").strip()
    if not raw:
        sys.exit("No idea given.")
    search = False if args.no_search else None

    print("\n-> Understanding your idea...")
    clarified = pipeline.clarify(raw)
    while True:
        print(f"\nHere's what I understood:\n  Pitch:    {clarified.one_liner}")
        print(f"  Problem:  {clarified.problem}")
        print(f"  Solution: {clarified.solution}")
        for q in clarified.follow_up_questions:
            print(f"  ? {q}")
        if args.yes:
            break
        ans = input("\nLooks right? [Y]es / type a correction: ").strip()
        if ans.lower() in ("", "y", "yes"):
            break
        clarified = pipeline.clarify(raw, feedback=ans, previous=clarified)

    _finish(pipeline.analyze(raw, clarified, on_step=_progress, enable_search=search))


def cmd_list(_):
    ideas = storage.list_ideas()
    if not ideas:
        print("No saved ideas yet.")
    for i in ideas:
        print(f"#{i['id']:<3} {i['overall']:>4}/10  {i['created_at']}  {i['title']}")


def cmd_show(idea_id):
    brief = storage.load(idea_id)
    print(report.render(brief) if brief else f"No idea #{idea_id}.")


def cmd_compare(a_id, b_id):
    a, b = storage.load(a_id), storage.load(b_id)
    if not a or not b:
        sys.exit("One of those ids does not exist. Use --list to see saved ideas.")
    print(f"A = #{a_id}: {a.clarified.one_liner}\nB = #{b_id}: {b.clarified.one_liner}\n")
    print(report.compare(a, b, f"#{a_id}", f"#{b_id}"))


def cmd_refine(idea_id, feedback, no_search):
    brief = storage.load(idea_id)
    if not brief:
        sys.exit(f"No idea #{idea_id}.")
    search = False if no_search else None
    _finish(pipeline.refine(brief, feedback, on_step=_progress, enable_search=search))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    p = argparse.ArgumentParser(description="Turn raw thoughts into startup briefs.")
    p.add_argument("idea", nargs="*", help="your idea or thought")
    p.add_argument("--yes", action="store_true", help="skip the confirmation step")
    p.add_argument("--no-search", action="store_true", help="skip web search")
    p.add_argument("--list", action="store_true", help="list saved ideas")
    p.add_argument("--show", type=int, metavar="ID", help="print a saved report")
    p.add_argument("--compare", type=int, nargs=2, metavar=("A", "B"), help="compare two saved ideas")
    p.add_argument("--refine", nargs=2, metavar=("ID", "FEEDBACK"), help="refine a saved idea")
    args = p.parse_args()

    try:
        if args.list:
            cmd_list(args)
        elif args.show is not None:
            cmd_show(args.show)
        elif args.compare:
            cmd_compare(*args.compare)
        elif args.refine:
            cmd_refine(int(args.refine[0]), args.refine[1], args.no_search)
        else:
            cmd_new(args)
    except LLMError as e:
        sys.exit(f"\nError: {e}")
    except KeyboardInterrupt:
        sys.exit("\nCancelled.")


if __name__ == "__main__":
    main()
