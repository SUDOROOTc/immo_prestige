from django import template
from core.models import Client, Agent, Bailleur, Manager

register = template.Library()

@register.filter
def is_client(user):
    return Client.objects.filter(pk=user.pk).exists()

@register.filter
def is_agent(user):
    return Agent.objects.filter(pk=user.pk).exists()

@register.filter
def is_bailleur(user):
    return Bailleur.objects.filter(pk=user.pk).exists()

@register.filter
def is_manager(user):
    return Manager.objects.filter(pk=user.pk).exists()
