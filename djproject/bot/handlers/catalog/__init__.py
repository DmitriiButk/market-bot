from .base import catalog_router
from . import categories, products, cart, checkout


from .categories import *
from .products import *
from .cart import *
from .checkout import *

__all__ = ["catalog_router"]