from django.contrib import admin
from django.urls import include, path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('about', views.about, name='about'),
    path('contact', views.contact, name='contact'),
    path('sitemap', views.sitemap, name='sitemap'),
    path('events', views.events, name='events'),
    path('admin/events', views.adminEvents, name = 'adminEvents'),
    path('admin/events/create', views.adminEventsCreate, name = 'adminEventsCreate'),
    path('admin/events/image/add/<uuid:event_id>', views.add_image, name = 'add_image'),
    path('admin/events/status/change/<uuid:event_id>', views.change_event, name = 'change_event'),
]