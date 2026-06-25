import os
from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

SUPABASE_URL = "https://ufyorklvapdprugkxiem.supabase.co/storage/v1/object/public/media/photo/propriete"

@register.filter
@stringfilter
def supabase_url(value):
    """
    Prend le chemin d'un fichier (ex: photos/proprietes/P1_xxx.jpg)
    et retourne l'URL Supabase complète.
    """
    if not value:
        return ""
    nom_fichier = os.path.basename(value)
    return f"{SUPABASE_URL}/{nom_fichier}"