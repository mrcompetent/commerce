# cart/context_processors.py
from .utils import get_cart_for_request


def cart_summary(request):
    """
    Adds cart_count and cart_total to every template,
    for header/bottom-nav badges, etc.
    """
    cart = get_cart_for_request(request)
    if not cart:
        return {"cart_count": 0, "cart_total": 0}

    return {
        "cart_count": cart.item_count,
        "cart_total": cart.total_amount,
    }
