from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^get_datatable_frame$', views.get_datatable_frame, name='get_datatable_frame'),
]
