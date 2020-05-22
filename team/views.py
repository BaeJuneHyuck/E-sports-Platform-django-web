from django.urls import reverse
from django.utils import timezone

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.views import generic
from django.views.generic import CreateView, FormView
from .models import Team, TeamRelation
from .forms import TeamCreateForm
from django.conf import settings
from user.models import User
from .forms import TeamRelationCreateForm

class IndexView(generic.ListView):
    template_name = 'team/index.html'
    context_object_name = 'teams'
    """
    전체 팀중에서 팀원으로 내가 팀원 으로 있는 경우
    """
    def get_queryset(self):
        myteams = TeamRelation.objects.filter(user_pk=self.request.user.pk).select_related('team_pk')
        return myteams[:5]

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['visible'] = Team.objects.filter(visible=True)
        return context


class CreateView(generic.CreateView):
    login_url = settings.LOGIN_URL
    model = Team

    def post_new(self):
        if not self.user.is_authenticated:
            return redirect('%s?next=%s' % (settings.LOGIN_URL, self.path))

        if self.method == 'POST':
            form = TeamCreateForm(self.POST)
            if form.is_valid():
                team = form.save(commit=False)
                team.master = self.user
                team.save()

                return redirect('team:detail', pk=team.pk)
            else:
                return HttpResponse('fail')
        else:
            form = TeamCreateForm()
        return render(self, 'team/create.html', {'form': form})



class DetailView(generic.DetailView):
    model = Team
    template_name = 'team/detail.html'

    def get_queryset(self):
        team=Team.objects.filter(pk=self.kwargs.get('pk'))
        return team

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['members'] = TeamRelation.objects.filter(team_pk = self.kwargs.get('pk'))
        return context

class InviteView(generic.ListView):
    template_name = 'team/invite.html'
    context_object_name = 'user'
    """
    전체 팀중에서 팀원으로 내가 팀원 으로 있는 경우
    """

    def get_queryset(self):
        user=User.objects.all()
        return user

    def get_context_data(self, **kwargs):
        context = super(generic.ListView, self).get_context_data(**kwargs)
        context['team'] = Team.objects.get(pk = self.kwargs.get('pk'))
        return context


class AttendView(generic.CreateView):
    login_url = settings.LOGIN_URL
    model = TeamRelation
    template_name = 'team/attend.html'

    def post_new(self, pk):
        if not self.user.is_authenticated:
            return redirect('%s?next=%s' % (settings.LOGIN_URL, self.path))

        if self.method == 'POST':
            form = TeamRelationCreateForm(self.POST)
            if form.is_valid():
                teamRelation = form.save(commit=False)
                teamRelation.team_pk = Team.objects.get(pk=pk)
                teamRelation.user_pk = self.user
                teamRelation.save()

                return redirect('team:detail', pk=pk)
            else:
                return HttpResponse('fail')
        else:
            form = TeamRelationCreateForm()
        return render(self, 'team/attend.html', {'form': form})
