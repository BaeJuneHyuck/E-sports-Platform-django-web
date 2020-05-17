from django.conf import settings
from django.db.models import Q
from django.db.models.functions import math
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from .forms import ParticipateForm
from .models import Competition, CompetitionParticipate
from practice.models import Practice

class IndexView(generic.ListView):
    template_name = 'competitions/index.html'
    context_object_name = 'latest_competitions_list'
    def get_queryset(self):
        return Competition.objects.filter(pub_date__lte=timezone.now()).order_by('-pub_date')[:5]

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['ongoings'] = Competition.objects.filter(Q(date_start__lte=timezone.now()) & Q(date_end__gte=timezone.now())).order_by('-pub_date')[:5]
        context['scheduleds'] = Competition.objects.filter(date_start__gt=timezone.now()).order_by('-pub_date')[:5]
        context['pasts'] = Competition.objects.filter(date_end__lt=timezone.now()).order_by('-pub_date')[:5]
        return context


class DetailView(generic.DetailView):
    model = Competition
    template_name = 'competitions/detail.html'

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Competition.objects.filter(pub_date__lte=timezone.now())

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['total_competition'] = Competition.total_Competition()
        context['today'] = timezone.now().strftime("%Y-%m-%d")
        return context


class AttendView(generic.DetailView):
    login_url = settings.LOGIN_URL
    model = CompetitionParticipate
    template_name = 'competitions/attend.html'

    def attend(self):
        if not self.user.is_authenticated:
            return redirect('%s?next=%s' % (settings.LOGIN_URL, self.path))
        if self.method == 'POST':
            form = ParticipateForm(self.POST)
            if form.is_valid():
                participation = form.save(commit=False)
                participation.save()
                return redirect(reverse('competitions:index'))
            else:
                return HttpResponse('fail')
        else:
            form = ParticipateForm()
        return render(self, 'competitions/attend.html', {'form': form})


class OngoingView(generic.ListView):
    template_name = 'competitions/ongoing.html'
    context_object_name = 'latest_competitions_list'

    def get_queryset(self):
        return Competition.objects.filter(Q(date_start__lte=timezone.now()) & Q(date_end__gte=timezone.now())).order_by('-pub_date')

    def paging(request):
        competitions = Competition.objects
        competitions_list = Competition.objects.filter(pub_date__lte=timezone.now())
        paginator = Paginator(competitions_list, 10)
        page = request.GET.get('page', 1)
        page_range = 5  # 페이지 범위 5
        try:
            lines = paginator.page(page)
        except PageNotAnInteger:
            lines = paginator.page(1)
        except EmptyPage:
            lines = paginator.page(paginator.num_pages)
        current_block = math.ceil(int(page) / page_range)
        start_block = (current_block - 1)
        end_block = start_block + page_range
        p_range = paginator.page_range[start_block:end_block]
        total_page = page.num_pages()
        posts = paginator.get_page(page)
        return render(request, 'Ongoing.html', {'competitions': competitions, 'p_range': p_range})


class ScheduledView(generic.ListView):
    template_name = 'competitions/scheduled.html'
    context_object_name = 'scheduled_competitions_list'

    def get_queryset(self):
        return Competition.objects.filter(date_start__gt=timezone.now()).order_by('-pub_date')

    def paging(request):
        competitions = Competition.objects
        competitions_list = Competition.objects.filter(date_start__gt=timezone.now())
        paginator = Paginator(competitions_list, 1)
        page = request.GET.get('page', 1)
        try:
            lines = paginator.page(page)
        except PageNotAnInteger:
            lines = paginator.page(1)
        except EmptyPage:
            lines = paginator.page(paginator.num_pages)
        context = {'samelines': lines}
        total_page = page.num_pages()
        posts = paginator.get_page(page)
        return render(request, 'Ongoing.html', {'competitions': competitions, 'posts': posts}, context)


class PastView(generic.ListView):
    template_name = 'competitions/past.html'
    context_object_name = 'past_competitions_list'

    def get_queryset(self):
        return Competition.objects.filter(date_end__lt=timezone.now()).order_by('-pub_date')

    def paging(self):
        competitions = Competition.objects
        competitions_list = Competition.objects.filter(date_end__lt=timezone.now())
        paginator = Paginator(competitions_list, 1)
        page = self.GET.get('page', 1)
        try:
            lines = paginator.page(page)
        except PageNotAnInteger:
            lines = paginator.page(1)
        except EmptyPage:
            lines = paginator.page(paginator.num_pages)
        context = {'samelines': lines}
        total_page = page.num_pages()
        posts = paginator.get_page(page)
        return render(self, 'Ongoing.html', {'competitions': competitions, 'posts': posts}, context)
