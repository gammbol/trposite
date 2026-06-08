from django.urls import path

from .views import ExplainView, ResultView, SolveView


urlpatterns = [
    path('solve/', SolveView.as_view()),
    path('explain/', ExplainView.as_view()),
    path('result/<str:job_id>/', ResultView.as_view()),
]
