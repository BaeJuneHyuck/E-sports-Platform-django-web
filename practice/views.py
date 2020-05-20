from django.http import HttpResponse
from django.urls import reverse
from django.views import generic
from django.utils import timezone


from user.models import User
from django.shortcuts import redirect, render, get_object_or_404
from .forms import PracticeCreateForm, CommentForm
from practice.models import Practice, Comment
from django.conf import settings


class IndexView(generic.ListView):
    template_name = 'practice/index.html'
    context_object_name = 'latest_practice_list'
    paginate_by = 10

    def get_queryset(self):
        return Practice.objects.filter(pub_date__lte=timezone.now()).order_by('-pub_date')[:5]

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['practices'] = Practice.objects.all()
        return context

class DetailView(generic.DetailView):
    model = Practice
    template_name = 'practice/detail.html'

    def comment(self, pk):
        practice = Practice.objects.get(pk=pk)
        comments = Comment.objects.filter(practice=practice)
        total_practice = Practice.total_practice()
        today = timezone.now().strftime("%Y-%m-%d")
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

        return render(self, 'practice/detail.html', {'practice':practice, 'comments':comments, 'form':form,
                                                     'total_practice':total_practice, 'today':today})

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

        if self.method == 'POST':
            form = PracticeCreateForm(self.POST)
            if form.is_valid():
                practice = form.save(commit=False)
                practice.author = self.user
                practice.save()
                return redirect(reverse('practice:index'))
            else:
                return HttpResponse('fail')
        else:
            form = PracticeCreateForm()
        return render(self, 'practice/create.html', {'form': form})



