from django.contrib import admin
from .models import TasksConfig, Job, ProfessionType, Hunt, HuntMonster

admin.site.register(TasksConfig)
admin.site.register(Job)
admin.site.register(ProfessionType)
admin.site.register(Hunt)
admin.site.register(HuntMonster)

