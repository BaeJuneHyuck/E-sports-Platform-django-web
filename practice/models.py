from django.db import models
from user.models import User


class Practice(models.Model):
    title = models.CharField(max_length=200)
    text = models.CharField(max_length=600)
    game = models.CharField(max_length=50)
    tier = models.IntegerField(default=1000)
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    practice_time = models.DateTimeField('practice time', auto_now_add=True)
    author = models.ForeignKey(User, on_delete = models.CASCADE)

    def __str__(self):
        return '[{}] {}'.format(self.id, self.title)

class PracticeParticipate(models.Model):
    practice = models.ForeignKey(Practice, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return '[{}] {}-{}'.format(self.id, self.practice, self.user)