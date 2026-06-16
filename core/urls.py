from django.urls import path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from . import views
from django.shortcuts import render

urlpatterns = [
    # --- AUTHENTIFICATION (NATIVE DJANGO) ---
    # Pas besoin de coder ces vues, Django s'en charge. 
    # Il te faudra juste créer un template HTML dans 'registration/login.html'
    path('connexion/', auth_views.LoginView.as_view(), name='login'),
    path('deconnexion/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin/', admin.site.urls),


    # --- ENCHAINEMENT DES ANNONCES ---
    path('annonce/deposer/', views.deposer_annonce_view, name='deposer_annonce'),
    path('annonce/<int:annonce_id>/valider/', views.valider_annonce_view, name='valider_annonce'),
    path('annonce/<int:annonce_id>/refuser/', views.refuser_annonce_view, name='refuser_annonce'),
    path('annonce/<int:annonce_id>/retirer/', views.retirer_annonce_view, name='retirer_annonce'),


    # --- DEMANDES DE VISITE ---
    path('annonce/<int:annonce_id>/demander-visite/', views.creer_demande_visite_view, name='creer_demande_visite'),
    path('demande-visite/<int:demande_id>/traiter/<str:decision>/', views.traiter_demande_visite_view, name='traiter_demande_visite'),


    # --- GESTION DES FAVORIS ---
    path('annonce/<int:annonce_id>/favori/ajouter/', views.ajouter_favori_view, name='ajouter_favori'),
    path('annonce/<int:annonce_id>/favori/retirer/', views.retirer_favori_view, name='retirer_favori'),


    # --- URLS DE REDIRECTION (Pour éviter les crashs au clic) ---
    # Pense à créer des vues simples (ou simples renders) pour ces pages de listes :
    path('mon-espace/bailleur/annonces/', views.mes_annonces_bailleur, name='mes_annonces_bailleur'),
    path('espace-agent/', views.agent_dashboard, name='agent_dashboard'),
    path('espace-agent/annonces-en-attente/', views.annonces_en_attente, name='liste_annonces_en_attente'),
    path('espace-agent/demandes-visites/', views.liste_demandes_agent, name='liste_demandes_agent'),
    path('espace-manager/toutes-les-annonces/', views.liste_utilisateurs, name='toutes_les_annonces_manager'),
    path('annonce/<int:annonce_id>/', views.detail_annonce, name='detail_annonce'),
    path('mes-favoris/', views.mes_favoris_client, name='mes_favoris_client'),

    # --- ACCÈS PUBLIC ---
    path('', views.accueil, name='accueil'),
    path('annonces/', views.liste_annonces, name='liste_annonces'),

    # --- INSCRIPTION ---
    path('inscription/', views.inscription, name='inscription'),

    # --- ESPACES ---
    path('bailleur/annonces/<int:annonce_id>/modifier/', views.modifier_annonce, name='modifier_annonce'),
    path('bailleur/annonces/<int:annonce_id>/supprimer/', views.supprimer_annonce, name='supprimer_annonce'),
    path('agent/clients/', views.clients_affectes, name='clients_affectes'),
    path('manager/dashboard/', views.dashboard, name='dashboard'),
    path('manager/utilisateurs/', views.liste_utilisateurs, name='liste_utilisateurs'),
    path('manager/affecter/', views.affecter_client, name='affecter_client'),
    path('client/demandes/', views.mes_demandes_client, name='mes_demandes_client'),
    path('redirect/', views.redirect_after_login, name='redirect_after_login'),
    path('manager/utilisateurs/<int:user_id>/supprimer/', views.supprimer_utilisateur, name='supprimer_utilisateur'), 
]