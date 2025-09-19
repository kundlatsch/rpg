from django.contrib import admin
from .models import TasksConfig, CharacterJobProgress, Job  # seus models

admin.site.register(TasksConfig)
admin.site.register(CharacterJobProgress)
admin.site.register(Job)
