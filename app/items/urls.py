from django.urls import path
from .views import inventory_view, equip_item, market_view, buy_item, sell_item, cancel_listing, store_view, store_buy, store_sell

urlpatterns = [
    path('inventory/', inventory_view, name='inventory'),
    path("inventory/equip/", equip_item, name="equip_item"),
    path("market/", market_view, name="market"),
    path("market/buy/", buy_item, name="buy_item"),
    path("market/cancel/", cancel_listing, name="cancel_listing"),
    path("market/sell/", sell_item, name="sell_item"),
    path("store/", store_view, name="store"),
    path("store/buy/", store_buy, name="store_buy"),
    path("store/sell/", store_sell, name="store_sell"),
]