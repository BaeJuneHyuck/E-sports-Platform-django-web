from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone

# avoid race conditions
from django.db.models import F

from .models import Competition


class IndexView(generic.ListView):
    template_name = 'competitions/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        return Competition.objects.filter(pub_date__lte=timezone.now()).order_by('-pub_date')[:5]

class DetailView(generic.DetailView):
    model = Competition
    template_name = 'competitions/detail.html'

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Competition.objects.filter(pub_date__lte=timezone.now())

class AttendView(generic.DetailView):
    model = Competition
    template_name = 'competitions/attend.html'
