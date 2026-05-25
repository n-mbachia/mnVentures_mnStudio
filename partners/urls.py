from django.urls import path
from . import views

app_name = "partners"

urlpatterns = [
    # ── Public ────────────────────────────────────────────────────────────────
    path("become-a-partner/",      views.become_partner,  name="become_partner"),
    path("become-a-partner/done/", views.apply_success,   name="apply_success"),
    path("submit-design/",         views.submit_design,   name="submit_design"),
    path("submit-design/done/",    views.submit_success,  name="submit_success"),

    # ── Staff dashboard ───────────────────────────────────────────────────────
    path("staff/partners/",                         views.admin_dashboard,             name="admin_dashboard"),
    path("staff/partners/application/<int:pk>/",    views.admin_application_detail,    name="admin_application_detail"),
    path("staff/partners/submission/<int:pk>/",     views.admin_submission_detail,     name="admin_submission_detail"),
]
