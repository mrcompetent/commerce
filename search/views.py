from django.db.models import Q
from django.shortcuts import render
from django.views.decorators.http import require_GET
from difflib import SequenceMatcher

from store.models import Product  # adjust if your app name differs


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _fuzzy_products(base_qs, query: str, *, limit: int = 12, pool: int = 4000):
    """
    Returns (qs, did_you_mean_string, best_score)
    """
    query_l = (query or "").strip().lower()
    if not query_l:
        return base_qs.none(), None, 0.0

    # Candidate pool (names only to keep it fast on SQLite)
    candidates = list(base_qs.values("id", "name")[:pool])

    scored = []
    for row in candidates:
        name = row["name"] or ""
        name_l = name.lower()

        # Base similarity
        score = _similarity(query_l, name_l)

        # Boost if query matches start of any word (helps: "marvelos" -> "marvelous")
        if any(w.startswith(query_l) for w in name_l.split()):
            score += 0.15

        scored.append((score, row["id"], name))

    scored.sort(reverse=True, key=lambda x: x[0])

    # threshold (tuneable)
    threshold = 0.55
    best = [x for x in scored if x[0] >= threshold][:limit]

    if not best:
        return base_qs.none(), None, 0.0

    best_name = best[0][2]
    best_score = best[0][0]
    best_ids = [x[1] for x in best]

    return base_qs.filter(id__in=best_ids), best_name, best_score


@require_GET
def search_view(request):
    q = (request.GET.get("q") or "").strip()

    # ✅ Base pool: only ACTIVE products
    base_qs = (
        Product.objects
        .filter(status=Product.ProductStatus.ACTIVE)
        .select_related("category")
        .prefetch_related("colors", "sizes")
    )

    products = base_qs.none()
    did_you_mean = None
    used_fuzzy = False
    best_score = 0.0

    if q:
        # ✅ Normal search first
        products = (
            base_qs.filter(
                Q(name__icontains=q) |
                Q(sku__icontains=q) |
                Q(category__name__icontains=q) |
                Q(short_description__icontains=q) |
                Q(description__icontains=q)
            )
            .distinct()
        )

        # ✅ Fuzzy fallback if nothing found
        if not products.exists():
            used_fuzzy = True
            products, did_you_mean, best_score = _fuzzy_products(base_qs, q, limit=12)

    context = {
        "query": q,
        "products": products[:24],  # show up to 24
        "count": products.count() if q else 0,
        "did_you_mean": did_you_mean,
        "used_fuzzy": used_fuzzy,
        "best_score": best_score,
    }
    return render(request, "search_results.html", context)
