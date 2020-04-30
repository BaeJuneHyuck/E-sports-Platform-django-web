from django.views import generic
from django.utils import timezone

from .models import Practice
from practice.models import Practice


class IndexView(generic.ListView):
    template_name = 'practice/index.html'
    context_object_name = 'latest_practice_list'

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
        return Practice.objects.filter(pub_date__lte=timezone.now())

class AttendView(generic.DetailView):
    model = Practice
    template_name = 'practice/attend.html'

