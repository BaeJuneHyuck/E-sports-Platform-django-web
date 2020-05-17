from django.db import models


class Competition(models.Model):
    competition_text = models.CharField(max_length=100)
    competition_name = models.CharField(max_length=600)
    competition_game = models.CharField(max_length=50)
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    date_start = models.DateTimeField('date_start')
    date_end = models.DateTimeField('date_end')
    attend_start = models.DateTimeField('attend_start')
    attend_end = models.DateTimeField('attend_end')

    @staticmethod
    def total_Competition():
        return Competition.objects.count()

class CompetitionParticipate(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE)
    team = models.CharField(max_length=100)
    avg_tier = models.IntegerField()
