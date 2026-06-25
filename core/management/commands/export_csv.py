import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Exporte chaque table SQLite en CSV (colonnes exactes de la base)"

    def handle(self, *args, **kwargs):
        export_dir = os.path.join(settings.BASE_DIR, "exports_csv")
        os.makedirs(export_dir, exist_ok=True)

        # Tables à exporter (nom_table_sqlite -> nom_fichier)
        tables = [
            "core_utilisateur",
            "core_employe",
            "core_agent",
            "core_manager",
            "core_bailleur",
            "core_client",
            "core_bienimmobilier",
            "core_photo",
            "core_annonce",
            "core_demandevisite",
            "core_favori",
        ]

        with connection.cursor() as cursor:
            for table in tables:
                # Récupérer les colonnes exactes dans l'ordre SQLite
                cursor.execute(f"PRAGMA table_info({table})")
                cols = cursor.fetchall()
                col_names = [c[1] for c in cols]  # c[1] = column name

                # Lire toutes les lignes
                cursor.execute(f"SELECT * FROM {table} ORDER BY {col_names[0]}")
                rows = cursor.fetchall()

                filepath = os.path.join(export_dir, f"{table}.csv")
                with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(col_names)
                    for row in rows:
                        writer.writerow(row)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ {table}.csv — {len(col_names)} colonnes, {len(rows)} lignes"
                    )
                )

        self.stdout.write(self.style.SUCCESS(f"\n📁 Dossier : {export_dir}"))