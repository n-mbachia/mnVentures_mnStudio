from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from store import views as store_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sitemap.xml', store_views.sitemap,    name='sitemap'),
    path('robots.txt',  store_views.robots_txt, name='robots_txt'),
    path('', include('store.urls')),
    path('.well-known/appspecific/com.chrome.devtools.json', lambda r: HttpResponse(status=204)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
