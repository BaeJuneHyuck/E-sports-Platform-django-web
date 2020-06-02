from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import generic
from django.utils import timezone
from .models import Competition, CompetitionParticipate
from team.models import TeamInvitation
from .forms import CompetitionCreateForm
from django.urls import reverse


NOW = timezone.now()

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
        context['invitations']= TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[:5]
        return context


class CommentForm(object):
    pass


class DetailView(generic.DetailView):
    model = Competition
    template_name = 'competitions/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['total_competition'] = Competition.total_competition()
        context['today'] = timezone.now()
        context['invitations']= TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[:5]
        return context

class CreateView(generic.CreateView):
    login_url = settings.LOGIN_URL
    model = Competition

    def post_new(self):
        if not self.user.is_authenticated:
            return redirect('%s?next=%s' % (settings.LOGIN_URL, self.path))

        invitations= TeamInvitation.objects.filter(invited_pk=self.user.pk).filter(checked=False)[:5]

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
                return render(self, 'competitions/create.html', {'form': form, 'invitations':invitations})
        return render(self, 'competitions/create.html', {'form': form, 'invitations':invitations})



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
    queryset = Competition.objects.filter(state='ONGOING').order_by('-pub_date')
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super(OngoingView, self).get_context_data(**kwargs)
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
        context['invitations']= TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[:5]

        return context


class ScheduledView(generic.ListView):
    template_name = 'competitions/scheduled.html'
    context_object_name = 'scheduled_competitions_list'
    queryset = Competition.objects.filter(state='SCHEDULED').order_by('-pub_date')
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super(ScheduledView, self).get_context_data(**kwargs)
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
        context['invitations']= TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[:5]

        return context


class PastView(generic.ListView):
    template_name = 'competitions/past.html'
    context_object_name = 'past_competitions_list'

    def get_queryset(self):
        return Competition.objects.filter(date_end__lt=timezone.now()).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super(PastView, self).get_context_data(**kwargs)
        context['invitations']= TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[:5]
        return context
