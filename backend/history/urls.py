from django.urls import path

from .views import HistoryDetailView, HistoryView


urlpatterns = [
    path("", HistoryView.as_view(), name="history-list"),
    path("<int:solution_id>/", HistoryDetailView.as_view(), name="history-detail"),
]
