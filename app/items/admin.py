from django.contrib import admin
from .models import Item, Equipment, Consumable, Material, InventoryItem, PassiveSkill, PassiveEffect

admin.site.register(Item)
admin.site.register(Equipment)
admin.site.register(Consumable)
admin.site.register(InventoryItem)
admin.site.register(PassiveSkill)
admin.site.register(PassiveEffect)
