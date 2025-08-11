from django.urls import path
from .views import SolveView, ResultView

urlpatterns = [
    path('solve/', SolveView.as_view()),
    path('result/<str:job_id>/', ResultView.as_view()),
]