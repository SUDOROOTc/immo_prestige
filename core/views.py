from core.models import Photo
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from .models import Annonce,DemandeVisite,Favori,Utilisateur,Agent,Client,Bailleur
from .services import AnnonceService ,DemandeVisiteService,FavoriService,UtilisateurService


def accueil(request):

    dernieres = Annonce.objects.filter(
        statut='PUBLIEE'
    ).order_by('-date_publication')[:6]

    villas = Annonce.objects.filter(
        statut='PUBLIEE',
        bien__type='VILLA'
    )[:3]

    terrains = Annonce.objects.filter(
        statut='PUBLIEE',
        bien__type='TERRAIN'
    )[:3]

    appartements = Annonce.objects.filter(
        statut='PUBLIEE',
        bien__type='APPARTEMENT'
    )[:3]

    locations = Annonce.objects.filter(
        statut='PUBLIEE',
        option='LOCATION'
    )[:3]

    ventes = Annonce.objects.filter(
        statut='PUBLIEE',
        option='VENTE'
    )[:3]

    return render(
        request,
        'accueil.html',
        {
            'dernieres': dernieres,
            'villas': villas,
            'terrains': terrains,
            'appartements': appartements,
            'locations': locations,
            'ventes': ventes,
        }
    )


def liste_annonces(request):
    annonces = Annonce.objects.filter(statut='PUBLIEE').order_by('-date_publication')
    
    if request.GET.get('type'):
        annonces = annonces.filter(bien__type=request.GET.get('type'))
    if request.GET.get('usage'):
        annonces = annonces.filter(bien__usage=request.GET.get('usage'))
    if request.GET.get('option'):
        annonces = annonces.filter(option=request.GET.get('option'))
    if request.GET.get('ville'):
        annonces = annonces.filter(bien__ville__icontains=request.GET.get('ville'))
    
    return render(request, 'annonces/liste.html', {'annonces': annonces})

def detail_annonce(request, annonce_id):
    annonce = get_object_or_404(Annonce, id=annonce_id, statut='PUBLIEE')
    return render(request, 'annonces/detail.html', {'annonce': annonce})






def inscription(request):
    if request.method == 'POST':
        try:
            user = UtilisateurService.inscrire(
                role=request.POST.get('role'),
                username=request.POST.get('username'),
                email=request.POST.get('email'),
                password=request.POST.get('password'),
                telephone=request.POST.get('telephone'),
                nom=request.POST.get('nom'),
                prenom=request.POST.get('prenom')
            )
            login(request, user)
            messages.success(request, f"Bienvenue {user.first_name} ! Compte créé avec succès.")
            return redirect('accueil')
        except (DjangoPermissionDenied, ValueError) as e:
            messages.error(request, str(e))
    return render(request, 'inscription.html')


@login_required
def deposer_annonce_view(request):
    if request.method == 'POST':
        try:
            annonce = AnnonceService.deposer_annonce(
                bailleur=request.user,
                type_bien=request.POST.get('type'),
                usage=request.POST.get('usage'),
                superficie=float(request.POST.get('superficie', 0)),
                localisation=request.POST.get('localisation'),
                ville=request.POST.get('ville'),
                option=request.POST.get('option'),
                prix=float(request.POST.get('prix', 0)),
                description=request.POST.get('description')
            )
            for photo in request.FILES.getlist('photos'):
                Photo.objects.create(
                    bien=annonce.bien,
                    chemin_fichier=photo
                )
            messages.success(request, "Annonce déposée avec succès. En attente de validation.")
            return redirect('mes_annonces_bailleur')
        except (DjangoPermissionDenied, ValueError) as e:
            messages.error(request, str(e))
    return render(request, 'bailleur/deposer_annonce.html')

@login_required
def mes_annonces_bailleur(request):
    annonces = Annonce.objects.filter(
        bailleur=request.user.bailleur
    ).order_by('-date_publication')
    return render(request, 'bailleur/mes_annonces.html', {'annonces': annonces})

@login_required
def modifier_annonce(request, annonce_id):
    annonce = get_object_or_404(Annonce, id=annonce_id)
    if request.method == 'POST':
        try:
            AnnonceService.modifier_annonce(
                annonce=annonce,
                bailleur=request.user,
                option=request.POST.get('option'),
                prix=float(request.POST.get('prix', 0)),
                description=request.POST.get('description')
            )
            messages.success(request, "Annonce modifiée avec succès.")
            return redirect('mes_annonces_bailleur')
        except (DjangoPermissionDenied, ValueError) as e:
            messages.error(request, str(e))
    return render(request, 'bailleur/modifier_annonce.html', {'annonce': annonce})

@login_required
def valider_annonce_view(request, annonce_id):
    annonce = get_object_or_404(Annonce, id=annonce_id)
    try:
        AnnonceService.valider_annonce(annonce=annonce, agent=request.user)
        messages.success(request, f"Annonce #{annonce.id} validée et publiée.")
    except (DjangoPermissionDenied, ValueError) as e:
        messages.error(request, str(e))
    return redirect('liste_annonces_en_attente')

@login_required
def refuser_annonce_view(request, annonce_id):
    annonce = get_object_or_404(Annonce, id=annonce_id)
    try:
        AnnonceService.refuser_annonce(annonce=annonce, agent=request.user)
        messages.success(request, f"Annonce #{annonce.id} refusée.")
    except (DjangoPermissionDenied, ValueError) as e:
        messages.error(request, str(e))
    return redirect('liste_annonces_en_attente')

@login_required
def retirer_annonce_view(request, annonce_id):
    annonce = get_object_or_404(Annonce, id=annonce_id)
    try:
        AnnonceService.retirer_annonce(annonce=annonce, manager=request.user)
        messages.success(request, "Annonce retirée du site public.")
    except (DjangoPermissionDenied, ValueError) as e:
        messages.error(request, str(e))
    return redirect('toutes_les_annonces_manager')


@login_required
def supprimer_annonce(request, annonce_id):
    annonce = get_object_or_404(Annonce, id=annonce_id)
    if request.method == 'POST':
        try:
            AnnonceService.supprimer_annonce(annonce=annonce, bailleur=request.user)
            messages.success(request, "Annonce supprimée avec succès.")
            return redirect('mes_annonces_bailleur')
        except (DjangoPermissionDenied, ValueError) as e:
            messages.error(request, str(e))
    return render(request, 'bailleur/confirmer_suppression.html', {'annonce': annonce})


@login_required
def agent_dashboard(request):

    if not Agent.objects.filter(pk=request.user.pk).exists():
        messages.error(
            request,
            "Accès réservé aux agents."
        )
        return redirect('accueil')

    return render(
        request,
        'agent/dashboard.html'
    )

@login_required
def annonces_en_attente(request):

    if not Agent.objects.filter(pk=request.user.pk).exists():
        messages.error(
            request,
            "Accès réservé aux agents."
        )
        return redirect('accueil')

    annonces = Annonce.objects.filter(
        statut='EN_ATTENTE'
    ).order_by('-date_publication')

    return render(
        request,
        'agent/annonces_en_attente.html',
        {
            'annonces': annonces
        }
    )


@login_required
def liste_demandes_agent(request):
    """
    Liste les demandes de visite EN_ATTENTE
    des clients affectés à cet agent (EF-D2).
    """
    try:
        agent = Agent.objects.get(pk=request.user.pk)
    except Agent.DoesNotExist:
        messages.error(request, "Accès réservé aux agents.")
        return redirect('accueil')

    demandes = DemandeVisite.objects.filter(
        client__agent_affecte=agent,   # ← le bon filtre
        statut='EN_ATTENTE'
    ).select_related(
        'client', 'annonce', 'annonce__bien'
    ).order_by('-date_demande')

    return render(request, 'agent/demandes.html', {'demandes': demandes})



@login_required
def traiter_demande_visite_view(request, demande_id, decision):
    """
    Valide ou refuse une demande de visite (POST uniquement).
    """
    if request.method != 'POST':
        messages.error(request, "Méthode non autorisée.")
        return redirect('liste_demandes_agent')

    demande = get_object_or_404(DemandeVisite, id=demande_id)

    try:
        DemandeVisiteService.traiter_demande(
            demande=demande,
            agent=request.user,
            decision=decision
        )
        label = "validée" if decision == "VALIDEE" else "refusée"
        messages.success(request, f"Demande {label} avec succès.")
    except (DjangoPermissionDenied, ValueError) as e:
        messages.error(request, str(e))

    return redirect('liste_demandes_agent')


@login_required
def clients_affectes(request):
    try:
        # Récupère l'objet Agent correspondant à l'utilisateur connecté
        agent = Agent.objects.get(pk=request.user.pk)
        clients = Client.objects.filter(
            agent_affecte=agent
        ).order_by('username')
    except Agent.DoesNotExist:
        messages.error(request, "Accès réservé aux agents.")
        return redirect('accueil')
    
    return render(request, 'agent/clients.html', {'clients': clients})


@login_required
def mes_favoris_client(request):
    try:
        favoris = FavoriService.lister_favoris(user=request.user)
    except DjangoPermissionDenied as e:
        messages.error(request, str(e))
        favoris = []
    return render(request, 'client/favoris.html', {'favoris': favoris})


@login_required
def ajouter_favori_view(request, annonce_id):
    annonce = get_object_or_404(Annonce, id=annonce_id)
    try:
        FavoriService.ajouter_favori(user=request.user, annonce=annonce)
        messages.success(request, "Annonce ajoutée à vos favoris !")
    except (DjangoPermissionDenied, ValueError) as e:
        messages.warning(request, str(e))
    return redirect('detail_annonce', annonce_id=annonce.id)


@login_required
def retirer_favori_view(request, annonce_id):
    annonce = get_object_or_404(Annonce, id=annonce_id)
    try:
        FavoriService.retirer_favori(user=request.user, annonce=annonce)
        messages.success(request, "Annonce retirée de vos favoris.")
    except (DjangoPermissionDenied, ValueError) as e:
        messages.error(request, str(e))
    return redirect('mes_favoris_client')


@login_required
def creer_demande_visite_view(request, annonce_id):
    annonce = get_object_or_404(Annonce, id=annonce_id)
    try:
        DemandeVisiteService.creer_demande(client=request.user, annonce=annonce)
        messages.success(request, "Demande de visite transmise. Un agent va la traiter.")
    except (DjangoPermissionDenied, ValueError) as e:
        messages.warning(request, str(e))
    return redirect('detail_annonce', annonce_id=annonce.id)


@login_required
def mes_demandes_client(request):
    try:
        demandes = DemandeVisite.objects.filter(
            client=request.user.client
        ).order_by('-date_demande')
    except Exception:
        demandes = []
    return render(request, 'client/demandes.html', {'demandes': demandes})


@login_required
def dashboard(request):
    try:
        stats = UtilisateurService.get_statistiques(manager=request.user)
    except DjangoPermissionDenied as e:
        messages.error(request, str(e))
        return redirect('accueil')
    return render(request, 'manager/dashboard.html', {'stats': stats})


@login_required
def liste_utilisateurs(request):
    try:
        data = UtilisateurService.lister_utilisateurs(manager=request.user)
    except DjangoPermissionDenied as e:
        messages.error(request, str(e))
        return redirect('accueil')
    return render(request, 'manager/utilisateurs.html', data)


@login_required
def supprimer_utilisateur(request, user_id):
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    if request.method == 'POST':
        try:
            UtilisateurService.supprimer_utilisateur(manager=request.user, utilisateur=utilisateur)
            messages.success(request, "Compte supprimé avec succès.")
            return redirect('liste_utilisateurs')
        except (DjangoPermissionDenied, ValueError) as e:
            messages.error(request, str(e))
    return render(request, 'manager/confirmer_suppression.html', {'utilisateur': utilisateur})


@login_required
def affecter_client(request):
    if request.method == 'POST':
        try:
            client = get_object_or_404(Client, id=request.POST.get('client_id'))
            agent  = get_object_or_404(Agent, id=request.POST.get('agent_id'))
            UtilisateurService.affecter_client(manager=request.user, client=client, agent=agent)
            messages.success(request, f"{client.username} affecté à {agent.username}.")
            return redirect('liste_affectations')
        except (DjangoPermissionDenied, ValueError) as e:
            messages.error(request, str(e))
    try:
        data = UtilisateurService.lister_utilisateurs(manager=request.user)
    except DjangoPermissionDenied as e:
        messages.error(request, str(e))
        return redirect('accueil')
    return render(request, 'manager/affecter_client.html', data)




from core.models import Manager, Agent, Bailleur, Client

def redirect_after_login(request):
    user = request.user

    if Manager.objects.filter(pk=user.pk).exists():
        return redirect('dashboard')
    elif Agent.objects.filter(pk=user.pk).exists():
        return redirect('agent_dashboard')
    elif Bailleur.objects.filter(pk=user.pk).exists():
        return redirect('mes_annonces_bailleur')
    elif Client.objects.filter(pk=user.pk).exists():
        return redirect('dashboard_client')
    
    return redirect('accueil')

@login_required
def ajouter_annonce_agence(request):

    if request.method == 'POST':

        try:

            annonce= AnnonceService.ajouter_annonce_agence(
                agent=request.user,
                type_bien=request.POST.get('type'),
                usage=request.POST.get('usage'),
                superficie=float(
                    request.POST.get('superficie', 0)
                ),
                localisation=request.POST.get(
                    'localisation'
                ),
                ville=request.POST.get('ville'),
                option=request.POST.get('option'),
                prix=float(
                    request.POST.get('prix', 0)
                ),
                description=request.POST.get(
                    'description'
                )
            )
            for photo in request.FILES.getlist('photos'):

                Photo.objects.create(
                    bien=annonce.bien,
                    chemin_fichier=photo
                )
            messages.success(
                request,
                "Annonce d'agence publiée avec succès."
            )

            return redirect(
                'mes_annonces_agence'
            )

        except (
            DjangoPermissionDenied,
            ValueError
        ) as e:

            messages.error(
                request,
                str(e)
            )

    return render(
        request,
        'agent/ajouter_annonce.html'
    )



@login_required
def mes_annonces_agence(request):

    annonces = Annonce.objects.filter(
        agent_createur=request.user
    ).order_by('-date_publication')

    return render(
        request,
        'agent/mes_annonces_agence.html',
        {
            'annonces': annonces
        }
    )

@login_required
def client_dashboard(request):
    return render(
        request,
        'client/dashboard.html'
    )

@login_required
def creer_utilisateur(request):
    """
    Permet au manager de créer tout type d'utilisateur (EF-A4, EF-D5).
    """
    # Vérification du rôle Manager
    if not Manager.objects.filter(pk=request.user.pk).exists():
        messages.error(request, "Accès réservé aux managers.")
        return redirect('accueil')

    if request.method == 'POST':
        try:
            UtilisateurService.inscrire(
                role=request.POST.get('role'),
                username=request.POST.get('username'),
                email=request.POST.get('email'),
                password=request.POST.get('password'),
                telephone=request.POST.get('telephone'),
                nom=request.POST.get('nom'),
                prenom=request.POST.get('prenom'),
                createur=request.user  # ← nécessaire pour Agent/Manager
            )
            messages.success(request, "Compte créé avec succès.")
            return redirect('liste_utilisateurs')
        except (DjangoPermissionDenied, ValueError) as e:
            messages.error(request, str(e))

    return render(request, 'manager/creer_utilisateur.html')




@login_required

def toutes_les_annonces_manager(request):
    annonces = Annonce.objects.select_related(
        'bien',
        'bailleur'
    ).order_by('-date_publication')
    return render(
        request,
        'manager/toutes_les_annonces.html',
        {
            'annonces': annonces
        }
    )



@login_required
def liste_affectations(request):

    clients = Client.objects.filter(
        agent_affecte__isnull=False
    )

    return render(
        request,
        'manager/liste_affectations.html',
        {
            'clients': clients
        }
    )