from django.urls import path

from async_downloads import views

app_name = "async_downloads"
urlpatterns = [
    path("ajax_update/", views.ajax_update, name="ajax_update"),
    path("ajax_clear_download/", views.ajax_clear_download, name="ajax_clear_download"),
]
