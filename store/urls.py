""" mnventure/store/urls.py """

from django.urls import path, include
from . import views 

app_name = 'store'

urlpatterns = [
    # ── Store ────────────────────────────────────────────
    path('',                        views.home,           name='home'),
    path('about/',                  views.about,          name='about'),
    path('terms/',                  views.terms,          name='terms'),
    path('privacy/',                views.privacy,        name='privacy'),
    path('enquiry/',                views.enquiry,        name='enquiry'),
    path('api/products/',           views.product_api,    name='product_api'),
    path('products/<slug:slug>/',   views.product_detail, name='product_detail'),

    # ── Auctions ─────────────────────────────────────────
    path('auctions/',                            views.auction_list,   name='auction_list'),
    path('auctions/<slug:slug>/',                views.auction_detail, name='auction_detail'),
    path('auctions/<slug:slug>/bid/',            views.place_bid,      name='place_bid'),
    path('auctions/<slug:slug>/proxy-bid/',      views.set_proxy_bid,  name='set_proxy_bid'),
    path('auctions/<slug:slug>/status/',         views.auction_status, name='auction_status'),
    path('auctions/<slug:slug>/pay/',            views.initiate_payment, name='initiate_payment'),

    # ── Bidder dashboard ─────────────────────────────────
    path('my-bids/',                             views.my_bids,        name='my_bids'),

    # ── Payments ─────────────────────────────────────────
    path('payments/mpesa/callback/',             views.mpesa_callback,  name='mpesa_callback'),
    path('payments/status/<uuid:reference>/',    views.payment_status,  name='payment_status'),
    path('payments/invoice/<uuid:reference>/',   views.invoice_view,    name='invoice_view'),
]
