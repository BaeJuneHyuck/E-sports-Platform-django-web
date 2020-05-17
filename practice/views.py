from django.http import HttpResponse
from django.urls import reverse
from django.views import generic
from django.utils import timezone

from user.models import User
from django.shortcuts import redirect, render, get_object_or_404
from .forms import PracticeCreateForm
from practice.models import Practice
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

    def paging(self):
        total_page = Practice.objects.all()/10

class DetailView(generic.DetailView):
    model = Practice
    template_name = 'practice/detail.html'

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Practice.objects.all()

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['total_practice'] = Practice.total_practice()
        return context

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


