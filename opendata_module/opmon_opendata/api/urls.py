from django.urls import include, path
from . import views

urlpatterns = [
    path('heartbeat/', views.heartbeat),
    path('daily_logs/', views.get_daily_logs),
    path('logs_sample/', views.get_preview_data),
    path('date_range/', views.get_date_range),
    path('column_data/', views.get_column_data)
]
