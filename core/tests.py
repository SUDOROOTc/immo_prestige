from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from .models import (
    Employe, Agent, Manager, Client, Bailleur,
    BienImmobilier, Annonce, DemandeVisite, Favori
)
from .services import (
    AnnonceService, DemandeVisiteService, FavoriService, UtilisateurService
)
from django.test import Client as DjangoClient


User = get_user_model()


class BaseTestCase(TestCase):
    def setUp(self):
        self.client = DjangoClient()

    def _create_user_direct(self, model_class, **kwargs):
        defaults = {
            'username': kwargs.get('username', 'user'),
            'email': kwargs.get('email', 'user@example.com'),
            'password': kwargs.get('password', 'pass12345'),
            'telephone': kwargs.get('telephone', '0123456789'),
            'first_name': kwargs.get('prenom', ''),
            'last_name': kwargs.get('nom', ''),
        }
        if model_class in (Agent, Manager):
            defaults['matricule'] = kwargs.get('matricule', 'XX-000000')
        user = model_class.objects.create_user(**defaults)
        return user

    def _create_bailleur(self):
        return self._create_user_direct(
            Bailleur,
            username='test_bailleur_001',
            email='test_bailleur_001@example.com',
            password='pass12345',
            nom='TestBailleur',
            prenom='User',
        )

    def _create_agent(self):
        return self._create_user_direct(
            Agent,
            username='test_agent_002',
            email='test_agent_002@example.com',
            password='pass12345',
            matricule='AG-000001',
            nom='TestAgent',
            prenom='User',
        )

    def _create_manager(self):
        return self._create_user_direct(
            Manager,
            username='test_manager_003',
            email='test_manager_003@example.com',
            password='pass12345',
            matricule='MG-000001',
            nom='TestManager',
            prenom='User',
        )

    def _create_client(self):
        return self._create_user_direct(
            Client,
            username='test_client_004',
            email='test_client_004@example.com',
            password='pass12345',
            nom='TestClient',
            prenom='User',
        )

    def _create_bien(self, bailleur):
        return BienImmobilier.objects.create(
            proprietaire=bailleur,
            type="VILLA",
            usage="RESIDENCE",
            superficie=120.0,
            ville="Ouagadougou",
            localisation="Centre ville",
            description="Belle villa",
        )

    def _create_annonce(self, bailleur, bien, option="VENTE", statut="EN_ATTENTE", prix=5000000):
        return Annonce.objects.create(
            bailleur=bailleur,
            bien=bien,
            option=option,
            prix=prix,
            description="Annonce test",
            statut=statut,
        )


class ModelTestCase(BaseTestCase):
    def test_creation_bailleur(self):
        bailleur = self._create_bailleur()
        self.assertIsInstance(bailleur, Bailleur)
        self.assertEqual(str(bailleur), bailleur.username)

    def test_creation_agent(self):
        agent = self._create_agent()
        self.assertIsInstance(agent, Agent)
        self.assertTrue(hasattr(agent, "matricule"))
        self.assertIn("AG-", agent.matricule)

    def test_creation_manager(self):
        manager = self._create_manager()
        self.assertIsInstance(manager, Manager)
        self.assertIn("MG-", manager.matricule)

    def test_creation_client_avec_agent_affecte(self):
        agent = self._create_agent()
        client = self._create_client()
        client.agent_affecte = agent
        client.save()
        self.assertEqual(client.agent_affecte, agent)

    def test_bien_immobilier_str(self):
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        expected = f"{bien.type} - {bien.ville} ({bailleur.username})"
        self.assertEqual(str(bien), expected)

    def test_annonce_str(self):
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien)
        self.assertIn("VILLA", str(annonce))
        self.assertIn("VENTE", str(annonce))
        self.assertIn("EN_ATTENTE", str(annonce))

    def test_demande_visite_str(self):
        client = self._create_client()
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien, statut="PUBLIEE")
        demande = DemandeVisite.objects.create(client=client, annonce=annonce)
        self.assertIn(client.username, str(demande))
        self.assertIn("EN_ATTENTE", str(demande))

    def test_favori_str(self):
        client = self._create_client()
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien, statut="PUBLIEE")
        favori = Favori.objects.create(client=client, annonce=annonce)
        self.assertIn(client.username, str(favori))

    def test_favori_unique_together(self):
        client = self._create_client()
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien, statut="PUBLIEE")
        Favori.objects.create(client=client, annonce=annonce)
        with self.assertRaises(Exception):
            Favori.objects.create(client=client, annonce=annonce)


class AnnonceServiceTestCase(BaseTestCase):
    def test_deposer_annonce_succes(self):
        bailleur = self._create_bailleur()
        annonce = AnnonceService.deposer_annonce(
            bailleur=bailleur,
            type_bien="VILLA",
            usage="RESIDENCE",
            superficie=200.0,
            localisation="Quartier ZACA",
            ville="Bobo-Dioulasso",
            option="VENTE",
            prix=7500000,
            description="Superbe villa 3 pièces",
        )
        self.assertEqual(annonce.statut, "EN_ATTENTE")
        self.assertEqual(annonce.bien.type, "VILLA")
        self.assertEqual(annonce.bien.ville, "Bobo-Dioulasso")

    def test_deposer_annonce_prix_invalide(self):
        bailleur = self._create_bailleur()
        with self.assertRaises(ValueError) as ctx:
            AnnonceService.deposer_annonce(
                bailleur=bailleur,
                type_bien="VILLA",
                usage="RESIDENCE",
                superficie=200.0,
                localisation="Quartier",
                ville="Ville",
                option="VENTE",
                prix=0,
                description="Description",
            )
        self.assertIn("prix", str(ctx.exception).lower())

    def test_deposer_annonce_superficie_invalide(self):
        bailleur = self._create_bailleur()
        with self.assertRaises(ValueError) as ctx:
            AnnonceService.deposer_annonce(
                bailleur=bailleur,
                type_bien="VILLA",
                usage="RESIDENCE",
                superficie=-10,
                localisation="Quartier",
                ville="Ville",
                option="VENTE",
                prix=5000000,
                description="Description",
            )
        self.assertIn("superficie", str(ctx.exception).lower())

    def test_deposer_annonce_description_vide(self):
        bailleur = self._create_bailleur()
        with self.assertRaises(ValueError):
            AnnonceService.deposer_annonce(
                bailleur=bailleur,
                type_bien="VILLA",
                usage="RESIDENCE",
                superficie=200.0,
                localisation="Quartier",
                ville="Ville",
                option="VENTE",
                prix=5000000,
                description="   ",
            )

    def test_deposer_annonce_option_invalide(self):
        bailleur = self._create_bailleur()
        with self.assertRaises(ValueError):
            AnnonceService.deposer_annonce(
                bailleur=bailleur,
                type_bien="VILLA",
                usage="RESIDENCE",
                superficie=200.0,
                localisation="Quartier",
                ville="Ville",
                option="INVALIDE",
                prix=5000000,
                description="Description",
            )

    def test_deposer_annonce_type_invalide(self):
        bailleur = self._create_bailleur()
        with self.assertRaises(ValueError):
            AnnonceService.deposer_annonce(
                bailleur=bailleur,
                type_bien="CHATEAU",
                usage="RESIDENCE",
                superficie=200.0,
                localisation="Quartier",
                ville="Ville",
                option="VENTE",
                prix=5000000,
                description="Description",
            )

    def test_valider_annonce(self):
        agent = self._create_agent()
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien, statut="EN_ATTENTE")
        annonce = AnnonceService.valider_annonce(annonce=annonce, agent=agent)
        self.assertEqual(annonce.statut, "PUBLIEE")

    def test_valider_annonce_deja_publiee(self):
        agent = self._create_agent()
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien, statut="PUBLIEE")
        with self.assertRaises(ValueError):
            AnnonceService.valider_annonce(annonce=annonce, agent=agent)

    def test_refuser_annonce(self):
        agent = self._create_agent()
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien, statut="EN_ATTENTE")
        annonce = AnnonceService.refuser_annonce(annonce=annonce, agent=agent)
        self.assertEqual(annonce.statut, "REFUSEE")

    def test_modifier_annonce(self):
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien)
        annonce = AnnonceService.modifier_annonce(
            annonce=annonce,
            bailleur=bailleur,
            option="LOCATION",
            prix=300000,
            description="Nouvelle description modifiée",
        )
        self.assertEqual(annonce.option, "LOCATION")
        self.assertEqual(annonce.prix, 300000)
        self.assertEqual(annonce.description, "Nouvelle description modifiée")

    def test_modifier_annonce_mauvais_bailleur(self):
        bailleur1 = self._create_bailleur()
        bailleur2 = self._create_user_direct(
            Bailleur,
            username='test_bailleur_005',
            email='test_bailleur_005@example.com',
            password='pass12345',
            nom='Other',
            prenom='Bailleur',
        )
        bien = self._create_bien(bailleur1)
        annonce = self._create_annonce(bailleur1, bien)
        with self.assertRaises(PermissionDenied):
            AnnonceService.modifier_annonce(
                annonce=annonce,
                bailleur=bailleur2,
                option="LOCATION",
                prix=300000,
                description="Description",
            )

    def test_supprimer_annonce(self):
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien)
        AnnonceService.supprimer_annonce(annonce=annonce, bailleur=bailleur)
        self.assertFalse(Annonce.objects.filter(pk=annonce.pk).exists())

    def test_retirer_annonce(self):
        manager = self._create_manager()
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien, statut="PUBLIEE")
        annonce = AnnonceService.retirer_annonce(annonce=annonce, manager=manager)
        self.assertEqual(annonce.statut, "RETIREE")

    def test_ajouter_annonce_agence(self):
        agent = self._create_agent()
        annonce = AnnonceService.ajouter_annonce_agence(
            agent=agent,
            type_bien="APPARTEMENT",
            usage="BUREAU",
            superficie=50.0,
            localisation="Centre",
            ville="Ouagadougou",
            option="LOCATION",
            prix=150000,
            description="Bureau moderne",
        )
        self.assertEqual(annonce.statut, "PUBLIEE")
        self.assertIsNone(annonce.bailleur)
        self.assertEqual(annonce.agent_createur, agent)


class DemandeVisiteServiceTestCase(BaseTestCase):
    def test_creer_demande_succes(self):
        client = self._create_client()
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien, statut="PUBLIEE")
        demande = DemandeVisiteService.creer_demande(client=client, annonce=annonce)
        self.assertEqual(demande.statut, "EN_ATTENTE")
        self.assertEqual(demande.client, client)
        self.assertEqual(demande.annonce, annonce)

    def test_creer_demande_double(self):
        client = self._create_client()
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien, statut="PUBLIEE")
        DemandeVisiteService.creer_demande(client=client, annonce=annonce)
        with self.assertRaises(ValueError):
            DemandeVisiteService.creer_demande(client=client, annonce=annonce)

    def test_creer_demande_annonce_non_publiee(self):
        client = self._create_client()
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien, statut="EN_ATTENTE")
        with self.assertRaises(ValueError):
            DemandeVisiteService.creer_demande(client=client, annonce=annonce)

    def test_traiter_demande_valider(self):
        agent = self._create_agent()
        client = self._create_client()
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien, statut="PUBLIEE")
        demande = DemandeVisiteService.creer_demande(client=client, annonce=annonce)
        demande = DemandeVisiteService.traiter_demande(
            demande=demande, agent=agent, decision="VALIDEE"
        )
        self.assertEqual(demande.statut, "VALIDEE")

    def test_traiter_demande_refuser(self):
        agent = self._create_agent()
        client = self._create_client()
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien, statut="PUBLIEE")
        demande = DemandeVisiteService.creer_demande(client=client, annonce=annonce)
        demande = DemandeVisiteService.traiter_demande(
            demande=demande, agent=agent, decision="REFUSEE"
        )
        self.assertEqual(demande.statut, "REFUSEE")


class FavoriServiceTestCase(BaseTestCase):
    def test_ajouter_favori(self):
        client = self._create_client()
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien, statut="PUBLIEE")
        favori = FavoriService.ajouter_favori(user=client, annonce=annonce)
        self.assertEqual(favori.client, client)
        self.assertEqual(favori.annonce, annonce)

    def test_ajouter_favori_double(self):
        client = self._create_client()
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien, statut="PUBLIEE")
        FavoriService.ajouter_favori(user=client, annonce=annonce)
        with self.assertRaises(ValueError):
            FavoriService.ajouter_favori(user=client, annonce=annonce)

    def test_retirer_favori(self):
        client = self._create_client()
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien, statut="PUBLIEE")
        FavoriService.ajouter_favori(user=client, annonce=annonce)
        result = FavoriService.retirer_favori(user=client, annonce=annonce)
        self.assertTrue(result)
        self.assertFalse(Favori.objects.filter(client=client, annonce=annonce).exists())

    def test_retirer_favori_inexistant(self):
        client = self._create_client()
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien, statut="PUBLIEE")
        with self.assertRaises(ValueError):
            FavoriService.retirer_favori(user=client, annonce=annonce)


class UtilisateurServiceTestCase(BaseTestCase):
    def test_inscrire_client(self):
        user = UtilisateurService.inscrire(
            role="CLIENT",
            username="test_cli_006",
            email="test_cli_006@example.com",
            password="pass12345",
            telephone="0123456789",
            nom="Nom",
            prenom="Prenom",
        )
        self.assertIsInstance(user, Client)
        self.assertEqual(user.email, "test_cli_006@example.com")

    def test_inscrire_bailleur(self):
        user = UtilisateurService.inscrire(
            role="BAILLEUR",
            username="test_bail_007",
            email="test_bail_007@example.com",
            password="pass12345",
            telephone="0123456789",
            nom="Nom",
            prenom="Prenom",
        )
        self.assertIsInstance(user, Bailleur)

    def test_inscrire_agent_sans_createur(self):
        with self.assertRaises(PermissionDenied):
            UtilisateurService.inscrire(
                role="AGENT",
                username="test_ag_008",
                email="test_ag_008@example.com",
                password="pass12345",
                telephone="0123456789",
                nom="A",
                prenom="B",
                createur=None,
            )

    def test_inscrire_manager_sans_createur(self):
        with self.assertRaises(PermissionDenied):
            UtilisateurService.inscrire(
                role="MANAGER",
                username="test_mg_009",
                email="test_mg_009@example.com",
                password="pass12345",
                telephone="0123456789",
                nom="M",
                prenom="G",
                createur=None,
            )

    def test_get_statistiques(self):
        manager = self._create_manager()
        stats = UtilisateurService.get_statistiques(manager=manager)
        self.assertIn("total_annonces", stats)
        self.assertIn("total_clients", stats)
        self.assertIn("total_bailleurs", stats)
        self.assertIn("total_agents", stats)
        self.assertIn("total_demandes", stats)

    def test_lister_utilisateurs(self):
        manager = self._create_manager()
        data = UtilisateurService.lister_utilisateurs(manager=manager)
        self.assertIn("clients", data)
        self.assertIn("bailleurs", data)
        self.assertIn("agents", data)
        self.assertIn("managers", data)

    def test_supprimer_utilisateur(self):
        manager = self._create_manager()
        client = self._create_client()
        UtilisateurService.supprimer_utilisateur(manager=manager, utilisateur=client)
        self.assertFalse(User.objects.filter(pk=client.pk).exists())

    def test_supprimer_manager_interdit(self):
        manager1 = self._create_manager()
        manager2 = self._create_user_direct(
            Manager,
            username='test_mg_010',
            email='test_mg_010@example.com',
            password='pass12345',
            matricule='MG-000010',
            nom='TestManager2',
            prenom='User2',
        )
        with self.assertRaises(PermissionDenied):
            UtilisateurService.supprimer_utilisateur(manager=manager1, utilisateur=manager2)

    def test_affecter_client(self):
        manager = self._create_manager()
        agent = self._create_agent()
        client = self._create_client()
        client_obj = UtilisateurService.affecter_client(
            manager=manager, client=client, agent=agent
        )
        self.assertEqual(client_obj.agent_affecte, agent)


class ViewTestCase(BaseTestCase):
    def test_accueil(self):
        response = self.client.get(reverse("accueil"))
        self.assertEqual(response.status_code, 200)

    def test_liste_annonces(self):
        response = self.client.get(reverse("liste_annonces"))
        self.assertEqual(response.status_code, 200)

    def test_inscription_get(self):
        response = self.client.get(reverse("inscription"))
        self.assertEqual(response.status_code, 200)

    def test_inscription_post_succes(self):
        response = self.client.post(reverse("inscription"), {
            "role": "CLIENT",
            "username": "newcli",
            "email": "newcli@example.com",
            "password": "pass12345",
            "telephone": "0123456789",
            "nom": "Nom",
            "prenom": "Prenom",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newcli").exists())

    def test_deposer_annonce_bailleur_non_connecte(self):
        response = self.client.get(reverse("deposer_annonce"))
        self.assertEqual(response.status_code, 302)

    def test_deposer_annonce_bailleur_connecte(self):
        bailleur = self._create_bailleur()
        self.client.login(username="test_bailleur_001", password="pass12345")
        response = self.client.get(reverse("deposer_annonce"))
        self.assertEqual(response.status_code, 200)

    def test_mes_annonces_bailleur_non_connecte(self):
        response = self.client.get(reverse("mes_annonces_bailleur"))
        self.assertEqual(response.status_code, 302)

    def test_mes_annonces_bailleur_connecte(self):
        bailleur = self._create_bailleur()
        self.client.login(username="test_bailleur_001", password="pass12345")
        response = self.client.get(reverse("mes_annonces_bailleur"))
        self.assertEqual(response.status_code, 200)

    def test_detail_annonce_inexistante(self):
        response = self.client.get(reverse("detail_annonce", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_client_dashboard_non_connecte(self):
        response = self.client.get(reverse("dashboard_client"))
        self.assertEqual(response.status_code, 302)

    def test_agent_dashboard_non_connecte(self):
        response = self.client.get(reverse("agent_dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_manager_dashboard_non_connecte(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_liste_utilisateurs_manager_non_connecte(self):
        response = self.client.get(reverse("liste_utilisateurs"))
        self.assertEqual(response.status_code, 302)

    def test_ajouter_favori_client(self):
        client = self._create_client()
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien, statut="PUBLIEE")
        self.client.login(username="test_client_004", password="pass12345")
        response = self.client.get(reverse("ajouter_favori", args=[annonce.id]))
        self.assertIn(response.status_code, [302, 200])
        self.assertTrue(Favori.objects.filter(client=client, annonce=annonce).exists())

    def test_ajouter_favori_non_client(self):
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien, statut="PUBLIEE")
        self.client.login(username="test_bailleur_001", password="pass12345")
        response = self.client.get(reverse("ajouter_favori", args=[annonce.id]))
        self.assertIn(response.status_code, [302, 403])

    def test_creer_demande_visite_client(self):
        client = self._create_client()
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien, statut="PUBLIEE")
        self.client.login(username="test_client_004", password="pass12345")
        response = self.client.get(reverse("creer_demande_visite", args=[annonce.id]))
        self.assertIn(response.status_code, [302, 200])
        self.assertTrue(DemandeVisite.objects.filter(client=client, annonce=annonce).exists())

    def test_creer_demande_visite_non_client(self):
        bailleur = self._create_bailleur()
        bien = self._create_bien(bailleur)
        annonce = self._create_annonce(bailleur, bien, statut="PUBLIEE")
        self.client.login(username="test_bailleur_001", password="pass12345")
        response = self.client.get(reverse("creer_demande_visite", args=[annonce.id]))
        self.assertIn(response.status_code, [302, 403])

    def test_liste_demandes_agent_non_connecte(self):
        response = self.client.get(reverse("liste_demandes_agent"))
        self.assertEqual(response.status_code, 302)