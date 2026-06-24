from .models import Annonce, BienImmobilier,DemandeVisite,Favori,Bailleur,Client,Agent
from django.core.exceptions import PermissionDenied
class AnnonceService:
    
    @staticmethod
    def deposer_annonce(bailleur, type_bien, usage, superficie,
                        localisation, ville, option, prix, description):
        
        # Règle 1 : l'utilisateur doit être un Bailleur
        from core.models import Bailleur
        if not Bailleur.objects.filter(pk=bailleur.pk).exists():
            raise PermissionDenied("Seul un bailleur peut faire cette action.")
        
        # Règle 2 : prix positif
        if prix <= 0:
            raise ValueError("Le prix doit être supérieur à zéro")
        
        # Règle 3 : superficie positive
        if superficie <= 0:
            raise ValueError("La superficie doit être supérieure à zéro")
        
        # Règle 4 : description non vide
        if not description or not description.strip():
            raise ValueError("La description ne peut pas être vide")
        
        # Règle 5 : option valide
        if option not in ['LOCATION', 'VENTE']:
            raise ValueError("L'option doit être LOCATION ou VENTE")
        types_valides = [
            'TERRAIN',
            'BATIMENT',
            'APPARTEMENT',
            'VILLA',
            'COMMERCE'
        ]

        if type_bien not in types_valides:
            raise ValueError("Type de bien invalide.")
        # Création du bien
        bailleur_obj = Bailleur.objects.get(pk=bailleur.pk)
        bien = BienImmobilier.objects.create(
            proprietaire=bailleur_obj, 
            type=type_bien,
            usage=usage,
            superficie=superficie,
            localisation=localisation,
        ville=ville
    )

        # Création de l'annonce — statut EN_ATTENTE automatique
        annonce = Annonce.objects.create(
            bailleur=bailleur_obj,
            bien=bien,
            option=option,
            prix=prix,
            description=description,
            statut='EN_ATTENTE'
        )
        return annonce

    @staticmethod
    def valider_annonce(annonce, agent):
        """
        Valide une annonce en attente pour la rendre publique.
        Règles : L'utilisateur doit être un Agent et l'annonce doit être EN_ATTENTE.
        """
        # 1. Double sécurité : Contrôle du rôle de l'acteur (ENF-8)
        from core.models import Agent
        if not Agent.objects.filter(pk=agent.pk).exists():
            raise PermissionDenied("Seul un agent peut faire cette action.")

        # 2. Vérification de la cohérence de l'état de l'annonce
        # Note : Ajuste "EN_ATTENTE" et "PUBLIEE" selon tes choix exacts de chaînes de caractères ou de choix (Choices) Django
        if annonce.statut != "EN_ATTENTE":
            raise ValueError("Erreur : Seule une annonce 'En attente de validation' peut être validée.")

        # 3. Application des modifications métier
        annonce.statut = "PUBLIEE"

        # Si tu as ajouté un champ ForeignKey vers Agent dans ton modèle Annonce pour la traçabilité (relation modère/valide)
        if hasattr(annonce, 'agent_validateur'):
            agent_obj = Agent.objects.get(pk=agent.pk)
            annonce.agent_validateur = agent_obj
        # Sauvegarde sécurisée via l'ORM Django (ENF-6 : requêtes paramétrées automatiques)
        annonce.save()
        
        return annonce

    @staticmethod
    def refuser_annonce(annonce, agent):
        """
        Refuse une annonce en attente pour empêcher sa publication.
        Règles : L'utilisateur doit être un Agent et l'annonce doit être EN_ATTENTE.
        """
        # 1. Double sécurité : Contrôle du rôle (ENF-8)
        # Si ce n'est pas un agent, Django intercepte et génère une erreur 403
        from core.models import Agent
        if not Agent.objects.filter(pk=agent.pk).exists():
            raise PermissionDenied("Seul un agent peut faire cette action.")

        # 2. Vérification de la cohérence de l'état de l'annonce
        # On ne peut pas refuser une annonce qui est déjà publiée ou retirée
        if annonce.statut != "EN_ATTENTE":
            raise ValueError("Erreur : Seule une annonce 'En attente de validation' peut être refusée.")

        # 3. Application des modifications métier
        annonce.statut = "REFUSEE"
        
        # Traçabilité : on enregistre l'agent qui a pris la décision de refuser

        agent_obj = Agent.objects.get(pk=agent.pk)
        annonce.agent_validateur = agent_obj
            
        # Sauvegarde sécurisée dans la base de données
        annonce.save()
        
        return annonce
    @staticmethod
    def modifier_annonce(annonce, bailleur, option, prix, description):
        if annonce.bailleur.pk != bailleur.pk:
            raise PermissionDenied("Vous ne pouvez pas modifier une annonce qui ne vous appartient pas.")
        if prix <= 0:
            raise ValueError("Le prix doit être supérieur à zéro.")
        if not description or not description.strip():
            raise ValueError("La description ne peut pas être vide.")
        if annonce.statut != "EN_ATTENTE":
            raise ValueError(
            "Seules les annonces en attente peuvent être modifiées."
            )
        annonce.option = option
        annonce.prix = prix
        annonce.description = description
        annonce.save()
        return annonce

    @staticmethod
    def supprimer_annonce(annonce, bailleur):
        if annonce.bailleur.pk != bailleur.pk:
            raise PermissionDenied("Vous ne pouvez pas supprimer une annonce qui ne vous appartient pas.")
        annonce.delete()
    @staticmethod
    def retirer_annonce(annonce, manager):
        """
        Retire une annonce publique du site pour la rendre invisible.
        Règles : L'utilisateur doit être un Manager et l'annonce doit être PUBLIEE.
        """
        # 1. Double sécurité : Contrôle du rôle du Manager (ENF-8)
        # Si ce n'est pas un manager, Django intercepte et renvoie une page 403
        from core.models import Manager
        if not Manager.objects.filter(pk=manager.pk).exists():
            raise PermissionDenied("Seul un manager peut faire cette action.")

        # 2. Vérification de la cohérence de l'état de l'annonce
        # On ne peut retirer qu'une annonce qui est actuellement en ligne
        if annonce.statut != "PUBLIEE":
            raise ValueError("Erreur : Seule une annonce 'Publiée' peut être retirée.")

        # 3. Application de la modification métier
        annonce.statut = "RETIREE"
        
        # Sauvegarde sécurisée dans la base de données
        annonce.save()
        
        return annonce
    @staticmethod
    def ajouter_annonce_agence(
        agent,
        type_bien,
        usage,
        superficie,
        localisation,
        ville,
        option,
        prix,
        description
    ):

        from core.models import Agent

        if not Agent.objects.filter(pk=agent.pk).exists():
            raise PermissionDenied(
                "Seul un agent peut ajouter une annonce agence."
            )

        if prix <= 0:
            raise ValueError(
                "Le prix doit être supérieur à zéro."
            )

        if superficie <= 0:
            raise ValueError(
                "La superficie doit être supérieure à zéro."
            )
        types_valides = [
            'TERRAIN',
            'BATIMENT',
            'APPARTEMENT',
            'VILLA',
            'COMMERCE'
        ]

        if type_bien not in types_valides:
            raise ValueError("Type de bien invalide.")

        agent_obj = Agent.objects.get(pk=agent.pk)

        bien = BienImmobilier.objects.create(
            proprietaire=None,
            type=type_bien,
            usage=usage,
            superficie=superficie,
            localisation=localisation,
            ville=ville
        )

        annonce = Annonce.objects.create(
            bailleur=None,
            bien=bien,
            agent_createur=agent_obj,
            option=option,
            prix=prix,
            description=description,
            statut='PUBLIEE'
        )

        return annonce

class DemandeVisiteService:

    @staticmethod
    def creer_demande(client, annonce):
        """
        Crée une demande de visite pour un client sur une annonce publiée.
        """
        # 1. Contrôle d'accès : Seul un client peut faire une demande
        from core.models import Client
        if not Client.objects.filter(pk=client.pk).exists():
            raise PermissionDenied("Seul un client peut faire cette action.")

        # 2. Vérification de l'état : L'annonce doit être publiée
        if annonce.statut != "PUBLIEE":
            raise ValueError("Erreur : Il est impossible de demander la visite d'un bien qui n'est pas en ligne.")

        # 3. Sécurité anti-doublon : Évite qu'un client clique plusieurs fois
        deja_demande = DemandeVisite.objects.filter(client=client, annonce=annonce).exists()
        if deja_demande:
            raise ValueError("Erreur : Vous avez déjà soumis une demande de visite pour cette annonce.")

        # 4. Action : Création en base de données au statut initial "EN_ATTENTE"
        client_obj = Client.objects.get(pk=client.pk)
        demande = DemandeVisite.objects.create(
            client=client_obj,
            annonce=annonce,
            statut="EN_ATTENTE"
        )
        return demande
    
    @staticmethod
    def traiter_demande(demande, agent, decision):
        """
        Permet à un agent de valider ou refuser une demande de visite.
        """
        from core.models import Agent
        if not Agent.objects.filter(pk=agent.pk).exists():
            raise PermissionDenied("Seul un agent peut faire cette action.")

        if demande.statut != "EN_ATTENTE":
            raise ValueError("Erreur : Cette demande de visite a déjà été traitée.")

        if decision not in ["VALIDEE", "REFUSEE"]:
            raise ValueError("Erreur : La décision doit être 'VALIDEE' ou 'REFUSEE'.")

        demande.statut = decision
        demande.save()
        return demande
class FavoriService:

    @staticmethod
    def ajouter_favori(user, annonce):
        from core.models import Client
        if not Client.objects.filter(pk=user.pk).exists():
            raise PermissionDenied("Seul un client peut faire cette action.")
        if annonce.statut != "PUBLIEE":
            raise ValueError("Erreur : Impossible d'ajouter aux favoris une annonce qui n'est pas en ligne.")
        client_obj = Client.objects.get(pk=user.pk)
        deja_favori = Favori.objects.filter(client=client_obj, annonce=annonce).exists()
        if deja_favori:
            raise ValueError("Cette annonce est déjà dans vos favoris.")
        favori = Favori.objects.create(client=client_obj, annonce=annonce)
        return favori

    @staticmethod
    def retirer_favori(user, annonce):
        from core.models import Client
        if not Client.objects.filter(pk=user.pk).exists():
            raise PermissionDenied("Seul un client peut faire cette action.")
        client_obj = Client.objects.get(pk=user.pk)
        favori = Favori.objects.filter(client=client_obj, annonce=annonce).first()
        if not favori:
            raise ValueError("Erreur : Cette annonce ne fait pas partie de vos favoris.")
        favori.delete()
        return True

    @staticmethod
    def lister_favoris(user):
        from core.models import Client
        if not Client.objects.filter(pk=user.pk).exists():
            raise PermissionDenied("Seul un client peut faire cette action.")
        client_obj = Client.objects.get(pk=user.pk)
        return Favori.objects.filter(client=client_obj).select_related('annonce', 'annonce__bien')
    



class UtilisateurService:

    @staticmethod
    def supprimer_utilisateur(manager, utilisateur):
        from core.models import Manager

        if not Manager.objects.filter(pk=manager.pk).exists():
            raise PermissionDenied(
                "Seul un manager peut faire cette action."
            )

        if Manager.objects.filter(pk=utilisateur.pk).exists():
            raise PermissionDenied(
                "Un manager ne peut pas supprimer un autre manager."
            )

        utilisateur.delete()

    @staticmethod
    def affecter_client(manager, client, agent):
        from core.models import Manager

        if not Manager.objects.filter(pk=manager.pk).exists():
            raise PermissionDenied(
                "Seul un manager peut faire cette action."
            )

        client_obj = Client.objects.get(pk=client.pk)
        agent_obj = Agent.objects.get(pk=agent.pk)

        client_obj.agent_affecte = agent_obj
        client_obj.save()

        return client_obj

    @staticmethod
    def inscrire(
        role,
        username,
        email,
        password,
        telephone,
        nom,
        prenom,
        createur=None
    ):
        """
        CLIENT et BAILLEUR : inscription libre
        AGENT et MANAGER : créés uniquement par un manager
        """
        



        
        from core.models import Agent, Manager

        if role in ['AGENT', 'MANAGER']:

            if createur is None:
                raise PermissionDenied(
                    "Un Agent ou Manager ne peut être créé que par un Manager."
                )

            if not Manager.objects.filter(pk=createur.pk).exists():
                raise PermissionDenied(
                    "Seul un Manager peut créer un employé."
                )

        if role == 'CLIENT':

            return Client.objects.create_user(
                username=username,
                email=email,
                password=password,
                telephone=telephone,
                first_name=prenom,
                last_name=nom
            )

        elif role == 'BAILLEUR':

            return Bailleur.objects.create_user(
                username=username,
                email=email,
                password=password,
                telephone=telephone,
                first_name=prenom,
                last_name=nom
            )

        elif role == 'AGENT':

            import random
            import string

            matricule = (
                'AG-' +
                ''.join(random.choices(string.digits, k=6))
            )

            return Agent.objects.create_user(
                username=username,
                email=email,
                password=password,
                telephone=telephone,
                first_name=prenom,
                last_name=nom,
                matricule=matricule
            )

        elif role == 'MANAGER':

            import random
            import string

            matricule = (
                'MG-' +
                ''.join(random.choices(string.digits, k=6))
            )

            return Manager.objects.create_user(
                username=username,
                email=email,
                password=password,
                telephone=telephone,
                first_name=prenom,
                last_name=nom,
                matricule=matricule
            )

        raise ValueError(
            "Rôle invalide. Choisissez CLIENT, BAILLEUR, AGENT ou MANAGER."
        )

    @staticmethod
    def get_statistiques(manager):
        from core.models import Manager

        if not Manager.objects.filter(pk=manager.pk).exists():
            raise PermissionDenied(
                "Seul un manager peut faire cette action."
            )

        return {
            'total_annonces': Annonce.objects.count(),
            'en_attente': Annonce.objects.filter(
                statut='EN_ATTENTE'
            ).count(),
            'publiees': Annonce.objects.filter(
                statut='PUBLIEE'
            ).count(),
            'retirees': Annonce.objects.filter(
                statut='RETIREE'
            ).count(),
            'total_clients': Client.objects.count(),
            'total_bailleurs': Bailleur.objects.count(),
            'total_agents': Agent.objects.count(),
            'total_demandes': DemandeVisite.objects.count(),
        }

    @staticmethod
    def lister_utilisateurs(manager):
        from core.models import Manager

        if not Manager.objects.filter(pk=manager.pk).exists():
            raise PermissionDenied(
                "Seul un manager peut faire cette action."
            )

        return {
            'clients': Client.objects.all(),
            'bailleurs': Bailleur.objects.all(),
            'agents': Agent.objects.all(),
            'managers': Manager.objects.all(),
        }

    @staticmethod
    def get_client_dashboard_data(client):
        """
        Retourne les données statistiques pour le dashboard client.
        """
        from core.models import Client
        if not Client.objects.filter(pk=client.pk).exists():
            raise PermissionDenied("Seul un client peut faire cette action.")

        client_obj = Client.objects.get(pk=client.pk)
        favoris_count = Favori.objects.filter(client=client_obj).count()
        demandes_count = DemandeVisite.objects.filter(client=client_obj).count()
        demandes_validees = DemandeVisite.objects.filter(
            client=client_obj, statut='VALIDEE'
        ).count()
        dernieres_demandes = DemandeVisite.objects.filter(
            client=client_obj
        ).select_related(
            'annonce', 'annonce__bien'
        ).order_by('-date_demande')[:5]

        return {
            'favoris_count': favoris_count,
            'demandes_count': demandes_count,
            'demandes_validees': demandes_validees,
            'dernieres_demandes': dernieres_demandes,
        }
