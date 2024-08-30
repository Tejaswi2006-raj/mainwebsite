from django.contrib import admin
from django.urls import include, path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('about', views.about, name='about'),
    path('email', views.email, name='email'),
    path('contact', views.contact, name='contact'),
    path('sitemap', views.sitemap, name='sitemap'),
    path('events', views.events, name='events'),
    path('admin/events', views.adminEvents, name = 'adminEvents'),
    path('admin/events/create', views.adminEventsCreate, name = 'adminEventsCreate'),
    path('admin/events/image/add/<uuid:event_id>', views.add_image, name = 'add_image'),
    path('admin/events/status/change/<uuid:event_id>', views.change_event, name = 'change_event'),
    path('admin/events/invoices/<uuid:event_id>', views.invoices, name = "invoices"),
    path('buy-tickets/<uuid:event_id>/', views.buy_tickets, name='buy_tickets'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('tickets/show', views.show_tickets, name='show_tickets'),
    path('tickets/verify', views.verify_tickets, name='verify_tickets'),
    path('login', views.login_view, name='login'),
    path('payment/confirmation/<uuid:invoice_id>', views.payment_success, name='payment_success'),
    path('payment/<uuid:invoice_id>/', views.payment_page, name='payment_page'),
]