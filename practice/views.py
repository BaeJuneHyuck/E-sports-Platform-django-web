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
    model = Practice
    template_name = 'practice/index.html'
    context_object_name = 'practices'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
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

        form = PracticeCreateForm(self.POST)
        if self.method == 'POST':
            form = PracticeCreateForm(self.POST)
            if form.is_valid():
                practice = form.save(commit=False)
                practice.author = self.user
                practice.save()
                return redirect(reverse('practice:index'))
            else:
                return render(self, 'practice/create.html', {'form': form})
            form = PracticeCreateForm()
        return render(self, 'practice/create.html', {'form': form})



