from django.urls import path, re_path
from . import views

urlpatterns = [
    # Server-rendered pages
    path('login', views.login_view, name='login'),
    path('signup', views.signup_view, name='signup'),

    # API
    path('api/generate-etude/', views.generate_etude, name='generate_etude'),

    # Everything else is a React page (routes live in frontend/src/App.js),
    # so new React pages need no change here. Keep this last.
    path('home', views.index, name='index'),
    re_path(r'^(?!api/|admin/|static/).*$', views.index),
]
