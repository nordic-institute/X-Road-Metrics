from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^daily_logs$', views.get_daily_logs, name='get_daily_logs'),
    url(r'^logs_sample$', views.get_preview_data, name='get_preview_data'),
    url(r'^date_range$', views.get_date_range, name='get_date_range'),
    url(r'^column_data$', views.get_column_data, name='get_column_data'),
]
