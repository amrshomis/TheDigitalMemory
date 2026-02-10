from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Magazine

class MagazineListView(ListView):
    model = Magazine
    template_name = 'index.html'
    context_object_name = 'magazines'
    
    def get_queryset(self):
        return Magazine.objects.filter(is_active=True).order_by('-created_at')

class MagazineDetailView(DetailView):
    model = Magazine
    template_name = 'magazine_viewer.html'
    context_object_name = 'magazine'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch pages if they exist
        context['pages'] = self.object.pages.all()
        return context
