from django.contrib import admin
from .models import TasksConfig, Job, ProfessionType  # seus models

admin.site.register(TasksConfig)
admin.site.register(Job)
admin.site.register(ProfessionType)
