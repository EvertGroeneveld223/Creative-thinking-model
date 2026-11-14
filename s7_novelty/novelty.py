"""Novelty check done by code: does this idea already exist on the web?

Each source answers one of:
  FOUND     an exact match that the code verified (the terms really are in the entry's data)
  REVIEW    a possibly related page; a person or agent must open it, code cannot decide
  CLEAR     the source answered and has nothing
  UNCHECKED the source could not be asked (blocked, rate limited, offline)

Verdict over all sources:
  KNOWN      any source says FOUND                       -> n = 0
  REVIEW     nothing FOUND, some candidate pages to open -> n undecided
  NOT-FOUND  every required source says CLEAR            -> n = 1, meaning "not found by these searches", never "new"
  UNCHECKED  a required source could not be asked        -> n undecided. An outage must never look like a discovery.
  TRIVIAL    too little information to search for        -> n undecided

`required` names the kinds of source that must all have answered before NOT-FOUND can be claimed.
An OEIS term match is only a start: compare() checks it against every term the entry lists, because 12 small numbers can match by chance.
Only the sequence terms and search phrases are sent out, with no API key and no personal data. Standard library only.
Answers are cached in novelty_cache.json; only successful answers are cached, so failures are retried."""
import gzip, html, json, os, re, time, urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "novelty_cache.json")
UA = {"User-Agent": "creativity-engine-novelty/1.0"}
PAUSE = 1.5                 # seconds between live requests to one service
PAUSES = {"export.arxiv.org": 3.5}
_last = {}


class Unavailable(Exception):
    pass


def http_get(url):
    """Returns the body text. Raises Unavailable unless the service really answered (200)."""
    host = urllib.parse.urlparse(url).netloc
    wait = PAUSES.get(host, PAUSE) - (time.time() - _last.get(host, 0))
    if wait > 0:
        time.sleep(wait)
    _last[host] = time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
            if r.status != 200:
                raise Unavailable(f"HTTP {r.status}")
            raw = r.read()
            return (gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw).decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise Unavailable(repr(e))


class Cache:
    def __init__(self, path=CACHE):
        self.path = path
        self.d = json.load(open(path)) if path and os.path.exists(path) else {}

    def get(self, k):
        return self.d.get(k)

    def put(self, k, v):
        self.d[k] = dict(v, checked=time.strftime("%Y-%m-%d"))
        if self.path:
            tmp = self.path + ".tmp"
            json.dump(self.d, open(tmp, "w"), indent=1, sort_keys=True)
            os.replace(tmp, self.path)


def has_run(data, terms):
    """True if terms occur contiguously in a comma-separated OEIS data string."""
    a = ",".join(str(x) for x in terms)
    return f",{a}," in f",{data.replace(' ', '')},"


def ask(cache, key, fn, fetch):
    hit = cache.get(key)
    if hit:
        return dict(hit, cached=True)
    try:
        out = fn(fetch)
    except Unavailable as e:
        return dict(status="UNCHECKED", why=str(e), hits=[])
    cache.put(key, out)
    return out


def oeis_terms(terms, cache, fetch=http_get):
    """Exact term search. The OEIS answer is re-checked here, so a loose search hit never counts as FOUND."""
    q = ",".join(str(x) for x in terms)

    def go(fetch):
        body = fetch("https://oeis.org/search?" + urllib.parse.urlencode({"q": q, "fmt": "json"}))
        try:
            rows = json.loads(body)
        except ValueError:
            raise Unavailable("OEIS sent something other than JSON")
        rows = rows or []
        if isinstance(rows, dict):          # older response shape
            rows = rows.get("results") or []
        exact = [r for r in rows if has_run(r.get("data", ""), terms)]
        hits = [dict(id=f"A{r['number']:06d}", name=r.get("name", ""), url=f"https://oeis.org/A{r['number']:06d}") for r in exact[:5]]
        return dict(status="FOUND" if hits else "CLEAR", hits=hits)
    return ask(cache, "oeis:" + q, go, fetch)


def oeis_text(phrase, cache, fetch=http_get):
    """OEIS text search. It may turn up an entry that indexes the terms differently, so a hit only asks for review."""
    def go(fetch):
        body = fetch("https://oeis.org/search?" + urllib.parse.urlencode({"q": phrase, "fmt": "json"}))
        try:
            rows = json.loads(body)
        except ValueError:
            raise Unavailable("OEIS sent something other than JSON")
        rows = rows or []
        if isinstance(rows, dict):
            rows = rows.get("results") or []
        hits = [dict(id=f"A{r['number']:06d}", name=r.get("name", ""), url=f"https://oeis.org/A{r['number']:06d}") for r in rows[:5]]
        return dict(status="REVIEW" if hits else "CLEAR", hits=hits)
    return ask(cache, "oeis-text:" + phrase, go, fetch)


def oeis_entry(aid, cache, fetch=http_get):
    """One whole entry, so a match can be compared on every term it lists."""
    def go(fetch):
        body = fetch("https://oeis.org/search?" + urllib.parse.urlencode({"q": "id:" + aid, "fmt": "json"}))
        try:
            rows = json.loads(body)
        except ValueError:
            raise Unavailable("OEIS sent something other than JSON")
        rows = (rows.get("results") if isinstance(rows, dict) else rows) or []
        if not rows:
            raise Unavailable("OEIS returned no entry for " + aid)
        r = rows[0]
        return dict(status="FOUND", id=aid, name=r.get("name", ""), data=r.get("data", ""), offset=r.get("offset", ""), hits=[])
    return ask(cache, "oeis-entry:" + aid, go, fetch)


def compare(table, data, min_overlap=30, run=12):
    """Lines the table up with an entry's data at the first place its first `run` terms occur, then compares every overlapping term.
    AGREES: no difference over at least min_overlap terms. SHORT: no difference, but too few terms to mean much. DIVERGES: a chance match.
    `overlap` counts the terms compared, `first_diff` is the index in the table of the first difference."""
    d = [int(x) for x in data.replace(" ", "").split(",") if x]
    k = min(run, len(table))
    at = next((i for i in range(len(d) - k + 1) if d[i:i+k] == list(table[:k])), None)
    if at is None:
        return dict(result="DIVERGES", overlap=0, first_diff=0, entry_terms=len(d))
    n = min(len(table), len(d) - at)
    diff = next((i for i in range(n) if table[i] != d[at+i]), None)
    return dict(result="DIVERGES" if diff is not None else ("AGREES" if n >= min_overlap else "SHORT"), overlap=n, first_diff=diff, entry_terms=len(d), at=at)


def _has_all(text, must):
    """must: words that must all occur. A tuple in the list means any one of those words."""
    t = text.lower()
    return all(any(x.lower() in t for x in w) if isinstance(w, tuple) else w.lower() in t for w in must)


def _mustkey(must):
    return ",".join("|".join(w) if isinstance(w, tuple) else w for w in must)


def _plain(x):
    return html.unescape(re.sub(r"<[^>]+>", " ", x or ""))


def openalex(query, must, cache, fetch=http_get):
    """Scholarly works, searched over title, abstract and full text. A work counts only if its title or abstract has every word in `must`."""
    def go(fetch):
        body = fetch("https://api.openalex.org/works?" + urllib.parse.urlencode({"search": query, "per-page": 25, "select": "id,title,doi,abstract_inverted_index"}))
        try:
            items = json.loads(body)["results"]
        except (ValueError, KeyError):
            raise Unavailable("OpenAlex sent an unexpected answer")
        hits = []
        for it in items:
            t = _plain(it.get("title")); ab = " ".join(it.get("abstract_inverted_index") or {})
            if t and _has_all(t + " " + ab, must):
                hits.append(dict(name=" ".join(t.split()), url=it.get("doi") or it.get("id", "")))
        return dict(status="REVIEW" if hits else "CLEAR", hits=hits)
    return ask(cache, "openalex:" + query + "|" + _mustkey(must), go, fetch)


def stackexchange(query, must, cache, fetch=http_get, site="math"):
    """Questions on a Stack Exchange site (math or mathoverflow), title and body."""
    def go(fetch):
        body = fetch("https://api.stackexchange.com/2.3/search/advanced?" + urllib.parse.urlencode({"order": "desc", "sort": "relevance", "q": query, "site": site, "pagesize": 25, "filter": "withbody"}))
        try:
            items = json.loads(body)["items"]
        except (ValueError, KeyError):
            raise Unavailable("Stack Exchange sent an unexpected answer")
        hits = [dict(name=_plain(i.get("title")), url=i.get("link", "")) for i in items if _has_all(_plain(i.get("title")) + " " + _plain(i.get("body")), must)]
        return dict(status="REVIEW" if hits else "CLEAR", hits=hits)
    return ask(cache, f"stackexchange-{site}:" + query + "|" + _mustkey(must), go, fetch)


def zbmath(query, must, cache, fetch=http_get):
    """zbMATH Open records, title and review text. A search with no result answers 404, which here means CLEAR."""
    def go(fetch):
        try:
            body = fetch("https://api.zbmath.org/v1/document/_search?" + urllib.parse.urlencode({"search_string": query, "results_per_page": 25}))
        except Unavailable as e:
            if "404" in str(e):
                return dict(status="CLEAR", hits=[])
            raise
        try:
            items = json.loads(body)["result"]
        except (ValueError, KeyError):
            raise Unavailable("zbMATH sent an unexpected answer")
        hits = []
        for it in items:
            t = it.get("title") or {}
            t = t.get("title", "") if isinstance(t, dict) else str(t)
            text = " ".join(str(c.get("text", "")) for c in it.get("editorial_contributions") or [])
            if _has_all(t + " " + text, must):
                hits.append(dict(name=_plain(t) or "(no title)", url=it.get("zbmath_url") or f"https://zbmath.org/?q=an:{it.get('identifier', '')}"))
        return dict(status="REVIEW" if hits else "CLEAR", hits=hits)
    return ask(cache, "zbmath:" + query + "|" + _mustkey(must), go, fetch)


def arxiv(query, cache, fetch=http_get, must=()):
    def go(fetch):
        body = fetch("https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"search_query": query, "max_results": 25 if must else 8}))
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            raise Unavailable("arXiv sent invalid XML")
        ns = {"a": "http://www.w3.org/2005/Atom"}
        hits = [dict(name=" ".join(e.findtext("a:title", "", ns).split()), url=e.findtext("a:id", "", ns)) for e in root.findall("a:entry", ns)
                if _has_all(e.findtext("a:title", "", ns) + " " + e.findtext("a:summary", "", ns), must)]
        return dict(status="REVIEW" if hits else "CLEAR", hits=hits)
    return ask(cache, "arxiv:" + query + ("|" + _mustkey(must) if must else ""), go, fetch)


def crossref(query, must, cache, fetch=http_get):
    """Crossref ranks fuzzily and always returns something, so a title must contain every word in `must`."""
    def go(fetch):
        body = fetch("https://api.crossref.org/works?" + urllib.parse.urlencode({"query.bibliographic": query, "rows": 25, "select": "title,DOI"}))
        try:
            items = json.loads(body)["message"]["items"]
        except (ValueError, KeyError):
            raise Unavailable("Crossref sent an unexpected answer")
        hits = []
        for it in items:
            t = html.unescape(re.sub(r"<[^>]+>", "", " ".join(it.get("title") or []))).lower()
            if t and _has_all(t, must):
                hits.append(dict(name=" ".join(t.split()), url="https://doi.org/" + it.get("DOI", "")))
        return dict(status="REVIEW" if hits else "CLEAR", hits=hits)
    return ask(cache, "crossref:" + query + "|" + _mustkey(must), go, fetch)


def duckduckgo(phrase, cache, fetch=http_get):
    """General web. If the service sends a bot check instead of results, say UNCHECKED; do not work around it."""
    def go(fetch):
        body = fetch("https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": phrase}))
        links = re.findall(r'class="result__a"[^>]*>(.*?)</a>', body, re.S)
        if not links and "no-results" not in body and "No results" not in body:
            raise Unavailable("no result list in the page (probably a bot check)")
        hits = [dict(name=html.unescape(re.sub(r"<[^>]+>", "", x)).strip()) for x in links[:8]]
        return dict(status="REVIEW" if hits else "CLEAR", hits=hits)
    return ask(cache, "ddg:" + phrase, go, fetch)


def informative(terms):
    """Very short or nearly constant term lists match lots of unrelated entries, so a search says nothing."""
    return len(terms) >= 6 and len(set(terms)) >= 3


def verdict(answers, required=("oeis-terms",)):
    """answers: {source: answer}. Every source of each `required` kind must have answered to claim NOT-FOUND, and each kind must have been asked."""
    st = {k: v["status"] for k, v in answers.items()}
    if "FOUND" in st.values():
        return "KNOWN", 0
    for kind in required:
        ks = [k for k in st if k == kind or k.startswith(kind + ":")]
        if not ks or any(st[k] == "UNCHECKED" for k in ks):
            return "UNCHECKED", None
    if "REVIEW" in st.values():
        return "REVIEW", None
    return "NOT-FOUND", 1               # an optional source that could not be asked is listed in `unreached`


def check(terms, phrases=(), arxiv_queries=(), crossref_queries=(), web=(), cache=None, fetch=http_get, openalex_queries=(), stackexchange_queries=(), zbmath_queries=(), required=("oeis-terms",)):
    """terms: the sequence to look for (one period repeated, or a period table).
    Returns the verdict, n, and every search that ran, so that n = 1 always says what it means."""
    cache = cache if cache is not None else Cache()
    terms = [int(x) for x in terms]
    if not informative(terms):
        return dict(verdict="TRIVIAL", n=None, terms=terms, searched={}, why="too few or too uniform terms to search for")
    a = {"oeis-terms": oeis_terms(terms, cache, fetch)}
    for p in phrases:
        a["oeis-text: " + p] = oeis_text(p, cache, fetch)
    for q in arxiv_queries:
        q, must = q if isinstance(q, tuple) else (q, ())
        a["arxiv: " + q] = arxiv(q, cache, fetch, must)
    for q, must in crossref_queries:
        a["crossref: " + q] = crossref(q, must, cache, fetch)
    for p in web:
        a["web: " + p] = duckduckgo(p, cache, fetch)
    for q, must in openalex_queries:
        a["openalex: " + q] = openalex(q, must, cache, fetch)
    for q, must in zbmath_queries:
        a["zbmath: " + q] = zbmath(q, must, cache, fetch)
    for q, must in stackexchange_queries:
        for site in ("math", "mathoverflow"):
            a[f"stackexchange-{site}: " + q] = stackexchange(q, must, cache, fetch, site)
    v, n = verdict(a, required)
    return dict(verdict=v, n=n, terms=terms, searched=a, unreached=[k for k, x in a.items() if x["status"] == "UNCHECKED"])


def add_manual(key, status, hits, note, cache=None):
    """Record a search run outside this code (for example by the agent's web search), so it is kept with the rest."""
    cache = cache if cache is not None else Cache()
    cache.put("manual:" + key, dict(status=status, hits=hits, note=note))
