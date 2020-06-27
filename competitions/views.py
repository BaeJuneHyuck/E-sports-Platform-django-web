from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.shortcuts import render, redirect
from django.views import generic
from .models import Competition, CompetitionParticipate, Match, MatchComment
from team.models import TeamInvitation, TeamRelation, Team
from user.models import User
from .forms import CompetitionCreateForm, CompetitionAttendForm, MatchEditForm, MatchCommentForm, CompetitionInviteForm
from django.contrib import messages
import random
import math
import itertools
from django.utils import timezone


NOW = datetime.now() + relativedelta(seconds=1)
one_years = NOW + relativedelta(years=-1)
two_years = NOW + relativedelta(years=-2)
three_years = NOW + relativedelta(years=-3)


class IndexView(generic.ListView):
    template_name = 'competitions/index.html'
    context_object_name = 'latest_competitions_list'

    def get_queryset(self):
        return Competition.objects.filter(pub_date__lte=NOW).order_by('-pub_date')[:5]

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        ongoing_competition = Competition.objects.filter(Q(date_start__lte=NOW) & Q(date_end__gte=NOW)).order_by('-pub_date')
        scheduled_competition = Competition.objects.filter(date_start__gt=NOW).order_by('-pub_date')
        for competition in ongoing_competition:
            competition.state = 'Ongoing'
            competition.save()
        for competition in scheduled_competition:
            competition.state = 'Scheduled'
            competition.save()
        context['ongoings'] = ongoing_competition[:5]
        context['scheduleds'] = scheduled_competition[:5]
        context['invitations'] = TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[
                                 :5]
        context['current_year'] = NOW.strftime('%Y')
        context['last_year'] = one_years.strftime('%Y')
        context['last_last_year'] = two_years.strftime('%Y')
        return context


class CommentForm(object):
    pass


class DetailView(generic.DetailView):
    model = Competition
    template_name = 'competitions/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        i=1
        context['otherteams'] = CompetitionParticipate.objects.filter(competition=self.kwargs.get('pk')).select_related(
            'team')
        context['total_competition'] = Competition.total_competition()
        context['today'] = NOW
        context['invitations'] = TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[
                                 :5]
        state = self.object.state
        print(state)
        page_num = self.object.page_num
        competition_list = Competition.objects.filter(state=state)
        for competition in competition_list:
            competition.page_num = i
            competition.save()
            i += 1
        context['state'] = state
        if page_num + 1 <= competition_list.count() and page_num!=0:
            next_page = Competition.objects.get(Q(state=state) & Q(page_num=page_num + 1))
            context['next'] = next_page
        if page_num - 1 > 0 and page_num!=0:
            previous_page = Competition.objects.get(Q(state=state) & Q(page_num=page_num - 1))
            context['previous'] = previous_page
        context['notSetting'] = 0
        return context


class CreateView(generic.CreateView):
    login_url = settings.LOGIN_URL
    model = Competition

    def post_new(self):
        if not self.user.is_authenticated:
            return redirect('%s?next=%s' % (settings.LOGIN_URL, self.path))

        invitations = TeamInvitation.objects.filter(invited_pk=self.user.pk).filter(checked=False)[:5]

        form = CompetitionCreateForm(self.POST)
        if self.method == 'POST':
            form = CompetitionCreateForm(self.POST)
            if form.is_valid():
                print("form valid")
                competition = form.save(commit=False)
                competition.master = self.user

                data = form.cleaned_data
                type = data['tournament_type']
                rounds = data['rounds']
                if type == "-1" or type == "-2":
                    competition.rounds = 1
                else:
                    competition.rounds = rounds

                competition.save()
                return redirect('competitions:detail', pk=competition.pk)
            else:
                print("form invalid")
                return render(self, 'competitions/create.html', {'form': form, 'invitations': invitations})
        return render(self, 'competitions/create.html', {'form': form, 'invitations': invitations})


class AttendView(generic.DetailView):
    login_url = settings.LOGIN_URL
    model = CompetitionParticipate

    def post_new(self, pk):
        if not self.user.is_authenticated:
            return redirect('%s?next=%s' % (settings.LOGIN_URL, self.path))

        competition = Competition.objects.get(pk=pk)
        if competition.current_teams >= competition.total_teams:
            messages.info(self, '신청이 마감된 대회입니다')
            return redirect('competitions:detail', pk=competition.pk)

        invitations = TeamInvitation.objects.filter(invited_pk=self.user.pk).filter(checked=False)[:5]
        myteams = TeamRelation.objects.filter(user_pk=self.user.pk).select_related('team_pk')
        form = CompetitionAttendForm(self.user.pk, self.POST)
        if self.method == 'POST':
            form = CompetitionAttendForm(self.user.pk, self.POST)
            if form.is_valid():
                data = form.cleaned_data
                selected_team = data['team']
                find_team = CompetitionParticipate.objects.filter(competition =competition).filter(team= selected_team)
                if find_team:
                    messages.success(self, '해당 팀은 이미 대회에 참가중입니다')
                    return redirect('/competitions/attend/' + str(pk))

                competitionParticipate = form.save(commit=False)
                competitionParticipate.competition = Competition.objects.get(pk=pk)
                competitionParticipate.save()

                competition = Competition.objects.get(pk=pk)
                competition.current_teams = competition.current_teams + 1
                competition.save()

                # 팀 신청 종료 -> 자동으로 매칭 생성
                if competition.current_teams == competition.total_teams:
                    if competition.tournament_type == -1:
                        makeSingleMatches(pk)
                    elif competition.tournament_type == -2:
                        makeDoubleMatches(pk)
                    else:
                        makeRoundRobin(pk, competition.tournament_type )

                messages.info(self, '참가 신청이 완료되었습니다.')
                return redirect('competitions:detail', pk=competition.pk)
            else:
                print("form invalid")
                return render(self, 'competitions/attend.html',
                              {'form': form, 'invitations': invitations, 'competition': competition,
                               'myteams': myteams})
        return render(self, 'competitions/attend.html',
                      {'form': form, 'invitations': invitations, 'competition': competition, 'myteams': myteams})


class InviteView(generic.FormView):
    template_name = 'competitions/invite.html'
    model = Competition
    form_class = CompetitionInviteForm

    success_url = '/team/'

    def get_context_data(self, **kwargs):
        context = super(InviteView, self).get_context_data(**kwargs)
        context['competition'] = Competition.objects.get(pk=self.kwargs.get('pk'))
        return context

    def form_valid(self, form):
        competition_pk = self.kwargs.get('pk')
        competition = Competition.objects.get(pk=competition_pk)
        f = form.save(commit=False)
        f.competition = competition
        team = form.cleaned_data['team']

        if CompetitionParticipate.objects.filter(team=team).filter(
                competition=competition).exists():
            messages.error(self.request, '이미 초대한 팀입니다.')
            return redirect(self.request.path_info)
        else:
            f.save()
            messages.success(self.request, str(team) + '을 초대했습니다')

            competition.current_teams = competition.current_teams + 1
            competition.save()

            # 팀 신청 종료 -> 자동으로 매칭 생성
            if competition.current_teams == competition.total_teams:
                if competition.tournament_type == -1:
                    makeSingleMatches(competition_pk)
                elif competition.tournament_type == -2:
                    makeDoubleMatches(competition_pk)
                else:
                    makeRoundRobin(competition_pk, competition.tournament_type )
            return redirect('competitions:detail', pk=competition.pk)


class OngoingView(generic.ListView):
    template_name = 'competitions/ongoing.html'
    context_object_name = 'latest_competitions_list'
    queryset = Competition.objects.filter(
        Q(date_start__lte=NOW) & Q(date_end__gte=NOW)).order_by('-pub_date')[:5]
    paginate_by = 10

    def get_queryset(self, *args, **kwargs):
        qs = Competition.objects.filter(Q(date_start__lt=NOW) & Q(date_end__gt=NOW)).order_by('-pub_date')
        query = self.request.GET.get("qs", None)
        attribute = self.request.GET.get("attribute", None)
        if query is not None:
            if attribute == 'title':
                qs = qs.filter(competition_name__icontains=query)
            elif attribute == 'master':
                qs = qs.filter(master__name__icontains=query)
            elif attribute == 'game':
                qs = qs.filter(competition_game__icontains=query)
            elif attribute == 'tier':
                qs = qs.filter(required_tier__icontains=query)
            elif attribute == 'text':
                qs = qs.filter(competition_text__icontains=query)
        return qs

    def get_context_data(self, **kwargs):
        context = super(OngoingView, self).get_context_data(**kwargs)
        competition_list = Competition.objects.filter(Q(date_start__lt=NOW) & Q(date_end__gt=NOW)).order_by('-pub_date')
        i = 1
        for competition in competition_list:
            competition.page_num = i
            competition.state = 'ongoing'
            competition.save()
            i += 1
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
        attribute = self.request.GET.get("attribute", None)
        context['attribute'] = attribute
        context['current_year'] = NOW.strftime('%Y')
        context['last_year'] = one_years.strftime('%Y')
        context['last_last_year'] = two_years.strftime('%Y')
        return context


class ScheduledView(generic.ListView):
    template_name = 'competitions/scheduled.html'
    context_object_name = 'scheduled_competitions_list'
    queryset = Competition.objects.filter(state='SCHEDULED').order_by('-pub_date')
    paginate_by = 10

    def get_queryset(self, *args, **kwargs):
        qs = Competition.objects.filter(date_start__gt=NOW).order_by('-pub_date')
        query = self.request.GET.get("qs", None)
        print(query)
        attribute = self.request.GET.get("attribute", None)
        if query is not None:
            if attribute == 'title':
                qs = qs.filter(competition_name__icontains=query)
            elif attribute == 'master':
                qs = qs.filter(master__name__icontains=query)
            elif attribute == 'game':
                qs = qs.filter(competition_game__icontains=query)
            elif attribute == 'tier':
                qs = qs.filter(required_tier__icontains=query)
            elif attribute == 'text':
                qs = qs.filter(competition_text__icontains=query)
        print(self.request.GET)
        return qs

    def get_context_data(self, **kwargs):
        context = super(ScheduledView, self).get_context_data(**kwargs)
        competition_list = Competition.objects.filter(date_start__gt=NOW).order_by('-pub_date')
        i = 1
        for competition in competition_list:
            competition.page_num = i
            competition.state = 'scheduled'
            competition.save()
            i += 1
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
        attribute = self.request.GET.get("attribute", None)
        context['attribute'] = attribute
        context['current_year'] = NOW.strftime('%Y')
        context['last_year'] = one_years.strftime('%Y')
        context['last_last_year'] = two_years.strftime('%Y')
        return context


class CurrentPastView(generic.ListView):
    model = Competition
    template_name = 'competitions/past.html'
    context_object_name = 'past_competitions_list'
    paginate_by = 2

    def get_queryset(self, *args, **kwargs):
        qs = Competition.objects.filter(
            Q(date_start__gt=one_years) & Q(date_end__lt=NOW)).order_by('-pub_date').order_by('-pub_date')
        query = self.request.GET.get("qs", None)
        print(query)
        attribute = self.request.GET.get("attribute", None)
        if query is not None:
            if attribute == 'title':
                qs = qs.filter(competition_name__icontains=query)
            elif attribute == 'master':
                qs = qs.filter(master__name__icontains=query)
            elif attribute == 'game':
                qs = qs.filter(competition_game__icontains=query)
            elif attribute == 'tier':
                qs = qs.filter(required_tier__icontains=query)
            elif attribute == 'text':
                qs = qs.filter(competition_text__icontains=query)
        print(self.request.GET)
        return qs

    def get_context_data(self, **kwargs):
        context = super(CurrentPastView, self).get_context_data(**kwargs)
        competition_current_list = Competition.objects.filter(
            Q(date_start__gt=one_years) & Q(date_end__lt=NOW)).order_by('-pub_date')
        competition_last_list = Competition.objects.filter(
            Q(date_start__gt=two_years) & Q(date_end__lt=one_years)).order_by('-pub_date')
        competition_last_last_list = Competition.objects.filter(
            Q(date_start__gt=three_years) & Q(date_end__lt=two_years)).order_by('-pub_date')
        competition_past = Competition.objects.filter(Q(date_start__lt=three_years)).order_by('-pub_date')
        i = 1
        for competition in competition_current_list:
            competition.page_num = i
            competition.state = 'current_past'
            competition.save()
            i += 1
        i = 1
        for competition in competition_last_list:
            competition.page_num = i
            competition.state = 'last_past'
            competition.save()
            i += 1
        i = 1
        for competition in competition_last_last_list:
            competition.page_num = i
            competition.state = 'last_last_past'
            competition.save()
            i += 1
        for competition in competition_past:
            competition.state = 'past'
            competition.save()
            i += 1
        context['invitations'] = TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[
                                 :5]
        # Pagination

        paginator = Paginator(competition_current_list, 2)
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
        context['state'] = 'current_past'
        context['current_year'] = NOW.strftime('%Y')
        context['last_year'] = one_years.strftime('%Y')
        context['last_last_year'] = two_years.strftime('%Y')

        return context

class LastPastView(generic.ListView):
    model = Competition
    template_name = 'competitions/past.html'
    context_object_name = 'past_competitions_list'
    paginate_by = 2

    def get_queryset(self):
        qs = Competition.objects.filter(
            Q(date_start__gt=two_years) & Q(date_end__lt=one_years)).order_by('-pub_date')
        query = self.request.GET.get("qs", None)
        print(query)
        attribute = self.request.GET.get("attribute", None)
        if query is not None:
            if attribute == 'title':
                qs = qs.filter(competition_name__icontains=query)
            elif attribute == 'master':
                qs = qs.filter(master__name__icontains=query)
            elif attribute == 'game':
                qs = qs.filter(competition_game__icontains=query)
            elif attribute == 'tier':
                qs = qs.filter(required_tier__icontains=query)
            elif attribute == 'text':
                qs = qs.filter(competition_text__icontains=query)
        return qs

    def get_context_data(self, **kwargs):
        context = super(LastPastView, self).get_context_data(**kwargs)
        competition_last_list = Competition.objects.filter(
            Q(date_start__gt=two_years) & Q(date_end__lt=one_years)).order_by('-pub_date')
        competition_past = Competition.objects.filter(Q(date_start__lt=three_years)).order_by('-pub_date')
        i = 1
        for competition in competition_last_list:
            competition.page_num = i
            competition.state = 'last_past'
            competition.save()
            i += 1
        i = 1
        for competition in competition_past:
            competition.state = 'past'
            competition.save()
            i += 1
        context['invitations'] = TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[
                                 :5]

        # Pagination

        paginator = Paginator(competition_last_list, 2)
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
        context['state'] = 'last_past'

        return context

class LastLastPastView(generic.ListView):
    model = Competition
    template_name = 'competitions/past.html'
    context_object_name = 'past_competitions_list'
    paginate_by = 2

    def get_queryset(self):
        qs = Competition.objects.filter(
            Q(date_start__gt=three_years) & Q(date_end__lt=two_years)).order_by('-pub_date')
        query = self.request.GET.get("qs", None)
        print(query)
        attribute = self.request.GET.get("attribute", None)
        if query is not None:
            if attribute == 'title':
                qs = qs.filter(competition_name__icontains=query)
            elif attribute == 'master':
                qs = qs.filter(master__name__icontains=query)
            elif attribute == 'game':
                qs = qs.filter(competition_game__icontains=query)
            elif attribute == 'tier':
                qs = qs.filter(required_tier__icontains=query)
            elif attribute == 'text':
                qs = qs.filter(competition_text__icontains=query)
        return qs

    def get_context_data(self, **kwargs):
        context = super(LastLastPastView, self).get_context_data(**kwargs)
        competition_last_last_list = Competition.objects.filter(
            Q(date_start__gt=three_years) & Q(date_end__lt=two_years)).order_by('-pub_date')
        competition_past = Competition.objects.filter(Q(date_start__lt=three_years)).order_by('-pub_date')
        i = 1
        for competition in competition_last_last_list:
            competition.page_num = i
            competition.state = 'last_last_past'
            competition.save()
            i += 1
        for competition in competition_past:
            competition.state = 'past'
            competition.save()
            i += 1
        context['invitations'] = TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[
                                 :5]
        # Pagination

        paginator = Paginator(competition_last_last_list, 2)
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
        context['state'] = 'last_last_past'

        return context

class BracketsView(generic.DetailView):
    model = Competition

    template_name = 'competitions/brackets.html'
    def get_context_data(self, **kwargs):
        context = super(BracketsView, self).get_context_data(**kwargs)
        context['today'] = NOW
        context['invitations'] = TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[:5]
        
        # 승리가 많은순, 패배가 적은순 정렬
        context['teams'] = CompetitionParticipate.objects.filter(competition=self.kwargs.get('pk')).order_by('lose').order_by('-win')
        context['matches1'] = Match.objects.filter(competition=self.kwargs.get('pk')).filter(round=1)
        context['matches2'] = Match.objects.filter(competition=self.kwargs.get('pk')).filter(round=2)
        context['matches3'] = Match.objects.filter(competition=self.kwargs.get('pk')).filter(round=3)
        context['matches4'] = Match.objects.filter(competition=self.kwargs.get('pk')).filter(round=4)
        context['matches5'] = Match.objects.filter(competition=self.kwargs.get('pk')).filter(round=5)
        context['matches6'] = Match.objects.filter(competition=self.kwargs.get('pk')).filter(round=6)
        context['matches7'] = Match.objects.filter(competition=self.kwargs.get('pk')).filter(round=7)
        context['matches8'] = Match.objects.filter(competition=self.kwargs.get('pk')).filter(round=8)
        return context


class MatchView(generic.DetailView):
    model = Match
    template_name = 'competitions/match.html'

    def get_context_data(self, **kwargs):
        context = super(MatchView, self).get_context_data(**kwargs)
        context['today'] = NOW
        context['invitations'] = TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[:5]
        match = Match.objects.get(pk=self.kwargs.get('pk'))
        context['master'] = User.objects.get(pk=match.competition.master.pk)
        context['comments'] = MatchComment.objects.filter(match=match)
        return context

    def comment(self, match_pk):
        match = Match.objects.get(pk=match_pk)
        comments = MatchComment.objects.filter(match=match)
        total_match = Match.total_match()
        today = NOW.strftime("%Y-%m-%d")
        if self.method == 'POST':
            form = MatchCommentForm(self.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.author = self.user
                comment.match = match
                comment.save()
            else:
                return HttpResponse('fail')
        else:
            form = MatchCommentForm()

        invitations = TeamInvitation.objects.filter(invited_pk=self.user.pk).filter(checked=False)[:5]

        return render(self, 'competitions/match.html', {'match': match, 'comments': comments, 'form': form,
                                                     'total_match': total_match, 'today': today,
                                                     'invitations': invitations})

    def delete(self, match_pk, comment_pk):
        delete_comment = MatchComment.objects.get(pk=comment_pk)
        delete_comment.delete()
        match = Match.objects.get(pk=match_pk)
        comments = MatchComment.objects.filter(match=match)
        total_match = Match.total_match()
        today = NOW.strftime("%Y-%m-%d")
        form = CommentForm()
        invitations = TeamInvitation.objects.filter(invited_pk=self.user.pk).filter(checked=False)[:5]

        return render(self, 'competitions/match.html', {'match': match, 'comments': comments, 'form': form,
                                                     'total_match': total_match, 'today': today,
                                                     'invitations': invitations})



class MatchEditView(generic.UpdateView):
    template_name = 'competitions/match_edit.html'
    model = Match
    form_class=MatchEditForm

    def get(self, request, pk ):
        match = Match.objects.get(pk=pk)
        competition_pk = match.competition.pk
        competition = Competition.objects.get(pk=competition_pk)
        master = User.objects.get(pk=match.competition.master.pk)
        if self.request.user != master :
            messages.success(self.request, '대회 관리자만 수정할 수 있습니다')
            return redirect('/competitions/match/' + str(pk))

        form = MatchEditForm(competition_pk, instance=match)
        invitations= TeamInvitation.objects.filter(invited_pk=request.user.pk).filter(checked=False)[:5]

        args = {'form': form, 'invitations':invitations, 'match':match , 'competition':competition}
        return render(request, self.template_name, args)

    def post(self, request, pk):
        match = Match.objects.get(pk=pk)
        competition_pk = match.competition.pk
        competition = Competition.objects.get(pk=competition_pk)
        form =  MatchEditForm(competition_pk, request.POST, instance=match)
        invitations= TeamInvitation.objects.filter(invited_pk=request.user.pk).filter(checked=False)[:5]
        if form.is_valid():
            f = form.save(commit=False)
            data = form.cleaned_data
            result = data['result']
            if result == "1":
                f.result = 1
            elif result == "2":
                f.result = 2
            elif result == "3":
                f.result = 3
            elif result == "0":
                f.result = 0
            elif result == "-1":
                f.result = -1
            f.save()

            # 라운드로빈이면 매치 결과로 승점 계산 실행
            competition =Competition.objects.get(pk=competition_pk)
            if competition.tournament_type >= 1:
                calculate_score(competition_pk)

            messages.info(request, '경기 정보를 수정했습니다')
            return redirect('/competitions/match/' + str(pk))
        args = {'form': form, 'invitations':invitations, 'match':match , 'competition':competition}
        return render(request, self.template_name, args)

def calculate_score(competition_pk):
    # 승패 0으로 초기화
    relations =CompetitionParticipate.objects.filter(competition=competition_pk)
    for relation in relations:
        relation.win=0
        relation.lose=0
        relation.save()

    # 모든 경기로 다시 계산
    allmatches = Match.objects.filter(competition=competition_pk)
    for match in allmatches:
        if match.team1 == None:
            print(str(match) + "team1 none")
            continue
        if match.team2 == None:
            print(str(match)+"team2 none")
            continue
        team1 = CompetitionParticipate.objects.filter(competition=competition_pk).get(team = match.team1.pk)
        team2 = CompetitionParticipate.objects.filter(competition=competition_pk).get(team = match.team2.pk)
        if match.result == 1:
            team1.win = team1.win+1
            team2.lose = team2.lose+1
        elif match.result == 2:
            team2.win = team2.win+1
            team1.lose = team1.lose+1
        team1.save()
        team2.save()

"""
대회에 참가중인 팀에게 1번부터 팀번호 할당
=> (12팀->1경기),  34팀->2경기,  56팀->3경기 ...(1round)
   (1경기승자,2경기승자-> x경기) , ... ( 2round)
   (준결승승자, 준결승승자->결승전) (last round)
    이렇게 경기정보 생성
"""
def makeSingleMatches(competition_pk):
    competition=Competition.objects.get(pk=competition_pk)
    allRelations = CompetitionParticipate.objects.filter(competition=competition_pk).select_related('team')
    current_number = 1

    team_number = []
    teams_for_match = []
    for relation in allRelations:
        team_number.append(relation.pk)

    random.shuffle(team_number)
    while team_number:
        pk = team_number.pop()
        relation = CompetitionParticipate.objects.get(pk=pk)
        relation.team_number = current_number
        relation.save()
        teams_for_match.append(relation.team)
        current_number= current_number+1

    match_number = 0
    prev_round_match_number = 0
    current_round = 1
    prev_won_by_default_team = None # 이전라운드에 부전승이 있엇다 => 이번 라운드 마지막경기도 부전승으로 만들어야함
    # 1라운드 생성
    while teams_for_match: # 남은팀이없음 즉, 모든팀이 매치에 들어감 => 종료
        match_number = match_number + 1
        prev_round_match_number = prev_round_match_number + 1

        team1 = teams_for_match.pop(0)

        # 남은 팀이 없음 , 즉 team1의 경기는 부전승으로 생성
        if not teams_for_match:
            prev_won_by_default_team = team1
            Match.objects.create(
                game = competition.competition_game,
                competition=competition,
                number = match_number,
                round = 1,
                team1 = team1,
                result = -1,
                date=timezone.now())
            break;

        # 팀1, 팀2가 선정됨 => 정상적인 match 생성
        else:
            team2 = teams_for_match.pop(0)
            Match.objects.create(
                game = competition.competition_game,
                competition=competition,
                number = match_number,
                round = 1,
                team1 = team1,
                team2 = team2,
                result = 0,
                date=timezone.now())


    # 이후 2라운드 이상 필요한경우( 이전 라운드에 실행한 match가 두개이상인 경우) => 반복
    while prev_round_match_number != 1 :    # 이전 라운드의 경기가 하나밖에없었다 => 결승전임, 루프 종료
        print("이전 라운드 경기수:" + str(prev_round_match_number))

        current_round = current_round + 1       # 라운드 증가
        current_round_match = math.floor(prev_round_match_number / 2)  # 이번 라운드에서 해야할 경기
        if prev_round_match_number % 2 == 1:      # 홀수번 경기를 했다면? -> 부전승경기 하나 더 해야함
            current_round_match = current_round_match + 1
        saved_prev_round_match_number = prev_round_match_number
        prev_round_match_number = 0         # 라운드의 경기수 초기화

        print("지금 라운드:" + str(current_round) + "이번라운드 경기" + str(current_round_match))

        # 해당 라운드의 경기들을 생성
        while current_round_match > 0 :  # 만들어야할 매치가 남아있으면 반복
            current_round_match = current_round_match - 1
            match_number = match_number + 1
            prev_round_match_number = prev_round_match_number + 1
            print('\t' + str(match_number))

            if prev_won_by_default_team and current_round_match ==0 : # 이전라운드에 부전승있으면 이번라운드 마지막경기도 홀수인원인 부전승일것
                if (saved_prev_round_match_number % 2) == 0:  # 다음번 라운드부터는 부전승이없다 => 마지막 부전승이다 => 뒤집어 줘야함
                    Match.objects.create(
                        game = competition.competition_game,
                        competition=competition,
                        number = match_number,
                        round = current_round,
                        team2= prev_won_by_default_team,
                        result = -1,
                        date=timezone.now())
                    prev_won_by_default_team = None
                else:
                    Match.objects.create(
                        game = competition.competition_game,
                        competition=competition,
                        number = match_number,
                        round = current_round,
                        team1= prev_won_by_default_team,
                        result = -1,
                        date=timezone.now())
            else:
                Match.objects.create(
                    game = competition.competition_game,
                    competition=competition,
                    number = match_number,
                    round = current_round,
                    result = 0,
                    date=timezone.now())


    #대회에 몇 라운드까지 있는지 기록
    competition.rounds = current_round
    competition.save()


def makeDoubleMatches(competition_pk):
    competition=Competition.objects.get(pk=competition_pk)
    allRelations = CompetitionParticipate.objects.filter(competition=competition_pk).select_related('team')
    current_number = 1

    team_number = []
    teams_for_match = []
    for relation in allRelations:
        team_number.append(relation.pk)

    random.shuffle(team_number)
    while team_number:
        pk = team_number.pop()
        relation = CompetitionParticipate.objects.get(pk=pk)
        relation.team_number = current_number
        relation.save()
        teams_for_match.append(relation.team)
        current_number= current_number+1

    match_number = 0
    prev_round_match_number = 0
    current_round = 1
    prev_won_by_default_team = None # 이전라운드에 부전승이 있엇다 => 이번 라운드 마지막경기도 부전승으로 만들어야함
    # 1라운드 생성
    while teams_for_match: # 남은팀이없음 즉, 모든팀이 매치에 들어감 => 종료
        match_number = match_number + 1
        prev_round_match_number = prev_round_match_number + 1

        team1 = teams_for_match.pop(0)

        # 남은 팀이 없음 , 즉 team1의 경기는 부전승으로 생성
        if not teams_for_match:
            prev_won_by_default_team = team1
            Match.objects.create(
                game = competition.competition_game,
                competition=competition,
                number = match_number,
                round = 1,
                team1 = team1,
                result = -1,
                date=timezone.now())
            break;

        # 팀1, 팀2가 선정됨 => 정상적인 match 생성
        else:
            team2 = teams_for_match.pop(0)
            Match.objects.create(
                game = competition.competition_game,
                competition=competition,
                number = match_number,
                round = 1,
                team1 = team1,
                team2 = team2,
                result = 0,
                date=timezone.now())


    # 이후 2라운드 이상 필요한경우( 이전 라운드에 실행한 match가 두개이상인 경우) => 반복
    while prev_round_match_number != 1 :    # 이전 라운드의 경기가 하나밖에없었다 => 결승전임, 루프 종료
        print("이전 라운드 경기수:" + str(prev_round_match_number))

        current_round = current_round + 1       # 라운드 증가
        current_round_match = math.floor(prev_round_match_number / 2)  # 이번 라운드에서 해야할 경기
        if prev_round_match_number % 2 == 1:      # 홀수번 경기를 했다면? -> 부전승경기 하나 더 해야함
            current_round_match = current_round_match + 1
        saved_prev_round_match_number = prev_round_match_number
        prev_round_match_number = 0         # 라운드의 경기수 초기화

        print("지금 라운드:" + str(current_round) + "이번라운드 경기" + str(current_round_match))

        # 해당 라운드의 경기들을 생성
        while current_round_match > 0 :  # 만들어야할 매치가 남아있으면 반복
            current_round_match = current_round_match - 1
            match_number = match_number + 1
            prev_round_match_number = prev_round_match_number + 1
            print('\t' + str(match_number))

            if prev_won_by_default_team and current_round_match ==0 : # 이전라운드에 부전승있으면 이번라운드 마지막경기도 홀수인원인 부전승일것
                if (saved_prev_round_match_number % 2) == 0:  # 다음번 라운드부터는 부전승이없다 => 마지막 부전승이다 => 뒤집어 줘야함
                    Match.objects.create(
                        game = competition.competition_game,
                        competition=competition,
                        number = match_number,
                        round = current_round,
                        team2= prev_won_by_default_team,
                        result = -1,
                        date=timezone.now())
                    prev_won_by_default_team = None
                else:
                    Match.objects.create(
                        game = competition.competition_game,
                        competition=competition,
                        number = match_number,
                        round = current_round,
                        team1= prev_won_by_default_team,
                        result = -1,
                        date=timezone.now())
            else:
                Match.objects.create(
                    game = competition.competition_game,
                    competition=competition,
                    number = match_number,
                    round = current_round,
                    result = 0,
                    date=timezone.now())


    #대회에 몇 라운드까지 있는지 기록
    competition.rounds = current_round
    competition.save()


def makeRoundRobin(competition_pk, rounds):
    competition=Competition.objects.get(pk=competition_pk)
    allRelations = CompetitionParticipate.objects.filter(competition=competition_pk).select_related('team')
    current_number = 1

    team_number = []
    teams_for_match = []
    for relation in allRelations:
        team_number.append(relation.pk)

    random.shuffle(team_number)
    while team_number:
        pk = team_number.pop()
        relation = CompetitionParticipate.objects.get(pk=pk)
        relation.team_number = current_number
        relation.save()
        teams_for_match.append(relation.team)
        current_number= current_number+1

    match_number = 0
    current_round = 0

    while current_round != competition.rounds :
        current_round = current_round + 1       # 라운드 증가
        print("현재라운드:"+str(current_round))
        random.shuffle(teams_for_match)
        matches = itertools.combinations(teams_for_match, 2)
        print(matches)
        for match in matches:
            print (match)
            match_number = match_number + 1
            Match.objects.create(
                    game = competition.competition_game,
                    competition=competition,
                    number = match_number,
                    round = current_round,
                    team1 = match[0],
                    team2 = match[1],
                    result = 0,
                    date=timezone.now())


    #대회에 몇 라운드까지 있는지 기록
    competition.rounds = current_round
    competition.save()
