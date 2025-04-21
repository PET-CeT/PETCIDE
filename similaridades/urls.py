from django.urls import path
from .views import SimilaridadeView, TextEventView

urlpatterns = [
    path('similaridade/', SimilaridadeView.as_view()),
    path('text-event-import/', TextEventView.as_view()),
]