from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.views import generic
from django.views.generic import CreateView, FormView, TemplateView

import practice
from practice.models import Comment, Practice
from .models import Team, TeamInvitation, TeamRelation
from .forms import TeamCreateForm
from django.conf import settings
from user.models import User
from .forms import TeamRelationCreateForm, TeamInvitationCreateForm, TeamInvitationUpdateForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages


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
        context['visible'] = Team.objects.filter(visible=True)[:5]
        context['invitations'] = TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[:5]
        comments = Comment.objects.filter(Q(author=self.request.user) & Q(content__contains="참가신청합니다")).values_list('practice', flat=True).distinct()[:5]
        practices = Practice.objects.filter(pk__in=comments)
        context['practices'] = practices
        print(comments)
        return context


class MyteamView(generic.ListView):
    template_name = 'team/myteam.html'
    context_object_name = 'myteams'
    paginate_by = 10

    def get_queryset(self):
        myteams = TeamRelation.objects.filter(user_pk=self.request.user.pk).select_related('team_pk')
        return myteams

    def get_context_data(self, **kwargs):
        context = super(MyteamView, self).get_context_data(**kwargs)
        paginator = context['paginator']
        page_numbers_range = 5  # Display only 5 page numbers
        max_index = len(paginator.page_range)

        page = self.request.GET.get('page')
        current_page = int(page) if page else 1

        start_index = int((current_page - 1) / page_numbers_range) * page_numbers_range
        end_index = start_index + page_numbers_range
        if end_index >= max_index:
            end_index = max_index

        page_range = paginator.page_range[start_index:end_index]
        context['page_range'] = page_range
        context['invitations'] = TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[
                                 :5]
        return context


class ListView(generic.ListView):
    template_name = 'team/list.html'
    context_object_name = 'teams'
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        if query:
            myteams = Team.objects.filter(visible=True).filter(name__icontains=query)
        else:
            myteams = Team.objects.filter(visible=True)
        return myteams

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        paginator = context['paginator']
        page_numbers_range = 5  # Display only 5 page numbers
        max_index = len(paginator.page_range)

        page = self.request.GET.get('page')
        current_page = int(page) if page else 1

        start_index = int((current_page - 1) / page_numbers_range) * page_numbers_range
        end_index = start_index + page_numbers_range
        if end_index >= max_index:
            end_index = max_index

        page_range = paginator.page_range[start_index:end_index]
        context['invitations'] = TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[
                                 :5]
        context['page_range'] = page_range
        return context


class MyInvitationView(generic.ListView):
    template_name = 'team/myinvitation.html'
    context_object_name = 'invitations'
    paginate_by = 10

    def get_queryset(self):
        invitations = TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[:5]
        return invitations

    def get_context_data(self, **kwargs):
        context = super(MyInvitationView, self).get_context_data(**kwargs)
        paginator = context['paginator']
        page_numbers_range = 5  # Display only 5 page numbers
        max_index = len(paginator.page_range)

        page = self.request.GET.get('page')
        current_page = int(page) if page else 1

        start_index = int((current_page - 1) / page_numbers_range) * page_numbers_range
        end_index = start_index + page_numbers_range
        if end_index >= max_index:
            end_index = max_index

        page_range = paginator.page_range[start_index:end_index]
        context['page_range'] = page_range
        return context

class MyPracticeView(generic.ListView):
    template_name = 'team/mypractice.html'
    context_object_name = 'practices'
    paginate_by = 10

    def get_queryset(self):
        comments = Comment.objects.filter(Q(author=self.request.user) & Q(content__contains="참가신청합니다")).values_list(
            'practice', flat=True).distinct()
        practices = Practice.objects.filter(pk__in=comments)
        return practices

    def get_context_data(self, **kwargs):
        context = super(MyPracticeView, self).get_context_data(**kwargs)
        paginator = context['paginator']
        page_numbers_range = 5  # Display only 5 page numbers
        max_index = len(paginator.page_range)

        page = self.request.GET.get('page')
        current_page = int(page) if page else 1

        start_index = int((current_page - 1) / page_numbers_range) * page_numbers_range
        end_index = start_index + page_numbers_range
        if end_index >= max_index:
            end_index = max_index

        page_range = paginator.page_range[start_index:end_index]
        context['page_range'] = page_range
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

                TeamRelation.objects.create(team_pk=team, user_pk=self.user)
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
        team = Team.objects.filter(pk=self.kwargs.get('pk'))
        return team

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['members'] = TeamRelation.objects.filter(team_pk=self.kwargs.get('pk'))
        context['invitations'] = TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[
                                 :5]
        return context


"""
    초대 보내기
"""


class InviteView(generic.FormView):
    template_name = 'team/invite.html'
    model = TeamInvitation
    form_class = TeamInvitationCreateForm

    success_url = '/team/'

    def get_context_data(self, **kwargs):
        context = super(InviteView, self).get_context_data(**kwargs)
        context['team'] = Team.objects.get(pk=self.kwargs.get('pk'))
        return context

    def form_valid(self, form):
        f = form.save(commit=False)
        f.team_pk = Team.objects.get(pk=self.kwargs.get('pk'))
        f.inviter_pk = self.request.user
        invited_user = form.cleaned_data['name']

        if not User.objects.filter(name=invited_user).exists():
            messages.error(self.request, '알 수 없는 사용자 입니다.')
            return redirect(self.request.path_info)
        elif TeamRelation.objects.filter(team_pk=self.kwargs.get('pk')).filter(
                user_pk=User.objects.get(name=invited_user).pk).exists():
            messages.error(self.request, '이미 가입된 멤버입니다.')
            return redirect(self.request.path_info)
        elif TeamInvitation.objects.filter(team_pk=self.kwargs.get('pk')).filter(
                invited_pk=User.objects.get(name=invited_user).pk).exists():
            messages.error(self.request, '이미 초대한 멤버입니다.')
            return redirect(self.request.path_info)
        else:
            f.invited_pk = User.objects.get(name=invited_user)
            f.save()
            messages.success(self.request, invited_user + '님을 초대했습니다')
            return redirect(self.request.path_info)


# 받은 초대
class InvitationView(generic.UpdateView):
    model = TeamInvitation
    template_name = 'team/invitation.html'
    form_class = TeamInvitationUpdateForm
    success_url = '/'

    def get_context_data(self, **kwargs):
        context = super(InvitationView, self).get_context_data(**kwargs)
        TeamInvitationObject = TeamInvitation.objects.get(pk=self.kwargs.get('pk'))
        context['team'] = Team.objects.get(pk=TeamInvitationObject.team_pk.pk)
        context['invitations'] = TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[
                                 :5]
        return context

    def form_valid(self, form):
        team_pk = TeamInvitation.objects.get(pk=self.kwargs.get('pk')).team_pk.pk
        team = Team.objects.get(pk=team_pk)
        f = form.save(commit=False)
        f.checked = True
        f.save()
        if f.accepted:
            messages.success(self.request, '초대를 수락했습니다')

            relation = TeamRelation(team_pk=team, user_pk=self.request.user)
            relation.save()
            return redirect('/team/detail/' + str(team_pk))
        else:
            messages.success(self.request, '초대를 거절했습니다')
            return redirect(self.request.path_info)


class AttendView(generic.CreateView):
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
