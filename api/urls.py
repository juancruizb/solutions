from django.urls import path
from . import views

urlpatterns = [
    path('solutions/',            views.solutions_list,   name='api-v1-solutions'),
    path('solutions/<str:solution_id>/', views.solution_detail, name='api-v1-solution-detail'),
    path('topics/',               views.topics_list,      name='api-v1-topics'),
    path('cache/flush/',          views.cache_flush,      name='api-v1-cache-flush'),
]
