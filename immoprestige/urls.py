from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # toutes les routes de core
]



if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]

    
# Pour servir les fichiers médias (photos) en développement
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)