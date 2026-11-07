from django.urls import path
from . import views

urlpatterns = [
    path('home', views.index, name='index'),  # Make sure this exists
    path('login', views.login_view, name='login'),
    path('signup', views.signup_view, name='signup'),
    path('api/generate-etude/', views.generate_etude, name='generate_etude'),

]