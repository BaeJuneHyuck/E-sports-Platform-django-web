from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.shortcuts import render, redirect
from django.views import generic
from .models import Competition, CompetitionParticipate, Match
from team.models import TeamInvitation, TeamRelation
from .forms import CompetitionCreateForm, CompetitionAttendForm
from django.contrib import messages
import random
import math

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
        past_competition = Competition.objects.filter(date_end__lt=NOW).order_by('-pub_date')
        for competition in ongoing_competition:
            competition.state = 'Ongoing'
            competition.save()
        for competition in scheduled_competition:
            competition.state = 'Scheduled'
            competition.save()
        for competition in past_competition:
            competition.state = 'Past'
            competition.save()
        context['ongoings'] = ongoing_competition[:5]
        context['scheduleds'] = scheduled_competition[:5]
        context['pasts'] = past_competition[:5]
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
            next = Competition.objects.get(Q(state=state) & Q(page_num=page_num + 1))
            context['next'] = next
        if page_num - 1 > 0 and page_num!=0:
            previous = Competition.objects.get(Q(state=state) & Q(page_num=page_num - 1))
            context['previous'] = previous
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
                    makeMatches(pk)

                messages.info(self, '참가 신청이 완료되었습니다.')
                return redirect('competitions:detail', pk=competition.pk)
            else:
                print("form invalid")
                return render(self, 'competitions/attend.html',
                              {'form': form, 'invitations': invitations, 'competition': competition,
                               'myteams': myteams})
        return render(self, 'competitions/attend.html',
                      {'form': form, 'invitations': invitations, 'competition': competition, 'myteams': myteams})


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
                qs = qs.filter(mast_name__icontains=query)
            elif attribute == 'game':
                qs = qs.filter(competition_game__icontains=query)
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
                #qs = qs.filter(mast_name__icontains=query)
                qs = qs.filter(master__name=query)
            elif attribute == 'game':
                qs = qs.filter(competition_game__icontains=query)
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
        return context


class CurrentPastView(generic.ListView):
    model = Competition
    template_name = 'competitions/past.html'
    context_object_name = 'past_competitions_list'

    def get_context_data(self, **kwargs):
        context = super(CurrentPastView, self).get_context_data(**kwargs)
        competition_current_list = Competition.objects.filter(
            Q(date_start__gt=one_years) & Q(date_end__lt=NOW)).order_by('-pub_date')
        competition_last_list = Competition.objects.filter(
            Q(date_start__gt=two_years) & Q(date_end__lt=one_years)).order_by('-pub_date')
        competition_last_last_list = Competition.objects.filter(
            Q(date_start__gt=three_years) & Q(date_end__lt=two_years)).order_by('-pub_date')
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
        context['invitations'] = TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[
                                 :5]
        context['current_year'] = competition_current_list
        context['last_year'] = competition_last_list
        context['last_last_year'] = competition_last_last_list

        paginator = Paginator(competition_current_list, 2)
        page_current = self.request.GET.get('page1')
        try:
            competition_current_list = paginator.page(page_current)
        except PageNotAnInteger:
            competition_current_list = paginator.page(1)
        except EmptyPage:
            competition_current_list = paginator.page(paginator.num_pages)

        context['competition_current_list'] = competition_current_list

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

        page_range_last = paginator.page_range[start_index:end_index]
        context['page_range_last'] = page_range_last

        return context

class LastPastView(CurrentPastView):

    def get_queryset(self):
        return Competition.objects.filter(
            Q(date_start__gt=two_years) & Q(date_end__lt=one_years)).order_by('-pub_date')

class LastLastPastView(CurrentPastView):

    def get_queryset(self):
        return Competition.objects.filter(
            Q(date_start__gt=three_years) & Q(date_end__lt=two_years)).order_by('-pub_date')

class BracketsView(generic.DetailView):
    model = Competition
    template_name = 'competitions/brackets.html'

    def get_context_data(self, **kwargs):
        context = super(BracketsView, self).get_context_data(**kwargs)
        context['today'] = NOW
        context['invitations'] = TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[:5]
        context['matches1'] = Match.objects.filter(competition=self.kwargs.get('pk')).filter(round=1)
        context['matches2'] = Match.objects.filter(competition=self.kwargs.get('pk')).filter(round=2)
        context['matches3'] = Match.objects.filter(competition=self.kwargs.get('pk')).filter(round=3)
        context['matches4'] = Match.objects.filter(competition=self.kwargs.get('pk')).filter(round=4)
        context['matches5'] = Match.objects.filter(competition=self.kwargs.get('pk')).filter(round=5)
        context['matches6'] = Match.objects.filter(competition=self.kwargs.get('pk')).filter(round=6)
        context['matches7'] = Match.objects.filter(competition=self.kwargs.get('pk')).filter(round=7)
        return context


class MatchView(generic.DetailView):
    model = Match
    template_name = 'competitions/match.html'

    def get_context_data(self, **kwargs):
        context = super(MatchView, self).get_context_data(**kwargs)
        context['today'] = NOW
        context['invitations'] = TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[:5]
        return context


"""
대회에 참가중인 팀에게 1번부터 팀번호 할당 <작성완료>
=> (12팀->1경기),  34팀->2경기,  56팀->3경기 ...(1round)
   (1경기승자,2경기승자-> x경기) , ... ( 2round)
   (준결승승자, 준결승승자->결승전) (last round)
    이렇게 경기정보 생성
    
=> 이후 대진표 에서는 해당 정보를 읽어서 대진표 그리기 
"""
def makeMatches(competition_pk):
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

    for i in teams_for_match:
        print(i)

    match_number = 0
    prev_round_match_number = 0
    current_round = 1
    
    # 1라운드 생성
    while teams_for_match: # 남은팀이없음 즉, 모든팀이 매치에 들어감 => 종료
        match_number = match_number + 1
        prev_round_match_number = prev_round_match_number + 1

        team1 = teams_for_match.pop(0)
        
        # 남은 팀이 없음 , 즉 team1의 경기는 부전승으로 생성
        if not teams_for_match:
            Match.objects.create(
                game = competition.competition_game,
                competition=competition,
                number = match_number,
                round = 1,
                team1 = team1,
                result = 0)
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
                result = 0)

    # 이후 2라운드 이상 필요한경우( 이전 라운드에 실행한 match가 두개이상인 경우) => 반복
    while prev_round_match_number != 1 :    # 이전 라운드의 경기가 하나밖에없었다 => 결승전임, 루프 종료
        print("이전 라운드 경기수:" + str(prev_round_match_number))

        current_round = current_round + 1       # 라운드 증가
        current_round_match = math.floor(prev_round_match_number / 2)  # 이번 라운드에서 해야할 경기
        if prev_round_match_number % 2 == 1:      # 홀수번 경기를 했다면? -> 부전승경기 하나 더 해야함
            current_round_match = current_round_match + 1
        prev_round_match_number = 0         # 라운드의 경기수 초기화

        print("지금 라운드:" + str(current_round) + "이번라운드 경기" + str(current_round_match))
        
        # 해당 라운드의 경기들을 생성
        while current_round_match > 0 :  # 만들어야할 매치가 남아있으면 반복
            current_round_match = current_round_match - 1
            match_number = match_number + 1
            prev_round_match_number = prev_round_match_number + 1
            print('\t' + str(match_number))

            Match.objects.create(
                    game = competition.competition_game,
                    competition=competition,
                    number = match_number,
                    round = current_round,
                    result = 0)

    #대회에 몇 라운드까지 있는지 기록
    competition.rounds = current_round
    competition.save()
