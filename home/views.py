from django.db.models import Q
from django.views import generic
from django.utils import timezone

from competitions.models import Competition
from practice.models import Practice, Comment
from team.models import TeamInvitation


class IndexView(generic.ListView):
    template_name = 'home/index.html'
    context_object_name = 'latest_competitions_list'

    def get_queryset(self):
        return Competition.objects.filter(pub_date__lte=timezone.now()).order_by('-pub_date')[:5]

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['practices'] = Practice.objects.all().order_by('-pub_date')[:5]
        context['latest_competitions'] = Competition.objects.filter(date_end__gt=timezone.now()).order_by('-pub_date')[:5]
        context['possible_attend_competitions'] = Competition.objects.filter(Q(attend_start__lt=timezone.now()) & Q(attend_end__gt=timezone.now())).order_by('-pub_date')[:5]
        context['invitations']= TeamInvitation.objects.filter(invited_pk=self.request.user.pk).filter(checked=False)[:5]
        context['scheduled_competition'] = Competition.objects.filter(date_start__gt=timezone.now()).order_by('-pub_date')[:5]

        if self.request.user.is_authenticated:
            comments = Comment.objects.filter(Q(author=self.request.user) & Q(content__contains="참가신청합니다"))\
                .values_list('practice', flat=True).distinct()
            attend_practice = Practice.objects.filter(pk__in=comments)[:5]
            context['attend_practice'] = attend_practice
        return context
