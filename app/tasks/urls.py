from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("create/", views.create_character, name="create_character"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("signup/", views.signup, name="signup"),
    path("training/", views.training, name="training"),
    path("training/start/", views.start_training, name="start_training"),
    path("training/end/", views.end_training, name="end_training"),
    path("resting/", views.resting, name="resting"),
    path("resting/start/", views.start_resting, name="start_resting"),
    path("resting/end/", views.end_resting, name="end_resting"),
    path("jobs/", views.jobs_list, name="jobs_list"),
    path("jobs/start/<int:job_id>/", views.start_job, name="start_job"),
    path("job/end/<int:job_id>/", views.end_job, name="end_job"),
    path("jobs/progress/", views.job_in_progress, name="job_in_progress"),
    path("hunt/", views.hunts_list, name="hunts_list"),
    path("hunt/start/<int:hunt_id>/", views.start_hunt, name="start_hunt"),
    path("hunt/end/<int:hunt_id>/", views.end_hunt, name="end_hunt"),
    path("hunt/progress/", views.hunt_in_progress, name="hunt_in_progress"),
]
