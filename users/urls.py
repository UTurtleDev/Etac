from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('collaborateur/inscription/', views.inscription_collaborateur, name='inscription_collaborateur'),
]
