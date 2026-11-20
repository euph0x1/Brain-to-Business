"""Web search tool (free, no API key) used for competitor research."""


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Return [{title, url, snippet}, ...]. Returns [] on any failure."""
    try:
        try:
            from ddgs import DDGS
        except ImportError:  # older package name
            from duckduckgo_search import DDGS
        raw = DDGS().text(query, max_results=max_results) or []
        return [
            {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
            for r in raw
        ]
    except Exception as e:  # network down, rate-limited, package missing...
        print(f"  (web search unavailable: {type(e).__name__})")
        return []


def gather(queries: list[str]) -> list[dict]:
    """Run several searches and de-duplicate by URL."""
    seen, out = set(), []
    for q in queries:
        for r in web_search(q):
            if r["url"] and r["url"] not in seen:
                seen.add(r["url"])
                out.append(r)
    return out


def format_results(results: list[dict]) -> str:
    return "\n\n".join(
        f"[{i}] {r['title']}\nURL: {r['url']}\n{r['snippet']}" for i, r in enumerate(results, 1)
    )
