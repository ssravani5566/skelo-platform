from math import ceil
from rest_framework.response import Response


def _positive_int(value, default, maximum=None):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    parsed = max(parsed, 1)
    return min(parsed, maximum) if maximum else parsed


def paginated_response(request, items, serializer_class=None, *, total=None, page_size_default=20):
    """Return a predictable pagination envelope for querysets or already-serialized lists."""
    page = _positive_int(request.query_params.get("page", 1), 1)
    page_size = _positive_int(request.query_params.get("page_size", page_size_default), page_size_default, 100)
    if hasattr(items, "count") and not isinstance(items, list):
        total_count = items.count() if total is None else total
        start = (page - 1) * page_size
        values = items[start:start + page_size]
    else:
        values = list(items)
        total_count = len(values) if total is None else total
        start = (page - 1) * page_size
        values = values[start:start + page_size]
    data = serializer_class(values, many=True, context={"request": request}).data if serializer_class else values
    return Response({
        "count": total_count,
        "page": page,
        "page_size": page_size,
        "pages": ceil(total_count / page_size) if total_count else 0,
        "results": data,
    })


def error_detail(message):
    return {"detail": message}
