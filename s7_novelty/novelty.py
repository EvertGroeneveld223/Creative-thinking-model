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

Only the sequence terms and search phrases are sent out. Standard library only.
Answers are cached in novelty_cache.json; only successful answers are cached, so failures are retried."""
import html, json, os, re, time, urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "novelty_cache.json")
UA = {"User-Agent": "creativity-engine-novelty/1.0"}
PAUSE = 1.5                 # seconds between live requests to one service
_last = {}


class Unavailable(Exception):
    pass


def http_get(url):
    """Returns the body text. Raises Unavailable unless the service really answered (200)."""
    host = urllib.parse.urlparse(url).netloc
    wait = PAUSE - (time.time() - _last.get(host, 0))
    if wait > 0:
        time.sleep(wait)
    _last[host] = time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
            if r.status != 200:
                raise Unavailable(f"HTTP {r.status}")
            return r.read().decode("utf-8", "replace")
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


def arxiv(query, cache, fetch=http_get):
    def go(fetch):
        body = fetch("https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"search_query": query, "max_results": 8}))
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            raise Unavailable("arXiv sent invalid XML")
        ns = {"a": "http://www.w3.org/2005/Atom"}
        hits = [dict(name=" ".join(e.findtext("a:title", "", ns).split()), url=e.findtext("a:id", "", ns)) for e in root.findall("a:entry", ns)]
        return dict(status="REVIEW" if hits else "CLEAR", hits=hits)
    return ask(cache, "arxiv:" + query, go, fetch)


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
            if t and all(w.lower() in t for w in must):
                hits.append(dict(name=" ".join(t.split()), url="https://doi.org/" + it.get("DOI", "")))
        return dict(status="REVIEW" if hits else "CLEAR", hits=hits)
    return ask(cache, "crossref:" + query + "|" + ",".join(must), go, fetch)


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
    """answers: {source: answer}. `required` sources must have been reached to claim NOT-FOUND."""
    st = {k: v["status"] for k, v in answers.items()}
    if "FOUND" in st.values():
        return "KNOWN", 0
    if any(st.get(k, "UNCHECKED") == "UNCHECKED" for k in required):
        return "UNCHECKED", None
    if "REVIEW" in st.values():
        return "REVIEW", None
    return "NOT-FOUND", 1               # an optional source that could not be asked is listed in `unreached`


def check(terms, phrases=(), arxiv_queries=(), crossref_queries=(), web=(), cache=None, fetch=http_get):
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
        a["arxiv: " + q] = arxiv(q, cache, fetch)
    for q, must in crossref_queries:
        a["crossref: " + q] = crossref(q, must, cache, fetch)
    for p in web:
        a["web: " + p] = duckduckgo(p, cache, fetch)
    v, n = verdict(a)
    return dict(verdict=v, n=n, terms=terms, searched=a, unreached=[k for k, x in a.items() if x["status"] == "UNCHECKED"])


def add_manual(key, status, hits, note, cache=None):
    """Record a search run outside this code (for example by the agent's web search), so it is kept with the rest."""
    cache = cache if cache is not None else Cache()
    cache.put("manual:" + key, dict(status=status, hits=hits, note=note))
