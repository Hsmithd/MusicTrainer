from django.urls import path
from . import views

urlpatterns = [
    # Pages handled by the React app. Each React route (frontend/src/App.js)
    # needs a matching entry here so refreshing the page doesn't 404.
    path('', views.index),
    path('home', views.index, name='index'),
    path('profile', views.index, name='profile'),

    # Server-rendered pages
    path('login', views.login_view, name='login'),
    path('signup', views.signup_view, name='signup'),

    # API
    path('api/generate-etude/', views.generate_etude, name='generate_etude'),
]
