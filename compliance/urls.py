"""compliance/urls.py"""
from django.urls import path
from . import views

app_name = "compliance"

urlpatterns = [
    # ── Main dashboard ────────────────────────────────────────────────────────
    path('dashboard/',			views.dashboard,	     name='dashboard'),

    # ── Sales portal ─────────────────────────────────────────────────────────
    path("sales/",                      views.sales_portal,          name="sales_portal"),
    path("sales/<int:pk>/edit/",        views.sales_edit,            name="sales_edit"),
    path("sales/<int:pk>/delete/",      views.sales_delete,          name="sales_delete"),
    path("sales/<int:pk>/etims/",       views.sales_toggle_etims,    name="sales_toggle_etims"),
    path("sales/<int:pk>/payment/",     views.sales_update_payment,  name="sales_update_payment"),

    # ── Quick-add endpoints (dashboard panel POSTs) ───────────────────────────
    path("add/purchase/",               views.add_purchase,          name="add_purchase"),
    path("add/expense/",                views.add_expense,           name="add_expense"),
    path("add/material-use/",           views.add_material_use,      name="add_material_use"),
    path("add/drawings/",               views.add_drawings,          name="add_drawings"),
]
