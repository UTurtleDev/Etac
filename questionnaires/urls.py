from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Page d'accueil
    path('', views.home, name='home'),
    path('mentions-legales/', views.mentions_legales, name='mentions_legales'),

    # API
    path('api/validate-siren/', views.validate_siren, name='validate_siren'),

    # Parcours CLIENT
    path('client/introduction/', views.client_introduction, name='client_introduction'),
    path('client/identification/', views.client_identification, name='client_identification'),
    path('client/questionnaire/', views.client_questionnaire, name='client_questionnaire'),
    path('client/recapitulatif/', views.client_recapitulatif, name='client_recapitulatif'),
    path('get-comptables/', views.get_comptables, name='get_comptables'),

    # Parcours COLLABORATEUR - Authentification
    path('collaborateur/login/', auth_views.LoginView.as_view(
        template_name='questionnaires/collaborateur/login.html',
        redirect_authenticated_user=True
    ), name='collaborateur_login'),
    path('collaborateur/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Parcours COLLABORATEUR - Dashboard et questionnaires
    path('collaborateur/dashboard/', views.dashboard, name='dashboard'),
    path('collaborateur/identification/', views.collaborateur_identification, name='collaborateur_identification'),
    path('collaborateur/questionnaire/', views.collaborateur_questionnaire, name='collaborateur_questionnaire'),
    path('collaborateur/recapitulatif/', views.collaborateur_recapitulatif, name='collaborateur_recapitulatif'),
    path('collaborateur/voir/<str:siren>/', views.voir_questionnaire, name='voir_questionnaire'),

    # Actions - Édition, Suppression, Export
    path('collaborateur/archiver/<str:siren>/', views.archiver_entreprise, name='archiver_entreprise'),
    path('collaborateur/editer/<str:siren>/', views.editer_entreprise, name='editer_entreprise'),
    path('collaborateur/export-csv/', views.export_csv, name='export_csv'),
]
