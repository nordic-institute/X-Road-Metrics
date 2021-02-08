"""
Opmon Opendata URL Configuration
"""
from django.urls import include, path
from .gui import urls as gui_urls
from .api import urls as api_urls

base_urlpatterns = [
    path('', include(gui_urls.urlpatterns)),
    path('api/', include(api_urls.urlpatterns))
]

urlpatterns = [
    path('', include(base_urlpatterns)),
    path('<slug:profile>/', include(base_urlpatterns))
]
