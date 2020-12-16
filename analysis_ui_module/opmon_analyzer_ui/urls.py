from django.urls import include, path
from . import views

base_urlpatterns = [
    path('', views.index),
    path('update_incident_status/', views.update_incident_status),
    path('get_historic_incident_data_serverside/', views.get_historic_incident_data_serverside),
    path('get_incident_data_serverside/', views.get_incident_data_serverside),
    path('get_request_list/', views.get_request_list),
    path('get_incident_table_initialization_data/', views.get_incident_table_initialization_data),
]

urlpatterns = [
    path('', include(base_urlpatterns)),
    path('<slug:profile>/', include(base_urlpatterns))
]
