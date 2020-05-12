from django.http import request, HttpResponseRedirect, HttpResponse
from django.views import generic
from django.utils import timezone

from .models import Practice
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

class DetailView(generic.DetailView):
    model = Practice
    template_name = 'practice/detail.html'

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Practice.objects.all()

class AttendView(generic.CreateView):
    model = Practice
    template_name = 'practice/attend.html'

    def get_object(self):
        return get_object_or_404(User, pk=self.request.user.id)


class CreateView(generic.CreateView):
    login_url = settings.LOGIN_URL
    model = Practice
    pk_url_kwarg = 'id'

    def post_new(request):
        if request.method == 'POST':
            form = PracticeCreateForm(request.POST)
            if form.is_valid():
                practice = form.save(commit=False)
                practice.author_id = request.user.id
                practice.save()
                return render(request, "practice/index.html")
            else:
                return HttpResponse('fail')
        else:
            form = PracticeCreateForm()
        return render(request, 'practice/create.html', {'form': form})
