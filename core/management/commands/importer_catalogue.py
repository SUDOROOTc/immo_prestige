import os
import re
import glob
import random
import json

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from core.models import (
    Agent,
    Bailleur,
    Client,
    Manager,
    BienImmobilier,
    Annonce,
    Photo
)


# --- QUARTIERS RÉALISTES DE OUAGADOUGOU ---
QUARTIERS_OUAGA = [
    "Ouaga 2000", "Zone du Bois", "Koulouba", "Bonheur Ville",
    "Tampouy", "Samadin", "Taghin", "Somgandé", "Rimkiéta",
    "Kamboinsé", "Barogo", "Tengandogo", "Kalgonde",
    "Bassinko", "Zone I", "Pissy", "Nagrin", "Saaba",
    "Garguin", "Cissin", "Zogona", "Wayalghin", "Karpala",
    "Gounghin", "Patte d'Oie", "Tanghin", "ZAD",
    "Kossodo", "Gampéla", "Komsilga", "Sanyiri", "Boinsyaare",
    "1200 Logements", "Sissin",
]

PRIX_PAR_TYPE = {
    "TERRAIN": {"VENTE": (5_000_000, 45_000_000), "LOCATION": None},
    "VILLA": {"VENTE": (30_000_000, 120_000_000), "LOCATION": (300_000, 2_500_000)},
    "APPARTEMENT": {"VENTE": (50_000_000, 200_000_000), "LOCATION": (500_000, 5_000_000)},
    "BATIMENT": {"VENTE": (60_000_000, 400_000_000), "LOCATION": (500_000, 3_000_000)},
    "COMMERCE": {"VENTE": (40_000_000, 400_000_000), "LOCATION": (200_000, 3_000_000)},
}

SUPERFICIE_PAR_TYPE = {
    "TERRAIN": (150, 5000), "VILLA": (200, 800), "APPARTEMENT": (80, 500),
    "BATIMENT": (200, 2000), "COMMERCE": (50, 1000),
}

USAGES_PAR_TYPE = {
    "TERRAIN": ["RESIDENCE", "AGRICULTURE", "COMMERCE"],
    "VILLA": ["RESIDENCE"], "APPARTEMENT": ["RESIDENCE"],
    "BATIMENT": ["RESIDENCE", "BUREAU", "COMMERCE"],
    "COMMERCE": ["COMMERCE", "BUREAU"],
}

PREFIXES_DESC = {
    "TERRAIN": [
        "Magnifique terrain à bâtir situé dans un quartier calme et sécurisé.",
        "Superbe parcelle bien située, idéale pour construction de villa.",
        "Terrain viabilisé avec tous les branchements à proximité.",
        "Belle parcelle offrant une vue dégagée et un bon ensoleillement.",
        "Terrain clôturé prêt à construire, dans un lotissement moderne.",
    ],
    "VILLA": [
        "Belle villa moderne avec finitions de qualité et grande cour.",
        "Superbe villa avec salon spacieux, cuisine équipée et climatisation.",
        "Villa de standing avec jardin paysager et terrasse aménagée.",
        "Magnifique villa avec piscine, garage et dépendances.",
        "Villa récente avec matériaux de qualité, prête à habiter.",
    ],
    "APPARTEMENT": [
        "Bel appartement lumineux avec balcon et belle vue.",
        "Appartement moderne avec cuisine américaine et placards intégrés.",
        "Superbe duplex avec grande terrasse et espace vert.",
        "Appartement bien agencé, calme et sécurisé avec parking.",
        "Bel immeuble avec appartements traversants et ascenseur.",
    ],
    "BATIMENT": [
        "Immeuble moderne avec plusieurs niveaux, idéal pour investissement.",
        "Bâtiment commercial avec rez-de-chaussée et étages aménageables.",
        "Immeuble de standing avec finitions haut de gamme.",
        "Bâtiment mixte (commercial + résidentiel) bien situé.",
        "Immeuble récent avec ascenseur et parking souterrain.",
    ],
    "COMMERCE": [
        "Local commercial bien situé avec forte visibilité et passage.",
        "Bureau spacieux et lumineux dans un immeuble moderne.",
        "Magasin en coin avec grande vitrine et bonne exposition.",
        "Espace commercial aménagé, prêt à exploiter.",
        "Boutique avec dépôt, idéale pour commerce de détail.",
    ],
}

SUPPL_DESC = [
    "Proche des commerces, écoles et transports en commun.",
    "Accès facile, quartier sécurisé avec voisinage calme.",
    "À proximité des axes principaux et des commodités.",
    "Quartier recherché, en plein développement.",
    "Bonne desserte en eau et électricité, fibre optique disponible.",
    "Environnement verdoyant et agréable, loin des nuisances.",
]


def generer_description_clean(code, type_bien, texte):
    """Génère une description propre et lisible à partir du texte brut."""
    desc = texte.replace("-", " ").replace("CFA", "").replace("/mois", "").replace("/année", "").replace("/annees", "")
    desc = re.sub(r'A\s*\d[\d\s\.]*', '', desc).strip()
    desc = re.sub(r'\s+', ' ', desc).strip()
    desc = desc.lower().capitalize()
    prefixe = random.choice(PREFIXES_DESC.get(type_bien, PREFIXES_DESC["TERRAIN"]))
    supplement = random.choice(SUPPL_DESC)
    return f"{prefixe} {desc}. {supplement}"


class Command(BaseCommand):

    help = "Importe des annonces de test avec des données réalistes"

    def handle(self, *args, **kwargs):

        self.stdout.write("--- Création des utilisateurs ---")

        # --- MANAGER ---
        manager, created = Manager.objects.get_or_create(
            username="manager1",
            defaults={
                "email": "manager@immofaso.bf",
                "matricule": "MGR001",
                "telephone": "70-00-00-01",
            }
        )
        manager.set_password("123456")
        manager.save()
        self.stdout.write(self.style.SUCCESS(f"  ✓ Manager 'manager1' créé (mdp: 123456)"))

        # --- AGENTS ---
        agents = []
        for i in range(1, 3):
            agent, created = Agent.objects.get_or_create(
                username=f"agent{i}",
                defaults={
                    "email": f"agent{i}@immofaso.bf",
                    "matricule": f"AG00{i}",
                    "telephone": f"70-00-00-0{i+1}",
                }
            )
            agent.set_password("123456")
            agent.save()
            agents.append(agent)
            self.stdout.write(self.style.SUCCESS(f"  ✓ Agent 'agent{i}' créé (mdp: 123456)"))

        # --- BAILLEURS ---
        bailleurs = []
        for i in range(1, 3):
            bailleur, created = Bailleur.objects.get_or_create(
                username=f"bailleur{i}",
                defaults={
                    "email": f"bailleur{i}@immofaso.bf",
                    "telephone": f"70-00-00-0{i+3}",
                }
            )
            bailleur.set_password("123456")
            bailleur.save()
            bailleurs.append(bailleur)
            self.stdout.write(self.style.SUCCESS(f"  ✓ Bailleur 'bailleur{i}' créé (tél: 70-00-00-0{i+3}, mdp: 123456)"))

        # --- CLIENTS ---
        clients = []
        for i in range(1, 3):
            client, created = Client.objects.get_or_create(
                username=f"client{i}",
                defaults={
                    "email": f"client{i}@immofaso.bf",
                    "telephone": f"70-00-00-0{i+5}",
                }
            )
            client.set_password("123456")
            client.save()
            client.agent_affecte = random.choice(agents)
            client.save()
            clients.append(client)
            self.stdout.write(self.style.SUCCESS(f"  ✓ Client 'client{i}' créé (mdp: 123456)"))

        self.stdout.write(self.style.SUCCESS("\n✓ Tous les utilisateurs ont été créés\n"))

        # --- IMPORT DES ANNONCES ---
        self.stdout.write("--- Import des annonces ---\n")

        base_dir = os.path.join(settings.BASE_DIR, "donnee_BD")
        fichier_infos = os.path.join(base_dir, "informations.txt")

        with open(fichier_infos, encoding="utf-8") as f:
            lignes = [ligne.strip() for ligne in f.readlines() if ligne.strip()]

        mapping_types = {
            "P": ("TERRAIN", "parcelle et terrain"),
            "V": ("VILLA", "villa"),
            "I": ("APPARTEMENT", "immeuble et duplex et appartement"),
            "T": ("BATIMENT", "triplex"),
            "BO": ("COMMERCE", "local commercial et bureau et boutique"),
            "B": ("BATIMENT", "local commercial et bureau et boutique"),
            "C": ("COMMERCE", "local commercial et bureau et boutique"),
            "D": ("APPARTEMENT", "immeuble et duplex et appartement"),
            "E": ("COMMERCE", "local commercial et bureau et boutique"),
            "F": ("TERRAIN", "parcelle et terrain"),
        }

        compteur = 0
        codes_utilises = set()

        for ligne in lignes:
            if ":" not in ligne:
                continue

            code, texte = ligne.split(":", 1)
            code = code.strip().upper()
            texte = texte.strip()

            if not code or code in codes_utilises:
                continue

            codes_utilises.add(code)

            # --- Déterminer le type du bien ---
            type_bien = None
            dossier_images = None
            for prefix, (type_val, dossier) in sorted(mapping_types.items(), key=lambda x: -len(x[0])):
                if code.startswith(prefix):
                    type_bien = type_val
                    dossier_images = os.path.join(base_dir, dossier)
                    break

            if not type_bien:
                continue

            usage = random.choice(USAGES_PAR_TYPE[type_bien])

            # --- Superficie ---
            sup_min, sup_max = SUPERFICIE_PAR_TYPE[type_bien]
            superficie = round(random.uniform(sup_min, sup_max), 1)
            match_sup = re.search(r'(\d+)\s*M[²2]', texte, re.IGNORECASE)
            if match_sup:
                try:
                    superficie = float(match_sup.group(1))
                except:
                    pass

            # --- Option ---
            option = "VENTE"
            if "LOCATION" in texte.upper() or "LOUER" in texte.upper() or "/MOIS" in texte.upper() or "/ANN" in texte.upper():
                option = "LOCATION"

            # --- Prix ---
            fourchette = PRIX_PAR_TYPE[type_bien].get(option)
            if fourchette:
                prix_min, prix_max = fourchette
                prix = round(random.uniform(prix_min, prix_max) / 10000) * 10000
            else:
                prix = round(random.uniform(5_000_000, 20_000_000) / 10000) * 10000

            match_prix = re.search(r'(\d[\d\.]*)', texte)
            if match_prix:
                try:
                    prix_txt = float(match_prix.group(1).replace(".", ""))
                    if prix_txt > 10000:
                        prix = int(prix_txt)
                except:
                    pass

            # --- Localisation ---
            quartier = random.choice(QUARTIERS_OUAGA)
            localisation = f"Ouagadougou, Quartier {quartier}"
            for q in QUARTIERS_OUAGA:
                if q.upper().replace(" ", "") in texte.upper().replace("-", "").replace(" ", ""):
                    localisation = f"Ouagadougou, Quartier {q}"
                    break

            description = generer_description_clean(code, type_bien, texte)

            # --- Alterner bailleur / agence ---
            if compteur % 2 == 0:
                bailleur = random.choice(bailleurs)
                agent_createur = None
            else:
                bailleur = None
                agent_createur = random.choice(agents)

            # --- Création du bien ---
            bien = BienImmobilier.objects.create(
                proprietaire=bailleur,
                type=type_bien,
                usage=usage,
                superficie=superficie,
                ville="Ouagadougou",
                localisation=localisation,
                description=description
            )

            # --- Création de l'annonce ---
            annonce = Annonce.objects.create(
                bailleur=bailleur,
                agent_createur=agent_createur,
                agent_validateur=random.choice(agents) if random.random() > 0.3 else None,
                bien=bien,
                option=option,
                prix=prix,
                description=description,
                statut="PUBLIEE",
            )

            compteur += 1

            # --- Photo ---
            if dossier_images and os.path.isdir(dossier_images):
                image_trouvee = None
                for ext in ["jpg", "jpeg", "png", "webp", "jfif"]:
                    chemin = os.path.join(dossier_images, f"{code}.{ext}")
                    if os.path.exists(chemin):
                        image_trouvee = chemin
                        break

                if not image_trouvee:
                    images_dispo = []
                    for ext in ["jpg", "jpeg", "png", "webp", "jfif"]:
                        images_dispo.extend(glob.glob(os.path.join(dossier_images, f"*.{ext}")))
                    if images_dispo:
                        image_trouvee = random.choice(images_dispo)

                if image_trouvee:
                    try:
                        with open(image_trouvee, "rb") as img:
                            photo = Photo(bien=bien)
                            nom_fichier = f"{code}_{os.path.basename(image_trouvee)}"
                            photo.chemin_fichier.save(nom_fichier, File(img), save=True)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  ⚠ Erreur photo {code}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\n✓ {compteur} annonces importées avec succès !"))
        self.stdout.write("")
        self.stdout.write("--- Récapitulatif ---")
        self.stdout.write(f"  Manager:   manager1 / 123456")
        self.stdout.write(f"  Agents:    agent1, agent2 / 123456")
        self.stdout.write(f"  Bailleurs: bailleur1 (70-00-00-04), bailleur2 (70-00-00-05) / 123456")
        self.stdout.write(f"  Clients:   client1, client2 / 123456")
        self.stdout.write(f"  Annonces créées: {compteur}")