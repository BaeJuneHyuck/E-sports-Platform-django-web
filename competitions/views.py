from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import generic
from django.utils import timezone
from .models import Competition, CompetitionParticipate


class IndexView(generic.ListView):
    template_name = 'competitions/index.html'
    context_object_name = 'latest_competitions_list'

    def get_queryset(self):
        return Competition.objects.filter(pub_date__lte=timezone.now()).order_by('-pub_date')[:5]

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['ongoings'] = Competition.objects.filter(
            Q(date_start__lte=timezone.now()) & Q(date_end__gte=timezone.now())).order_by('-pub_date')[:5]
        context['scheduleds'] = Competition.objects.filter(date_start__gt=timezone.now()).order_by('-pub_date')[:5]
        context['pasts'] = Competition.objects.filter(date_end__lt=timezone.now()).order_by('-pub_date')[:5]
        return context


class CommentForm(object):
    pass


class DetailView(generic.DetailView):
    model = Competition
    template_name = 'competitions/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['total_competition'] = Competition.total_competition()
        context['today'] = timezone.now().strftime("%Y-%m-%d")
        return context


class AttendView(generic.DetailView):
    login_url = settings.LOGIN_URL
    model = CompetitionParticipate
    template_name = 'competitions/attend.html'

    def attend(self):
        if not self.user.is_authenticated:
            return redirect('%s?next=%s' % (settings.LOGIN_URL, self.path))
        return HttpResponse('not yet :(')


class OngoingView(generic.ListView):
    template_name = 'competitions/ongoing.html'
    context_object_name = 'latest_competitions_list'

    def get_queryset(self):
        return Competition.objects.filter(Q(date_start__lte=timezone.now()) & Q(date_end__gte=timezone.now())).order_by(
            '-pub_date')


class ScheduledView(generic.ListView):
    template_name = 'competitions/scheduled.html'
    context_object_name = 'scheduled_competitions_list'

    def get_queryset(self):
        return Competition.objects.filter(date_start__gt=timezone.now()).order_by('-pub_date')


class PastView(generic.ListView):
    template_name = 'competitions/past.html'
    context_object_name = 'past_competitions_list'

    def get_queryset(self):
        return Competition.objects.filter(date_end__lt=timezone.now()).order_by('-pub_date')
