from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('similaridades.urls')),
    path('api/users/', include('users.urls')),
    
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('textos/', TemplateView.as_view(template_name='similaridades/textos.html'), name='textos'),
    path('similaridade/', TemplateView.as_view(template_name='similaridades/similaridade.html'), name='similaridade'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register'),
    path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile'),
]
