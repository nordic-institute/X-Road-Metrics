from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.index),
    path('get_datatable_frame/', views.get_datatable_frame),
]
