"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from pipelines.views import help_view

admin.site.site_url = "/pipelines/"
admin.site.site_header = "Anonimizáció admin"
admin.site.index_title = "Modellek"

urlpatterns = [
    path('pipelines/', include('pipelines.urls')),
    path('alerts/', include('alerts.urls')),
    path('help/', help_view, name='help'),
    path('admin/', admin.site.urls),
]
