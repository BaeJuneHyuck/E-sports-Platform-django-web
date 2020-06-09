from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.shortcuts import render, redirect
from django.views import generic
from .models import Competition, CompetitionParticipate
from team.models import TeamInvitation, TeamRelation
from .forms import CompetitionCreateForm, CompetitionAttendForm
from django.contrib import messages

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
            messages.info(self, '신청이 마감된 대회입니다.')
            return redirect('competitions:detail', pk=competition.pk)

        invitations = TeamInvitation.objects.filter(invited_pk=self.user.pk).filter(checked=False)[:5]
        myteams = TeamRelation.objects.filter(user_pk=self.user.pk).select_related('team_pk')
        form = CompetitionAttendForm(self.user.pk, self.POST)
        if self.method == 'POST':
            form = CompetitionAttendForm(self.user.pk, self.POST)
            if form.is_valid():
                print("form valid")
                competitionParticipate = form.save(commit=False)
                competitionParticipate.competition = Competition.objects.get(pk=pk)
                competitionParticipate.save()

                competition = Competition.objects.get(pk=pk)
                competition.current_teams = competition.current_teams + 1
                competition.save()

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
                qs = qs.filter(master_name__icontains=query)
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
        attribute = self.request.GET.get("attribute", None)
        if query is not None:
            if attribute == 'title':
                qs = qs.filter(competition_name__icontains=query)
            elif attribute == 'master':
                qs = qs.filter(master_name__icontains=query)
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