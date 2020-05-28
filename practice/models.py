from django.db import models

from team.models import Team
from user.models import User

class Practice(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    text = models.CharField(max_length=600)
    game = models.CharField(max_length=50)
    tier = models.IntegerField(default=1000)
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    practice_time = models.DateTimeField('practice time')

    def __str__(self):
        return '[{}] {}'.format(self.id, self.title)

    @staticmethod
    def total_practice():
        return Practice.objects.count()

class PracticeParticipate(models.Model):
    practice = models.ForeignKey(Practice, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return '[{}] {}-{}'.format(self.id, self.practice, self.user)

class Comment(models.Model):
    practice = models.ForeignKey(Practice, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    create_date = models.DateTimeField(auto_now_add=True)
    modify_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} : {}'.format(self.author, self.content)
