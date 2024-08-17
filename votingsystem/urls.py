# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('candidatelogin/', views.candidate_login, name='candidatelogin'),
    path('adminlogin/', views.admin_login, name='adminlogin')
]
