from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^update_incident_status/?', views.update_incident_status),
    url(r'^get_historic_incident_data_serverside/?', views.get_historic_incident_data_serverside),
    url(r'^get_incident_data_serverside/?', views.get_incident_data_serverside),
    url(r'^get_request_list/?', views.get_request_list),
    url(r'^get_incident_table_initialization_data/?', views.get_incident_table_initialization_data),
]
