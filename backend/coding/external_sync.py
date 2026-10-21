import math
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from django.db import transaction
from django.utils.text import slugify

from .external import build_external_tags, platform_label
from .models import Problem

# A browser-like user agent is important here. HackerRank and CodeChef can return
# a reduced/blocked page to obvious bot user agents, which made the old sync
# return zero questions even though the sites were reachable in a browser.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/155.0.0.0 Safari/537.36"
)


HACKERRANK_TRACKS = (
    "algorithms",
    "data-structures",
    "mathematics",
    "ai",
    "databases",
    "regex",
    "shell",
    "sql",
    "python",
    "java",
    "cpp",
    "c",
    "ruby",
    "functional-programming",
)


def _session():
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
    )
    return s


def _difficulty(value):
    value = str(value or "").upper().strip()
    if value in {"1", "EASY", "BEGINNER", "BASIC"}:
        return "EASY"
    if value in {"2", "MEDIUM", "INTERMEDIATE"}:
        return "MEDIUM"
    if value in {"3", "HARD", "ADVANCED", "EXPERT"}:
        return "HARD"
    return "MEDIUM"


def _difficulty_from_rating(value):
    try:
        rating = int(float(value))
    except (TypeError, ValueError):
        return "MEDIUM"
    if rating < 1000:
        return "EASY"
    if rating < 1800:
        return "MEDIUM"
    return "HARD"


def _safe_percent(value):
    """Normalize ratios such as 0.9756 or percentages such as 97.56."""
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if 0 <= result <= 1:
        result *= 100
    if not 0 <= result <= 100:
        return None
    return round(result, 2)


def _upsert(item):
    platform = item["platform"]
    external_id = str(item.get("external_id") or "").strip()
    url = item["url"]
    tags = build_external_tags(
        platform,
        url,
        external_id,
        item.get("tags"),
        number=item.get("number"),
        acceptance=item.get("acceptance"),
        success_rate=item.get("success_rate"),
        premium=item.get("premium"),
        topics=item.get("topics"),
        score=item.get("score"),
    )
    slug_base = slugify(f"{platform}-{external_id or item['title']}")[:230] or "external-problem"
    obj = Problem.objects.filter(slug=slug_base).first()
    if obj is None:
        slug = slug_base
        suffix = 2
        while Problem.objects.filter(slug=slug).exists():
            slug = f"{slug_base[:220]}-{suffix}"
            suffix += 1
        obj = Problem(slug=slug)
    obj.title = item["title"][:200]
    obj.description = item.get("description") or (
        f"Open this {platform_label(platform)} problem on the original platform "
        "to read the full statement and solve it."
    )
    obj.input_format = ""
    obj.output_format = ""
    obj.constraints = ""
    obj.difficulty = _difficulty(item.get("difficulty"))
    obj.topic = (item.get("topic") or "Coding")[:100]
    obj.tags = tags
    obj.points = 0
    obj.is_published = True
    obj.save()
    return obj


def sync_leetcode(limit=5000):
    """Import public LeetCode problem metadata while keeping solving on LeetCode."""
    s = _session()

    try:
        response = s.get(
            "https://leetcode.com/api/problems/all/",
            timeout=30,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json,text/plain,*/*",
                "Referer": "https://leetcode.com/problemset/all/",
            },
        )
        response.raise_for_status()
        payload = response.json()
        pairs = payload.get("stat_status_pairs") or []
    except Exception:
        pairs = []

    if not pairs:
        try:
            response = s.get(
                "https://alfa-leetcode-api.onrender.com/problems",
                params={"limit": min(int(limit), 5000)},
                timeout=45,
            )
            response.raise_for_status()
            payload = response.json()
            pairs = (
                payload.get("problemsetQuestionList")
                or payload.get("problems")
                or payload.get("data")
                or []
            )
        except Exception as exc:
            raise RuntimeError(
                "Unable to load the LeetCode problem catalog. "
                f"Official endpoint and fallback endpoint failed: {exc}"
            ) from exc

    if not pairs:
        raise RuntimeError("No LeetCode problems were returned by the catalog sources.")

    count = 0
    with transaction.atomic():
        for item in pairs:
            if count >= min(int(limit), 5000):
                break

            stat = item.get("stat") or {}
            title = str(stat.get("question__title") or "").strip()
            slug = str(stat.get("question__title_slug") or "").strip()
            question_number = str(
                stat.get("frontend_question_id") or stat.get("question_id") or ""
            ).strip()
            difficulty_level = (item.get("difficulty") or {}).get("level")
            premium = bool(item.get("paid_only") or item.get("isPaidOnly"))

            acceptance = None
            total_accepted = stat.get("total_acs")
            total_submitted = stat.get("total_submitted")
            if total_accepted is not None and total_submitted:
                try:
                    acceptance = round(
                        float(total_accepted) / float(total_submitted) * 100, 2
                    )
                except (TypeError, ValueError, ZeroDivisionError):
                    acceptance = None

            if not title:
                title = str(item.get("title") or item.get("name") or "").strip()
            if not slug:
                slug = str(
                    item.get("titleSlug")
                    or item.get("title_slug")
                    or item.get("slug")
                    or ""
                ).strip()
            if not question_number:
                question_number = str(
                    item.get("questionFrontendId")
                    or item.get("frontendQuestionId")
                    or item.get("questionId")
                    or item.get("id")
                    or ""
                ).strip()

            difficulty_value = (
                item.get("difficulty") or item.get("difficulty_name") or ""
                if difficulty_level is None
                else difficulty_level
            )
            difficulty = _difficulty(difficulty_value)

            if acceptance is None:
                acceptance = _safe_percent(
                    item.get("acRate")
                    or item.get("acceptance_rate")
                    or item.get("acceptance")
                )

            if not title or not slug:
                continue

            _upsert(
                {
                    "platform": "LEETCODE",
                    "external_id": question_number or slug,
                    "number": question_number,
                    "title": title,
                    "difficulty": difficulty,
                    "acceptance": acceptance,
                    "premium": premium,
                    "topic": "Algorithms",
                    "url": f"https://leetcode.com/problems/{slug}/",
                }
            )
            count += 1

    if count == 0:
        raise RuntimeError(
            "LeetCode catalog was reached, but no usable questions were imported."
        )
    return count


def sync_codeforces(limit=5000):
    s = _session()
    response = s.get("https://codeforces.com/api/problemset.problems", timeout=30)
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") != "OK":
        raise RuntimeError("Codeforces returned an unsuccessful API response.")

    problems = payload.get("result", {}).get("problems", [])
    stats = payload.get("result", {}).get("problemStatistics", [])
    solved_by_key = {
        f"{x.get('contestId')}-{x.get('index')}": x.get("solvedCount", 0)
        for x in stats
    }

    count = 0
    with transaction.atomic():
        for p in problems[: min(int(limit), 5000)]:
            cid, index = p.get("contestId"), p.get("index")
            if cid is None or not index or not p.get("name"):
                continue
            rating = p.get("rating") or 0
            difficulty = (
                "EASY" if rating < 1300 else "MEDIUM" if rating < 1900 else "HARD"
            )
            tags = p.get("tags") or []
            _upsert(
                {
                    "platform": "CODEFORCES",
                    "external_id": f"{cid}-{index}",
                    "number": f"{cid}{index}",
                    "title": p["name"],
                    "difficulty": difficulty,
                    "topic": tags[0] if tags else "Algorithms",
                    "tags": tags[:12],
                    "score": solved_by_key.get(f"{cid}-{index}", 0),
                    "url": f"https://codeforces.com/problemset/problem/{cid}/{index}",
                }
            )
            count += 1
    return count


def _hackerrank_model_to_item(model, fallback_track="Coding"):
    if not isinstance(model, dict):
        return None

    challenge = model.get("challenge") if isinstance(model.get("challenge"), dict) else model
    slug = str(
        challenge.get("slug")
        or challenge.get("ch_slug")
        or challenge.get("challenge_slug")
        or ""
    ).strip()
    title = str(
        challenge.get("name")
        or challenge.get("title")
        or challenge.get("challenge_name")
        or ""
    ).strip()
    if not slug or not title:
        return None

    difficulty = (
        challenge.get("difficulty_name")
        or challenge.get("difficulty")
        or challenge.get("difficulty_label")
        or "MEDIUM"
    )

    success = _safe_percent(
        challenge.get("success_ratio")
        or challenge.get("success_rate")
        or challenge.get("successRatio")
    )

    track_obj = challenge.get("track") if isinstance(challenge.get("track"), dict) else {}
    topic = str(
        track_obj.get("name")
        or track_obj.get("track_name")
        or challenge.get("track_name")
        or challenge.get("subdomain_name")
        or fallback_track
    ).strip()

    return {
        "platform": "HACKERRANK",
        "external_id": slug,
        "number": str(challenge.get("id") or challenge.get("challenge_id") or slug),
        "title": title,
        "difficulty": _difficulty(difficulty),
        "success_rate": success,
        "topic": topic[:100] or "Coding",
        "url": f"https://www.hackerrank.com/challenges/{slug}/problem",
    }


def _sync_hackerrank_rest(session, limit):
    """
    HackerRank's practice pages use public JSON endpoints to load challenge cards.
    This is much more reliable than scraping only the first rendered HTML page.
    """
    count = 0
    seen = set()
    last_error = None

    for track in HACKERRANK_TRACKS:
        if count >= limit:
            break
        offset = 0
        batch_size = min(50, max(10, limit - count))

        while count < limit:
            url = f"https://www.hackerrank.com/rest/contests/master/tracks/{track}/challenges"
            try:
                response = session.get(
                    url,
                    params={"offset": offset, "limit": batch_size},
                    headers={
                        "Accept": "application/json,text/plain,*/*",
                        "Referer": f"https://www.hackerrank.com/domains/{track}",
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    timeout=30,
                )
                response.raise_for_status()
                payload = response.json()
            except Exception as exc:
                last_error = exc
                break

            models = (
                payload.get("models")
                or payload.get("challenges")
                or payload.get("data")
                or []
            )
            if isinstance(models, dict):
                models = models.get("models") or models.get("items") or []
            if not isinstance(models, list) or not models:
                break

            added_this_page = 0
            with transaction.atomic():
                for model in models:
                    item = _hackerrank_model_to_item(model, track.replace("-", " ").title())
                    if not item or item["external_id"] in seen:
                        continue
                    seen.add(item["external_id"])
                    _upsert(item)
                    count += 1
                    added_this_page += 1
                    if count >= limit:
                        break

            if count >= limit:
                break
            if added_this_page == 0:
                break

            total = payload.get("total") or payload.get("total_count") or payload.get("count")
            offset += len(models)
            if len(models) < batch_size:
                break
            try:
                if total is not None and offset >= int(total):
                    break
            except (TypeError, ValueError):
                pass

    return count, last_error, seen


def _hackerrank_slugs_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    found = []
    seen = set()
    pattern = re.compile(r"^/challenges/([^/?#]+)(?:/problem)?(?:[?#].*)?$")
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        parsed_path = urlparse(urljoin("https://www.hackerrank.com", href)).path
        match = pattern.match(parsed_path)
        if not match:
            continue
        slug = match.group(1)
        if slug not in seen:
            seen.add(slug)
            found.append(slug)
    return found


def _hackerrank_detail(session, slug):
    try:
        response = session.get(
            f"https://www.hackerrank.com/rest/contests/master/challenges/{slug}",
            headers={"Accept": "application/json,text/plain,*/*"},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        model = payload.get("model") or payload.get("challenge") or payload
        return _hackerrank_model_to_item(model)
    except Exception:
        return None


def _sync_hackerrank_html_fallback(session, limit, exclude_slugs=None):
    """
    Fallback for deployments where the list JSON endpoint changes.

    Important fix: challenge links currently include `/problem`; the old regex
    only accepted `/challenges/<slug>` and therefore imported zero rows.
    """
    count = 0
    seen = set(exclude_slugs or ())
    errors = []

    for track in HACKERRANK_TRACKS:
        if count >= limit:
            break
        try:
            response = session.get(
                f"https://www.hackerrank.com/domains/{track}",
                timeout=30,
                headers={"Referer": "https://www.hackerrank.com/dashboard"},
            )
            response.raise_for_status()
        except Exception as exc:
            errors.append(str(exc))
            continue

        for slug in _hackerrank_slugs_from_html(response.text):
            if slug in seen:
                continue
            seen.add(slug)
            item = _hackerrank_detail(session, slug)
            if item is None:
                # Keep a usable link even if the detail endpoint is temporarily unavailable.
                item = {
                    "platform": "HACKERRANK",
                    "external_id": slug,
                    "number": slug,
                    "title": slug.replace("-", " ").title(),
                    "difficulty": "MEDIUM",
                    "topic": track.replace("-", " ").title(),
                    "url": f"https://www.hackerrank.com/challenges/{slug}/problem",
                }
            _upsert(item)
            count += 1
            if count >= limit:
                break

    return count, errors


def sync_hackerrank(limit=1000):
    limit = max(1, min(int(limit), 5000))
    session = _session()

    count, rest_error, rest_seen = _sync_hackerrank_rest(session, limit)
    if count >= limit:
        return count

    # If REST returned only part of the catalog or no catalog, add anything that
    # can be discovered from the public practice pages.
    fallback_count, fallback_errors = _sync_hackerrank_html_fallback(
        session, limit - count, exclude_slugs=rest_seen
    )
    count += fallback_count

    if count == 0:
        detail = str(rest_error) if rest_error else "; ".join(fallback_errors[-2:])
        raise RuntimeError(
            "HackerRank was reachable but no challenge links could be imported. "
            "The upstream catalog may be blocking server-side requests."
            + (f" Details: {detail}" if detail else "")
        )
    return count


def _parse_codechef_rows(html):
    """Extract CodeChef problem code/name/rating from the server-rendered old practice table."""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()
    href_pattern = re.compile(r"/problems/([A-Za-z0-9_-]+)(?:/)?(?:[?#].*)?$")

    for row in soup.find_all("tr"):
        anchors = row.find_all("a", href=True)
        problem_anchor = None
        code = None
        for anchor in anchors:
            path = urlparse(urljoin("https://www.codechef.com", anchor.get("href", ""))).path
            match = href_pattern.search(path)
            if match:
                problem_anchor = anchor
                code = match.group(1).upper()
                break
        if not problem_anchor or not code or code in seen:
            continue

        cells = [" ".join(cell.get_text(" ", strip=True).split()) for cell in row.find_all("td")]
        title = ""
        rating = None

        # Old practice table columns are Code | Name | Submission | Difficulty | Contest Code.
        # Use the header layout when available, but keep fallbacks so minor markup changes do not
        # break the importer.
        code_index = next((i for i, text in enumerate(cells) if text.upper() == code), None)
        if code_index is not None and code_index + 1 < len(cells):
            title = cells[code_index + 1].strip()
            if code_index + 3 < len(cells):
                rating_match = re.search(r"\b(\d{1,4})\b", cells[code_index + 3])
                if rating_match:
                    rating = int(rating_match.group(1))

        anchor_text = " ".join(problem_anchor.get_text(" ", strip=True).split())
        if not title or title.upper() == code:
            title = anchor_text if anchor_text and anchor_text.upper() != code else code

        if rating is None:
            # Difficulty ratings are normally 0..5000. Scan from the right so submission counts
            # (often much larger) are less likely to be mistaken for a rating.
            for text in reversed(cells):
                for token in reversed(re.findall(r"\b\d{1,4}\b", text.replace(",", ""))):
                    value = int(token)
                    if 0 <= value <= 5000:
                        rating = value
                        break
                if rating is not None:
                    break

        if not title:
            continue

        seen.add(code)
        results.append({"code": code, "title": title, "rating": rating})

    return results


def sync_codechef(limit=5000):
    """
    Import CodeChef's public Practice catalog.

    The previous implementation scraped https://www.codechef.com/practice, which is
    now primarily a JavaScript landing page and frequently contains no direct problem
    anchors in the server response. The old practice table is server-rendered and
    supports pagination, so it is a more dependable metadata source.
    """
    limit = max(1, min(int(limit), 5000))
    session = _session()
    requested_page_size = 100
    actual_page_size = requested_page_size
    seen = set()
    count = 0
    page = 0
    last_error = None
    total_available = None

    while count < limit:
        try:
            response = session.get(
                "https://www.codechef.com/practice-old",
                params={
                    "end_rating": 4999,
                    "group": "all",
                    "hints": 0,
                    "limit": actual_page_size,
                    "page": page,
                    "search": "",
                    "sort_by": "difficulty_rating",
                    "sort_order": "asc",
                    "start_rating": 0,
                    "tags": "",
                    "topic": "",
                    "video_editorial": 0,
                    "wa_enabled": 1,
                },
                headers={"Referer": "https://www.codechef.com/practice"},
                timeout=35,
            )
            response.raise_for_status()
        except Exception as exc:
            last_error = exc
            break

        rows = _parse_codechef_rows(response.text)
        if not rows and page == 0 and actual_page_size != 20:
            # Some deployments cap/ignore a larger requested page size. Retry with
            # the same size used by CodeChef's own old Practice UI.
            actual_page_size = 20
            continue
        if not rows:
            break

        total_match = re.search(r"\bof\s+([0-9,]+)\b", BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True), re.I)
        if total_match:
            try:
                total_available = int(total_match.group(1).replace(",", ""))
            except ValueError:
                total_available = None

        # If CodeChef returned fewer rows than requested but says there are more,
        # use the actual row count as the next page size instead of stopping early.
        if page == 0 and len(rows) < actual_page_size and total_available and total_available > len(rows):
            actual_page_size = len(rows)

        added_this_page = 0
        with transaction.atomic():
            for item in rows:
                code = item["code"]
                if code in seen:
                    continue
                seen.add(code)
                _upsert(
                    {
                        "platform": "CODECHEF",
                        "external_id": code,
                        "number": code,
                        "title": item["title"],
                        "difficulty": _difficulty_from_rating(item.get("rating")),
                        "topic": "CodeChef Practice",
                        "tags": ([f"rating:{item['rating']}"] if item.get("rating") is not None else []),
                        "url": f"https://www.codechef.com/problems/{code}",
                    }
                )
                count += 1
                added_this_page += 1
                if count >= limit:
                    break

        if added_this_page == 0:
            break
        page += 1
        if total_available is not None and page * actual_page_size >= total_available:
            break
        if total_available is None and len(rows) < actual_page_size:
            break

        # Safety guard if the upstream endpoint starts repeating pages forever.
        if page > math.ceil(limit / max(actual_page_size, 1)) + 20:
            break

    if count == 0:
        raise RuntimeError(
            "CodeChef was reachable but no Practice problems could be imported. "
            "The upstream Practice page may have changed or blocked server-side requests."
            + (f" Details: {last_error}" if last_error else "")
        )
    return count


def sync_platform(platform, limit=5000):
    platform = str(platform or "").upper().strip()
    if platform == "LEETCODE":
        return sync_leetcode(limit)
    if platform == "CODEFORCES":
        return sync_codeforces(limit)
    if platform == "HACKERRANK":
        return sync_hackerrank(limit)
    if platform == "CODECHEF":
        return sync_codechef(limit)
    if platform == "GEEKSFORGEEKS":
        raise RuntimeError(
            "GeeksforGeeks live catalog sync is not enabled. "
            "Add approved question links through Management → External Coding."
        )
    raise RuntimeError("Unsupported platform.")
