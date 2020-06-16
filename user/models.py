from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
import django.db.models.manager 
import requests
import json

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.is_active = True;
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField('email', unique=True)
    name = models.CharField('이름', max_length=30, blank=True)
    is_staff = models.BooleanField('스태프 권한', default=False)
    is_active = models.BooleanField('사용중', default=False)
    date_joined = models.DateTimeField('가입일', default=timezone.now)

    lolid = models.CharField(blank=True, max_length=30, verbose_name='LOL 계정 이름')
    overwid = models.CharField(blank=True, max_length=30, verbose_name='오버워치 계정 이름')
    usage_agree = models.BooleanField(default=False, verbose_name='정보 제공 동의')
    message = models.CharField('인사말', max_length=300, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'  # email을 사용자의 식별자로 설정
    REQUIRED_FIELDS = ['name']  # 필수입력값

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        swappable = 'AUTH_USER_MODEL'

    def email_user(self, subject, message, from_email=None, **kwargs):  # 이메일 발송 메소드
        send_mail(subject, message, from_email, [self.email], **kwargs)

class lol_record(models.Model):
    nickName = models.CharField('nickName', max_length=20)
    gameId = models.IntegerField('gameId', unique=True, primary_key=True)
    outCome = models.CharField('outCome', max_length=5)
    gameType = models.CharField('gameType',max_length=5)
    startTime = models.IntegerField('startTime')
    playTime = models.IntegerField('playTime')
    champion = models.CharField('champion', max_length=20)
    mainRune = models.CharField('mainRune', max_length=10)
    subRune = models.CharField('subRune', max_length=5)
    dSpell = models.CharField('dSpell', max_length=10)
    fSpell = models.CharField('fSpell',max_length=5)
    level = models.IntegerField('level')
    killratio = models.IntegerField('killratio')
    kill = models.IntegerField('Kill')
    death = models.IntegerField('death')
    assist = models.IntegerField('assist')
    cs = models.IntegerField('cs')
    baron = models.IntegerField('baron')
    dragon = models.IntegerField('dragon')
    tower = models.IntegerField('tower')
    damage = models.IntegerField('damage')
    pinkWard = models.IntegerField('pinkWart')
    wardSet = models.IntegerField('wardSet')
    wardDel = models.IntegerField('wardDel') 
    
    def __str__(self):
        return '{}_{}'.format(self.nickName, self.gameId)



class OW_BattleTag(models.Model):
    user_key = models.CharField(max_length=50)
    battle_tag = models.CharField(max_length=50, unique=True)
    data = models.TextField()
    tank_level = models.CharField(max_length=10)
    tank_icon = models.TextField()
    tank_rank = models.TextField()
    damage_level = models.CharField(max_length=10)
    damage_icon = models.TextField()
    damage_rank = models.TextField()
    support_level = models.CharField(max_length=10)
    support_icon = models.TextField()
    support_rank = models.TextField()
    top1_character = models.CharField(max_length=20)
    top1_timePlayed = models.CharField(max_length=10)
    top1_gamesWon = models.IntegerField(null=True)
    top1_winPercentage = models.IntegerField(null=True)
    top1_weaponAccuracy = models.IntegerField(null=True)
    top1_eliminationsPerLife = models.IntegerField(null=True)
    top1_multiKillBest = models.IntegerField(null=True)
    top1_objectiveKills = models.IntegerField(null=True)
    top2_character = models.CharField(max_length=20)
    top2_timePlayed = models.CharField(max_length=10)
    top2_gamesWon = models.IntegerField(null=True)
    top2_winPercentage = models.IntegerField(null=True)
    top2_weaponAccuracy = models.IntegerField(null=True)
    top2_eliminationsPerLife = models.IntegerField(null=True)
    top2_multiKillBest = models.IntegerField(null=True)
    top2_objectiveKills = models.IntegerField(null=True)
    top3_character = models.CharField(max_length=20)
    top3_timePlayed = models.CharField(max_length=10)
    top3_gamesWon = models.IntegerField(null=True)
    top3_winPercentage = models.IntegerField(null=True)
    top3_weaponAccuracy = models.IntegerField(null=True)
    top3_eliminationsPerLife = models.IntegerField(null=True)
    top3_multiKillBest = models.IntegerField(null=True)
    top3_objectiveKills = models.IntegerField(null=True)

    def get_data(self):
        point = self.battle_tag.find('#')
        name = self.battle_tag[:point]
        code = self.battle_tag[point+1:]
        URL = f'https://ow-api.com/v1/stats/pc/asia/{name}-{code}/complete'
        data = requests.get(URL)
        self.data = data.text
        json_data = data.json()
        self.tank_level = json_data['ratings'][0]['level']
        self.tank_icon = json_data['ratings'][0]['roleIcon']
        self.tank_rank = json_data['ratings'][0]['rankIcon']
        self.damage_level  = json_data['ratings'][1]['level']
        self.damage_icon = json_data['ratings'][1]['roleIcon']
        self.damage_rank = json_data['ratings'][1]['rankIcon']
        self.support_level = json_data['ratings'][2]['level']
        self.support_icon = json_data['ratings'][2]['roleIcon']
        self.support_rank = json_data['ratings'][2]['rankIcon']
        top_heroes = json_data['competitiveStats']['topHeroes']
        for hero, time in top_heroes.items():
            time['timePlayed'] = int(time['timePlayed'].replace(":", ""))
        top_heroes = sorted(top_heroes.items(), key=lambda x: x[1]['timePlayed'], reverse=True)
        self.top1_character = top_heroes[0][0]
        self.top1_timePlayed = json_data['competitiveStats']['topHeroes'][self.top1_character]['timePlayed']
        self.top1_gamesWon = json_data['competitiveStats']['topHeroes'][self.top1_character]['gamesWon']
        self.top1_winPercentage = json_data['competitiveStats']['topHeroes'][self.top1_character]['winPercentage']
        self.top1_weaponAccuracy = json_data['competitiveStats']['topHeroes'][self.top1_character]['weaponAccuracy']
        self.top1_eliminationsPerLife = json_data['competitiveStats']['topHeroes'][self.top1_character]['eliminationsPerLife']
        self.top1_multiKillBest = json_data['competitiveStats']['topHeroes'][self.top1_character]['multiKillBest']
        self.top1_objectiveKills = json_data['competitiveStats']['topHeroes'][self.top1_character]['objectiveKills']
        self.top2_character = top_heroes[1][0]
        self.top2_timePlayed = json_data['competitiveStats']['topHeroes'][self.top2_character]['timePlayed']
        self.top2_gamesWon = json_data['competitiveStats']['topHeroes'][self.top2_character]['gamesWon']
        self.top2_winPercentage = json_data['competitiveStats']['topHeroes'][self.top2_character]['winPercentage']
        self.top2_weaponAccuracy = json_data['competitiveStats']['topHeroes'][self.top2_character]['weaponAccuracy']
        self.top2_eliminationsPerLife = json_data['competitiveStats']['topHeroes'][self.top2_character]['eliminationsPerLife']
        self.top2_multiKillBest = json_data['competitiveStats']['topHeroes'][self.top2_character]['multiKillBest']
        self.top2_objectiveKills = json_data['competitiveStats']['topHeroes'][self.top2_character]['objectiveKills']
        self.top3_character = top_heroes[2][0]
        self.top3_timePlayed = json_data['competitiveStats']['topHeroes'][self.top3_character]['timePlayed']
        self.top3_gamesWon = json_data['competitiveStats']['topHeroes'][self.top3_character]['gamesWon']
        self.top3_winPercentage = json_data['competitiveStats']['topHeroes'][self.top3_character]['winPercentage']
        self.top3_weaponAccuracy = json_data['competitiveStats']['topHeroes'][self.top3_character]['weaponAccuracy']
        self.top3_eliminationsPerLife = json_data['competitiveStats']['topHeroes'][self.top3_character]['eliminationsPerLife']
        self.top3_multiKillBest = json_data['competitiveStats']['topHeroes'][self.top3_character]['multiKillBest']
        self.top3_objectiveKills = json_data['competitiveStats']['topHeroes'][self.top3_character]['objectiveKills']
        self.save()