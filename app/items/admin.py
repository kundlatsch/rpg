from django.contrib import admin
from .models import Item, Equipment, Consumable, Material, InventoryItem

admin.site.register(Item)
admin.site.register(Equipment)
admin.site.register(Consumable)
admin.site.register(InventoryItem)
