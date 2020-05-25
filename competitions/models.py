from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from team.models import Team

NOW = timezone.now()

STATE = [
    ('ONGOING', 'Ongoing'),
    ('PAST', 'Past'),
    ('SCHEDULED', 'Scheduled'),
]

GAME = [
    ('Overwatch', 'Overwatch'),
    ('LOL', 'LOL'),
]

class Competition(models.Model):
    competition_text = models.CharField(max_length=100)
    competition_name = models.CharField(max_length=600)
    competition_game = models.CharField(max_length=50)
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    date_start = models.DateTimeField('date_start')
    date_end = models.DateTimeField('date_end')
    attend_start = models.DateTimeField('attend_start')
    attend_end = models.DateTimeField('attend_end')
    state = models.CharField(max_length=10, choices=STATE, default='none')

    @staticmethod
    def total_competition():
        return Competition.objects.count()

@receiver(pre_save, sender=Competition)
def competition_save(sender, instance, update_fields, **kwargs):
    if instance.date_start > NOW:
        instance.state = 'SCHEDULED'
    elif instance.date_end < NOW:
        instance.state = 'PAST'
    else:
        instance.state = 'ONGOING'

class CompetitionParticipate(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    avg_tier = models.IntegerField()

