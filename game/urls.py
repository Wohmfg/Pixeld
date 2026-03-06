from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('puzzle/<str:date_str>/', views.past_puzzle, name='past_puzzle'),
    path('image/<str:date_str>/<int:level>/', views.get_image, name='get_image'),
    path('guess/', views.submit_guess, name='submit_guess'),
]
