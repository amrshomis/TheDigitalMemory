from django.urls import path
from . import views

urlpatterns = [
    path('', views.MagazineListView.as_view(), name='index'),
    path('magazine/<slug:slug>/', views.MagazineDetailView.as_view(), name='magazine_detail'),
]
