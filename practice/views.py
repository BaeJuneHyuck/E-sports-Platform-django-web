from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.http import HttpResponse
from django.urls import reverse
from django.views import generic

from django.shortcuts import redirect, render, get_object_or_404
from .forms import PracticeCreateForm, CommentForm
from team.models import TeamInvitation
from practice.models import Practice, Comment, User
from django.conf import settings

NOW = datetime.now()
one_years = NOW+relativedelta(years=-1)
two_years = NOW+relativedelta(years=-2)
three_years = NOW+relativedelta(years=-3)

class IndexView(generic.ListView):
    model = Practice
    template_name = 'practice/index.html'
    context_object_name = 'practices'
    paginate_by = 5

    def get_queryset(self, *args, **kwargs):
        qs = Practice.objects.all()
        query = self.request.GET.get("qs", None)
        attribute = self.request.GET.get("attribute", None)
        if query is not None:
            if attribute == 'title':
                qs = qs.filter(title__icontains=query)
            elif attribute == 'author':
                qs = qs.filter(author_name__icontains=query)
            elif attribute == 'tier':
                qs = qs.filter(tier=query)
            elif attribute == 'text':
                qs = qs.filter(text__icontains=query)
        print(self.request.GET)
        return qs

    def get_context_data(self, *args, **kwargs):
        context = super(IndexView, self).get_context_data(*args,**kwargs)
        context['practices'] = Practice.objects.filter(practice_time__gt=three_years)
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

        attribute = self.request.GET.get("attribute", None)
        context['attribute'] = attribute
        return context


class DetailView(generic.DetailView):
    model = Practice
    template_name = 'practice/detail.html'

    def comment(self, practice_pk):
        practice = Practice.objects.get(pk=practice_pk)
        comments = Comment.objects.filter(practice=practice)
        total_practice = Practice.total_practice()
        today = NOW.strftime("%Y-%m-%d")
        if self.method == 'POST':
            form = CommentForm(self.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.author = self.user
                comment.practice = practice
                comment.save()
            else:
                return HttpResponse('fail')
        else:
            form = CommentForm()

        form = CommentForm()
        invitations= TeamInvitation.objects.filter(invited_pk=self.user.pk).filter(checked=False)[:5]

        return render(self, 'practice/detail.html', {'practice':practice, 'comments':comments, 'form':form,
                                                     'total_practice':total_practice, 'today':today, 'invitations':invitations})

    def delete(self, practice_pk, comment_pk):
        delete_comment = Comment.objects.get(pk=comment_pk)
        delete_comment.delete()
        practice = Practice.objects.get(pk=practice_pk)
        comments = Comment.objects.filter(practice=practice)
        total_practice = Practice.total_practice()
        today = NOW.strftime("%Y-%m-%d")
        if self.method == 'POST':
            form = CommentForm(self.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.author = self.user
                comment.practice = practice
                comment.save()
            else:
                return HttpResponse('fail')
        else:
            form = CommentForm()

        form = CommentForm()
        invitations = TeamInvitation.objects.filter(invited_pk=self.user.pk).filter(checked=False)[:5]

        return render(self, 'practice/detail.html', {'practice': practice, 'comments': comments, 'form': form,
                                                     'total_practice': total_practice, 'today': today, 'invitations':invitations})


class AttendView(generic.CreateView):
    model = Practice
    template_name = 'practice/attend.html'

    def get_object(self):
        return get_object_or_404(User, pk=self.request.comment_user.id)


class CreateView(generic.CreateView):
    login_url = settings.LOGIN_URL
    model = Practice

    def post_new(self):
        if not self.user.is_authenticated:
            return redirect('%s?next=%s' % (settings.LOGIN_URL, self.path))

        invitations= TeamInvitation.objects.filter(invited_pk=self.user.pk).filter(checked=False)[:5]

        form = PracticeCreateForm(self.POST)
        if self.method == 'POST':
            form = PracticeCreateForm(self.POST)
            if form.is_valid():
                practice = form.save(commit=False)
                practice.author = self.user
                practice.save()
                return redirect(reverse('practice:index'))
            else:
                return render(self, 'practice/create.html', {'form': form, 'invitations':invitations})
        return render(self, 'practice/create.html', {'form': form, 'invitations':invitations})



