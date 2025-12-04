from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home, name='home'),
    path('performance/', views.performance, name='performance'),
    path('metrics/', views.metrics, name='metrics'),
    path('day-of-week/', views.day_of_week, name='day_of_week'),
    path('strategy-images/', views.strategy_images, name='strategy_images'),
    path('purchase/', views.purchase, name='purchase'),
    path('checkout/', views.checkout, name='checkout'),
    # Trial download / start endpoint
    path(
        'download-trial/<str:strategy_name>/',
        views.download_trial,
        name='download_trial',
    ),
    path('news/', views.news, name='news'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
]

