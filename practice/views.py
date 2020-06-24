import datetime

from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse
from django.views import generic

from django.shortcuts import redirect, render, get_object_or_404
from .forms import PracticeCreateForm, CommentForm
from team.models import TeamInvitation
from practice.models import Practice, Comment, User, PracticeParticipate
from django.conf import settings

NOW = datetime.datetime.now()
one_years = NOW+relativedelta(years=-1)
two_years = NOW+relativedelta(years=-2)
three_years = NOW+relativedelta(years=-3)

class IndexView(generic.ListView):
    model = Practice
    template_name = 'practice/index.html'

    def get_context_data(self, *args, **kwargs):
        context = super(IndexView, self).get_context_data(*args,**kwargs)
        context['practices'] = Practice.objects.all().order_by('-pub_date')[:5]

        if self.request.user.is_authenticated:
            attend_practice = PracticeParticipate.objects.filter(user=self.request.user)[:5]
            context['attend_practice'] = attend_practice
        return context

class TotalListView(generic.ListView):
    template_name = 'practice/list.html'
    context_object_name = 'practices'
    queryset = Practice.objects.filter(practice_time__gt=three_years)
    paginate_by = 10

    def get_queryset(self, *args, **kwargs):
        qs = Practice.objects.all()
        query = self.request.GET.get("qs", None)
        attribute = self.request.GET.get("attribute", None)
        if query is not None:
            if attribute == 'title':
                qs = qs.filter(title__icontains=query)
            elif attribute == 'author':
                qs = qs.filter(author__name__icontains=query)
            elif attribute == 'tier':
                qs = qs.filter(tier__icontains=query)
            elif attribute == 'text':
                qs = qs.filter(text__icontains=query)
            elif attribute == 'game':
                qs = qs.filter(game__icontains=query)
        return qs

    def get_context_data(self, *args, **kwargs):
        context = super(TotalListView, self).get_context_data(*args,**kwargs)
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

        attribute = self.request.GET.get("attribute", None)
        context['attribute'] = attribute
        return context

class MyListView(generic.ListView):
    template_name = 'practice/mypractice.html'
    context_object_name = 'practices'
    paginate_by = 10

    def get_queryset(self, *args, **kwargs):
        qs = PracticeParticipate.objects.filter(user=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        context = super(MyListView, self).get_context_data(**kwargs)
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

class SortTitleListView(TotalListView):
    def get_queryset(self, *args, **kwargs):
        qs = Practice.objects.all()
        qs = qs.order_by('title')
        return qs

class SortTierListView(TotalListView):
    def get_queryset(self, *args, **kwargs):
        qs = Practice.objects.all()
        qs = qs.order_by('tier')
        return qs

class SortPracticeTimeListView(TotalListView):
    def get_queryset(self, *args, **kwargs):
        qs = Practice.objects.all()
        qs = qs.order_by('-practice_time')
        return qs

class SortGameListView(TotalListView):
    def get_queryset(self, *args, **kwargs):
        qs = Practice.objects.all()
        qs = qs.order_by('game')
        return qs


class DetailView(generic.DetailView):
    model = Practice
    template_name = 'practice/detail.html'
    context_object_name = 'practice'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        comments = Comment.objects.filter(practice=self.object.pk)
        total_practice = Practice.total_practice()
        practice_time = self.object.practice_time.strftime("%Y-%m-%d")
        today = NOW.strftime("%Y-%m-%d")
        context['comments'] = comments
        context['total_practice'] = total_practice
        context['today'] = today
        context['practice_time'] = practice_time

        form = CommentForm(self.request.POST or None)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = self.user
            comment.practice = self.object
            comment.save()
            print('댓글작성완료')
            self.particiate(comment)
        else:
            form = CommentForm()
        context['form'] = form
        return context

    def particiate(self, comment):
        if '참가신청합니다' in comment.content:
            if PracticeParticipate.objects.filter(practice=self.object, user=self.user):
                pass
            else:
                PracticeParticipate.objects.create(practice=self.object, user=self.user)
            print('참가신청완료')
        else:
            print('참가신청실패')

    def new_comment(self, practice_pk):
        practice = Practice.objects.get(pk=practice_pk)
        comments = Comment.objects.filter(practice=practice)
        total_practice = Practice.total_practice()
        today = NOW.strftime("%Y-%m-%d")
        practice_time = practice.practice_time.strftime("%Y-%m-%d")

        form = CommentForm(self.request.POST or None)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = self.user
            comment.practice = practice
            comment.save()
            self.particiate(comment)
        else:
            return HttpResponse('fail')

        return render(self, 'practice/detail.html', {'practice': practice, 'comments': comments, 'form': form,
                                                     'total_practice': total_practice, 'today': today,
                                                     practice_time: practice_time})

    def delete(self, practice_pk, comment_pk):
        delete_comment = Comment.objects.filter(pk=comment_pk)
        delete_comment.delete()
        if not Comment.objects.filter(practice__pk=practice_pk, author=self.user):
            delete_practiceParticipate = PracticeParticipate.objects.filter(practice__pk=practice_pk, user=self.user)
            delete_practiceParticipate.delete()
        practice = Practice.objects.get(pk=practice_pk)
        comments = Comment.objects.filter(practice=practice)
        total_practice = Practice.total_practice()
        today = NOW.strftime("%Y-%m-%d")
        practice_time = practice.practice_time.strftime("%Y-%m-%d")

        form = CommentForm(self.request.POST or None)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = self.user
            comment.practice = practice
            comment.save()
            self.particiate(comment)
        else:
            return HttpResponse('fail')

        return render(self, 'practice/detail.html', {'practice': practice, 'comments': comments, 'form': form,
                                                     'total_practice': total_practice, 'today': today,
                                                     practice_time: practice_time})

    def delete_all(self, practice_pk):
        delete_comment = Comment.objects.filter(practice__pk=practice_pk, author__pk=self.user.pk)
        delete_practiceParticipate = PracticeParticipate.objects.filter(practice__pk=practice_pk, user=self.user)
        delete_comment.delete()
        delete_practiceParticipate.delete()
        practice = Practice.objects.get(pk=practice_pk)
        comments = Comment.objects.filter(practice=practice)
        total_practice = Practice.total_practice()
        today = NOW.strftime("%Y-%m-%d")
        practice_time = practice.practice_time.strftime("%Y-%m-%d")

        form = CommentForm(self.request.POST or None)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = self.user
            comment.practice = practice
            comment.save()
            self.particiate(comment)
        else:
            return HttpResponse('fail')

        return render(self, 'practice/detail.html', {'practice': practice, 'comments': comments, 'form': form,
                                                     'total_practice': total_practice, 'today': today,
                                                     'practice_time': practice_time})


class CreateView(generic.CreateView):
    login_url = settings.LOGIN_URL
    model = Practice

    def post_new(self):
        if not self.user.is_authenticated:
            return redirect('%s?next=%s' % (settings.LOGIN_URL, self.path))

        form = PracticeCreateForm(self.POST)
        if self.method == 'POST':
            form = PracticeCreateForm(self.POST)
            if form.is_valid():
                practice = form.save(commit=False)
                practice.author = self.user
                practice.save()
                return redirect(reverse('practice:list'))
            else:
                return render(self, 'practice/create.html', {'form': form})
        return render(self, 'practice/create.html', {'form': form})



