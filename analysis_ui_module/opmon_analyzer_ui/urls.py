from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'index/?([a-zA-Z0-9]{0,10})/?', views.index),
    url(r'^update_incident_status/?([a-zA-Z0-9]{0,10})/?', views.update_incident_status),
    url(r'^get_historic_incident_data_serverside/?([a-zA-Z0-9]{0,10})/?', views.get_historic_incident_data_serverside),
    url(r'^get_incident_data_serverside/?([a-zA-Z0-9]{0,10})/?', views.get_incident_data_serverside),
    url(r'^get_request_list/?([a-zA-Z0-9]{0,10})/?', views.get_request_list),
    url(r'^get_incident_table_initialization_data/?([a-zA-Z0-9]{0,10})/?', views.get_incident_table_initialization_data),
]
