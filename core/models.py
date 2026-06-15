from django.db import models
from django.contrib.auth.models import AbstractUser

# notre classe user herite de la classe user de base de django donc on a automatiquement nom ,prenom etc 
class Utilisateur(AbstractUser):
    telephone = models.CharField(max_length=20, blank=True)
    
    class Meta:
        verbose_name = 'Utilisateur'


class Client(Utilisateur):
    agent_affecte = models.ForeignKey(
        'Agent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clients'
    )

    class Meta:
        verbose_name = 'Client'


class Bailleur(Utilisateur):
    class Meta:
        verbose_name = 'Bailleur'


class Employe(Utilisateur):
    matricule = models.CharField(max_length=20, unique=True)

    class Meta:
        verbose_name = 'Employé'


class Agent(Employe):
    class Meta:
        verbose_name = 'Agent'


class Manager(Employe):
    class Meta:
        verbose_name = 'Manager'


class BienImmobilier(models.Model):
    TYPE_CHOICES = [
        ('TERRAIN', 'Terrain'),
        ('BATIMENT', 'Bâtiment'),
        ('APPARTEMENT', 'Appartement'),
        ('VILLA', 'Villa'),
        ('COMMERCE', 'Commerce'),
    ]
    USAGE_CHOICES = [
        ('RESIDENCE', 'Résidence'),
        ('BUREAU', 'Bureau'),
        ('COMMERCE', 'Commerce'),
        ('AGRICULTURE', 'Agriculture'),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    usage = models.CharField(max_length=20, choices=USAGE_CHOICES)
    superficie = models.FloatField()
    localisation = models.TextField()
    ville = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.type} — {self.ville}"

    class Meta:
        verbose_name = 'Bien Immobilier'







class Annonce(models.Model):
    OPTION_CHOICES = [
        ('LOCATION', 'Location'),
        ('VENTE', 'Vente'),
    ]
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente de validation'),
        ('PUBLIEE', 'Publiée'),
        ('RETIREE', 'Retirée'),
    ]

    bailleur = models.ForeignKey(
        Bailleur,
        on_delete=models.CASCADE,
        related_name='annonces'
    )
    bien = models.ForeignKey(
        BienImmobilier,
        on_delete=models.CASCADE,
        related_name='annonces'
    )
    agent_validateur = models.ForeignKey(
        Agent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='annonces_validees'
    )
    option = models.CharField(max_length=10, choices=OPTION_CHOICES)
    prix = models.FloatField()
    description = models.TextField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')
    date_publication = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bien} — {self.option} — {self.statut}"

    class Meta:
        verbose_name = 'Annonce'

class Photo(models.Model):
    annonce = models.ForeignKey(
        Annonce,
        on_delete=models.CASCADE,
        related_name='photos'
    )
    chemin_fichier = models.ImageField(upload_to='photos/proprietes/')
    date_ajout = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo de {self.annonce}"

    class Meta:
        verbose_name = 'Photo'

class DemandeVisite(models.Model):
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('VALIDEE', 'Validée'),
        ('REFUSEE', 'Refusée'),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='demandes'
    )
    annonce = models.ForeignKey(
        Annonce,
        on_delete=models.CASCADE,
        related_name='demandes'
    )
    date_demande = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')

    def __str__(self):
        return f"Demande de {self.client} pour {self.annonce} — {self.statut}"

    class Meta:
        verbose_name = 'Demande de visite'


class Favori(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='favoris'
    )
    annonce = models.ForeignKey(
        Annonce,
        on_delete=models.CASCADE,
        related_name='favoris'
    )
    date_ajout = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client} — {self.annonce}"

    class Meta:
        verbose_name = 'Favori'
        unique_together = ('client', 'annonce')