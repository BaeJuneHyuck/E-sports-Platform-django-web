from django.db import models
from django.http import request
from bs4 import BeautifulSoup

# Create your models here.
class OW_BattleTag(models.Model):
    user_key = models.CharField(max_length=50)
    battle_tag = models.CharField(max_length=50)
    data = models.TextField()

    def get_data(self):
        point = self.battle_tag.find('#')
        name = self.battle_tag[:point]
        code = self.battle_tag[point+1:]
        URL = f'https://ow-api.com/v1/stats/pc/asia/{name}-{code}/complete'
        self.data = requests.get(URL).text
        self.save()
