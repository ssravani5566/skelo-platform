from urllib.parse import urlparse

PLATFORM_CHOICES = (
    ("LEETCODE", "LeetCode"),
    ("HACKERRANK", "HackerRank"),
    ("CODECHEF", "CodeChef"),
    ("CODEFORCES", "Codeforces"),
    ("GEEKSFORGEEKS", "GeeksforGeeks"),
)

PLATFORM_HOME = {
    "LEETCODE": "https://leetcode.com/problemset/all/",
    "HACKERRANK": "https://www.hackerrank.com/domains/algorithms",
    "CODECHEF": "https://www.codechef.com/practice",
    "CODEFORCES": "https://codeforces.com/problemset",
    "GEEKSFORGEEKS": "https://www.geeksforgeeks.org/explore",
}

PLATFORM_HOSTS = {
    "LEETCODE": {"leetcode.com", "leetcode.cn"},
    "HACKERRANK": {"hackerrank.com"},
    "CODECHEF": {"codechef.com"},
    "CODEFORCES": {"codeforces.com"},
    "GEEKSFORGEEKS": {"geeksforgeeks.org"},
}


def platform_label(platform):
    return dict(PLATFORM_CHOICES).get(platform, platform or "External")


def parse_external_tags(tags):
    """Read external metadata from the existing Problem.tags JSON field."""
    meta = {}
    if isinstance(tags, dict):
        for key in ("external", "platform", "url", "id", "number", "acceptance", "success_rate", "premium", "topics", "score"):
            if key in tags:
                meta[key] = tags[key]
        return meta
    for item in tags or []:
        if not isinstance(item, str):
            continue
        if item == "external":
            meta["external"] = True
        elif item.startswith("platform:"):
            meta["platform"] = item.split(":", 1)[1].strip().upper()
        elif item.startswith("url:"):
            meta["url"] = item.split(":", 1)[1].strip()
        elif item.startswith("external_id:"):
            meta["id"] = item.split(":", 1)[1].strip()
        elif item.startswith("number:"):
            meta["number"] = item.split(":", 1)[1].strip()
        elif item.startswith("acceptance:"):
            meta["acceptance"] = item.split(":", 1)[1].strip()
        elif item.startswith("success_rate:"):
            meta["success_rate"] = item.split(":", 1)[1].strip()
        elif item.startswith("premium:"):
            meta["premium"] = item.split(":", 1)[1].strip().lower() == "true"
        elif item.startswith("topics:"):
            meta["topics"] = [x.strip() for x in item.split(":", 1)[1].split(",") if x.strip()]
        elif item.startswith("score:"):
            meta["score"] = item.split(":", 1)[1].strip()
    return meta


def is_external_problem(problem):
    meta = parse_external_tags(problem.tags)
    return bool(meta.get("external") and meta.get("platform") and meta.get("url"))


def build_external_tags(platform, url, external_id="", extra_tags=None, **metadata):
    values = ["external", f"platform:{platform}", f"url:{url}"]
    if external_id:
        values.append(f"external_id:{external_id}")
    if metadata.get("number") not in (None, ""):
        values.append(f"number:{metadata['number']}")
    if metadata.get("acceptance") not in (None, ""):
        values.append(f"acceptance:{metadata['acceptance']}")
    if metadata.get("success_rate") not in (None, ""):
        values.append(f"success_rate:{metadata['success_rate']}")
    if metadata.get("premium") is not None:
        values.append(f"premium:{str(bool(metadata['premium'])).lower()}")
    topics = metadata.get("topics") or []
    if topics:
        values.append("topics:" + ",".join(str(x) for x in topics[:12]))
    if metadata.get("score") not in (None, ""):
        values.append(f"score:{metadata['score']}")
    for tag in extra_tags or []:
        if isinstance(tag, str) and not tag.startswith(("external", "platform:", "url:", "external_id:", "number:", "acceptance:", "success_rate:", "premium:", "topics:", "score:")):
            values.append(tag)
    return values


def validate_platform_url(platform, url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("External problem URL must be a valid HTTPS URL.")
    host = (parsed.hostname or "").lower()
    allowed = PLATFORM_HOSTS.get(platform)
    if not allowed:
        raise ValueError("Unsupported external coding platform.")
    if not any(host == domain or host.endswith("." + domain) for domain in allowed):
        raise ValueError(f"The URL does not belong to the selected {platform_label(platform)} platform.")


def detect_platform(url):
    host = (urlparse(url).hostname or "").lower()
    for platform, domains in PLATFORM_HOSTS.items():
        if any(host == domain or host.endswith("." + domain) for domain in domains):
            return platform
    return None
