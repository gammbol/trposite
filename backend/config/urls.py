from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("solver.urls")),
    path("api/history/", include("history.urls")),
]
