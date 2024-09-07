# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('candidatelogin/', views.candidate_login, name='candidatelogin'),
    path('candidatelist/', views.candidate_list, name='candidatelist'),
    path('adminpage/', views.admin_page, name='adminpage'),
    path('cast_vote/', views.cast_vote, name='cast_vote'),
    path('adminlogin/', views.admin_login, name='adminlogin')
]
