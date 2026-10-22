from django.urls import path
from .views import SimilaridadeView, TextEventView

urlpatterns = [
    # API endpoints
    path('similaridade/', SimilaridadeView.as_view(), name='api_similaridade'),
    path('eventos/', TextEventView.as_view(), name='api_eventos'),
    path('eventos/<int:pk>/', TextEventView.as_view(), name='api_evento_detalhe'),
]