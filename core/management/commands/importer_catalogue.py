import os
import re
import glob
import random

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from core.models import (
    Agent,
    Bailleur,
    Client,
    BienImmobilier,
    Annonce,
    Photo
)


class Command(BaseCommand):

    help = "Importe des annonces de test"

    def handle(self, *args, **kwargs):

        self.stdout.write("Création des utilisateurs...")

        agents = [
            Agent.objects.get_or_create(
                username="agent1",
                defaults={
                    "email": "agent1@test.com",
                    "matricule": "AG001"
                }
            )[0],

            Agent.objects.get_or_create(
                username="agent2",
                defaults={
                    "email": "agent2@test.com",
                    "matricule": "AG002"
                }
            )[0]
        ]

        for agent in agents:
            agent.set_password("123456")
            agent.save()

        bailleurs = [
            Bailleur.objects.get_or_create(
                username="bailleur1",
                defaults={
                    "email": "bailleur1@test.com"
                }
            )[0],

            Bailleur.objects.get_or_create(
                username="bailleur2",
                defaults={
                    "email": "bailleur2@test.com"
                }
            )[0]
        ]

        for bailleur in bailleurs:
            bailleur.set_password("123456")
            bailleur.save()

        clients = [
            Client.objects.get_or_create(
                username="client1",
                defaults={
                    "email": "client1@test.com"
                }
            )[0],

            Client.objects.get_or_create(
                username="client2",
                defaults={
                    "email": "client2@test.com"
                }
            )[0]
        ]

        for client in clients:
            client.set_password("123456")
            client.save()

        self.stdout.write(self.style.SUCCESS("Utilisateurs créés"))

        base_dir = os.path.join(
            settings.BASE_DIR,
            "donnee_BD"
        )

        fichier_infos = os.path.join(
            base_dir,
            "informations.txt"
        )

        with open(
            fichier_infos,
            encoding="utf-8"
        ) as f:

            lignes = [
                ligne.strip()
                for ligne in f.readlines()
                if ligne.strip()
            ]

        compteur = 0

        for ligne in lignes:

            if ":" not in ligne:
                continue

            code, texte = ligne.split(":", 1)

            code = code.strip().upper()

            texte = texte.strip()

            compteur += 1

            # ---------- TYPE ----------

            dossier_images = None

            if code.startswith("P"):

                type_bien = "TERRAIN"

                dossier_images = os.path.join(
                    base_dir,
                    "parcelle et terrain"
                )

            elif code.startswith("V"):

                type_bien = "VILLA"

                dossier_images = os.path.join(
                    base_dir,
                    "villa"
                )

            elif code.startswith("I"):

                type_bien = "APPARTEMENT"

                dossier_images = os.path.join(
                    base_dir,
                    "immeuble et duplex et appartement"
                )

            elif code.startswith("T"):

                type_bien = "BATIMENT"

                dossier_images = os.path.join(
                    base_dir,
                    "triplex"
                )

            elif code.startswith("BO"):

                type_bien = "COMMERCE"

                dossier_images = os.path.join(
                    base_dir,
                    "local commercial et bureau et boutique"
                )

            else:
                continue

            # ---------- PRIX ----------

            prix = 10000000

            match_prix = re.search(
                r'(\d[\d\.]*)$',
                texte
            )

            if match_prix:

                prix_txt = (
                    match_prix.group(1)
                    .replace(".", "")
                )

                try:
                    prix = float(prix_txt)
                except:
                    pass

            # ---------- SUPERFICIE ----------

            superficie = 250

            match_sup = re.search(
                r'(\d+)\s*M',
                texte
            )

            if match_sup:

                try:
                    superficie = float(
                        match_sup.group(1)
                    )
                except:
                    pass

            # ---------- OPTION ----------

            option = "VENTE"

            if "LOCATION" in texte:
                option = "LOCATION"

            # ---------- BIEN ----------

            if compteur % 2 == 0:

                bailleur = random.choice(
                    bailleurs
                )

                agent_createur = None

            else:

                bailleur = None

                agent_createur = random.choice(
                    agents
                )

            bien = BienImmobilier.objects.create(

                proprietaire=bailleur,

                type=type_bien,

                usage="RESIDENCE",

                superficie=superficie,

                ville="Ouagadougou",

                localisation="Ouagadougou",

                description=texte
            )

            annonce = Annonce.objects.create(

                bailleur=bailleur,

                agent_createur=agent_createur,

                bien=bien,

                option=option,

                prix=prix,

                description=texte,

                statut="PUBLIEE"
            )

            # ---------- PHOTO ----------

            extensions = [
                "jpg",
                "jpeg",
                "png",
                "webp",
                "jfif"
            ]

            image_trouvee = None

            print(f"\n=== Recherche image pour {code} ===")
            print(f"Dossier : {dossier_images}")

            for ext in extensions:

                chemin = os.path.join(
                    dossier_images,
                    f"{code}.{ext}"
                )

                print(f"Test : {chemin}")

                if os.path.exists(chemin):

                    print(f"✅ Image trouvée : {chemin}")

                    image_trouvee = chemin

                    break

            if image_trouvee:

                try:

                    with open(
                        image_trouvee,
                        "rb"
                    ) as img:

                        photo = Photo(
                            bien=bien
                        )

                        photo.chemin_fichier.save(
                            os.path.basename(
                                image_trouvee
                            ),
                            File(img),
                            save=True
                        )

                        print(
                            f"✅ Photo enregistrée en base : "
                            f"{photo.chemin_fichier.name}"
                        )

                except Exception as e:

                    print(
                        f"❌ Erreur lors de l'enregistrement : {e}"
                    )

            else:

                print(
                    f"❌ Aucune image trouvée pour {code}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"{compteur} annonces importées"
            )
        )