from django.contrib import admin
from .models import (
    Utilisateur, Client, Bailleur,
    Employe, Agent, Manager,
    BienImmobilier, Annonce, Photo,
    DemandeVisite, Favori
)

admin.site.register(Utilisateur)
admin.site.register(Client)
admin.site.register(Bailleur)
admin.site.register(Employe)
admin.site.register(Agent)
admin.site.register(Manager)
admin.site.register(BienImmobilier)
admin.site.register(Annonce)
admin.site.register(Photo)
admin.site.register(DemandeVisite)
admin.site.register(Favori)