from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('historico/', views.historico, name='historico'),
    path('api/solutions/', views.api_solutions, name='api_solutions'),
]
