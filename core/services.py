from .models import Annonce, BienImmobilier,DemandeVisite,Favori,Bailleur,Client,Agent
from django.core.exceptions import PermissionDenied
class AnnonceService:
    
    @staticmethod
    def deposer_annonce(bailleur, type_bien, usage, superficie,
                        localisation, ville, option, prix, description):
        
        # Règle 1 : l'utilisateur doit être un Bailleur
        if not hasattr(bailleur, 'bailleur'):
            raise ValueError("Seul un bailleur peut déposer une annonce")
        
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
    
        # Création du bien
        bien = BienImmobilier.objects.create(
            proprietaire=bailleur.bailleur, 
            type=type_bien,
            usage=usage,
            superficie=superficie,
            localisation=localisation,
        ville=ville
    )

        # Création de l'annonce — statut EN_ATTENTE automatique
        annonce = Annonce.objects.create(
            bailleur=bailleur.bailleur,
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
        if not hasattr(agent, 'agent'):
            raise PermissionDenied("Accès refusé : Seul un agent peut valider une annonce.")

        # 2. Vérification de la cohérence de l'état de l'annonce
        # Note : Ajuste "EN_ATTENTE" et "PUBLIEE" selon tes choix exacts de chaînes de caractères ou de choix (Choices) Django
        if annonce.statut != "EN_ATTENTE":
            raise ValueError("Erreur : Seule une annonce 'En attente de validation' peut être validée.")

        # 3. Application des modifications métier
        annonce.statut = "PUBLIEE"
        
        # Si tu as ajouté un champ ForeignKey vers Agent dans ton modèle Annonce pour la traçabilité (relation modère/valide)
        if hasattr(annonce, 'agent_validateur'):
            annonce.agent_validateur = agent
            
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
        if not hasattr(agent, 'agent'):
            raise PermissionDenied("Accès refusé : Seul un agent peut refuser une annonce.")

        # 2. Vérification de la cohérence de l'état de l'annonce
        # On ne peut pas refuser une annonce qui est déjà publiée ou retirée
        if annonce.statut != "EN_ATTENTE":
            raise ValueError("Erreur : Seule une annonce 'En attente de validation' peut être refusée.")

        # 3. Application des modifications métier
        annonce.statut = "REFUSEE"
        
        # Traçabilité : on enregistre l'agent qui a pris la décision de refuser
        if hasattr(annonce, 'agent_validateur'):
            annonce.agent_validateur = agent
            
        # Sauvegarde sécurisée dans la base de données
        annonce.save()
        
        return annonce
    @staticmethod
    def modifier_annonce(annonce, bailleur, option, prix, description):
        if annonce.bailleur != bailleur:
            raise PermissionDenied("Vous ne pouvez pas modifier une annonce qui ne vous appartient pas.")
        if prix <= 0:
            raise ValueError("Le prix doit être supérieur à zéro.")
        if not description or not description.strip():
            raise ValueError("La description ne peut pas être vide.")
        annonce.option = option
        annonce.prix = prix
        annonce.description = description
        annonce.save()
        return annonce

    @staticmethod
    def supprimer_annonce(annonce, bailleur):
        if annonce.bailleur != bailleur:
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
        if not hasattr(manager, 'manager'):
            raise PermissionDenied("Accès refusé : Seul un manager peut retirer une annonce.")

        # 2. Vérification de la cohérence de l'état de l'annonce
        # On ne peut retirer qu'une annonce qui est actuellement en ligne
        if annonce.statut != "PUBLIEE":
            raise ValueError("Erreur : Seule une annonce 'Publiée' peut être retirée.")

        # 3. Application de la modification métier
        annonce.statut = "RETIREE"
        
        # Sauvegarde sécurisée dans la base de données
        annonce.save()
        
        return annonce

class DemandeVisiteService:

    @staticmethod
    def creer_demande(client, annonce):
        """
        Crée une demande de visite pour un client sur une annonce publiée.
        """
        # 1. Contrôle d'accès : Seul un client peut faire une demande
        if not hasattr(client, 'client'):
            raise PermissionDenied("Accès refusé : Seul un client connecté peut effectuer une demande de visite.")

        # 2. Vérification de l'état : L'annonce doit être publiée
        if annonce.statut != "PUBLIEE":
            raise ValueError("Erreur : Il est impossible de demander la visite d'un bien qui n'est pas en ligne.")

        # 3. Sécurité anti-doublon : Évite qu'un client clique plusieurs fois
        deja_demande = DemandeVisite.objects.filter(client=client, annonce=annonce).exists()
        if deja_demande:
            raise ValueError("Erreur : Vous avez déjà soumis une demande de visite pour cette annonce.")

        # 4. Action : Création en base de données au statut initial "EN_ATTENTE"
        demande = DemandeVisite.objects.create(
            client=client,
            annonce=annonce,
            statut="EN_ATTENTE"
        )
        return demande
    
    @staticmethod
    def traiter_demande(demande, agent, decision):
        """
        Permet à un agent de valider ou refuser une demande de visite.
        """
        if not hasattr(agent, 'agent'):
            raise PermissionDenied("Accès refusé : Seul un agent peut traiter une demande de visite.")

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
        if not hasattr(user, 'client'):
            raise PermissionDenied("Accès refusé : Seul un client peut ajouter des favoris.")
        if annonce.statut != "PUBLIEE":
            raise ValueError("Erreur : Impossible d'ajouter aux favoris une annonce qui n'est pas en ligne.")
        deja_favori = Favori.objects.filter(client=user.client, annonce=annonce).exists()
        if deja_favori:
            raise ValueError("Cette annonce est déjà dans vos favoris.")
        favori = Favori.objects.create(client=user.client, annonce=annonce)
        return favori

    @staticmethod
    def retirer_favori(user, annonce):
        if not hasattr(user, 'client'):
            raise PermissionDenied("Accès refusé : Seul un client peut retirer des favoris.")
        favori = Favori.objects.filter(client=user.client, annonce=annonce).first()
        if not favori:
            raise ValueError("Erreur : Cette annonce ne fait pas partie de vos favoris.")
        favori.delete()
        return True

    @staticmethod
    def lister_favoris(user):
        if not hasattr(user, 'client'):
            raise PermissionDenied("Accès refusé : Seul un client peut consulter ses favoris.")
        return Favori.objects.filter(client=user.client).select_related('annonce', 'annonce__bien')
    



class UtilisateurService:

    @staticmethod
    def supprimer_utilisateur(manager, utilisateur):
        if not hasattr(manager, 'manager'):
            raise PermissionDenied("Seul un manager peut supprimer un compte.")
        utilisateur.delete()

    @staticmethod
    def affecter_client(manager, client, agent):
        if not hasattr(manager, 'manager'):
            raise PermissionDenied("Seul un manager peut affecter un client.")
        client.agent_affecte = agent
        client.save()
        return client
    


    @staticmethod
    def inscrire(role, username, email, password, telephone, nom, prenom):
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
        else:
            raise ValueError("Rôle invalide. Choisissez Client ou Bailleur.")

    @staticmethod
    def get_statistiques(manager):
        if not hasattr(manager, 'manager'):
            raise PermissionDenied("Seul un manager peut accéder aux statistiques.")
        return {
            'total_annonces'  : Annonce.objects.count(),
            'en_attente'      : Annonce.objects.filter(statut='EN_ATTENTE').count(),
            'publiees'        : Annonce.objects.filter(statut='PUBLIEE').count(),
            'retirees'        : Annonce.objects.filter(statut='RETIREE').count(),
            'total_clients'   : Client.objects.count(),
            'total_bailleurs' : Bailleur.objects.count(),
            'total_agents'    : Agent.objects.count(),
            'total_demandes'  : DemandeVisite.objects.count(),
        }

    @staticmethod
    def lister_utilisateurs(manager):
        if not hasattr(manager, 'manager'):
            raise PermissionDenied("Seul un manager peut lister les utilisateurs.")
        return {
            'clients'   : Client.objects.all(),
            'bailleurs' : Bailleur.objects.all(),
            'agents'    : Agent.objects.all(),
        }
    