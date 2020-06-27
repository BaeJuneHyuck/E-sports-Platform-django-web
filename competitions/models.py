from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from imagekit.models import ImageSpecField
from pilkit.processors import ResizeToFill, Adjust
from django.core.validators import MinValueValidator, MaxValueValidator
from team.models import Team
from user.models import User

NOW = datetime.now() + relativedelta(seconds=1)
one_years = NOW + relativedelta(years=-1)
two_years = NOW + relativedelta(years=-2)
three_years = NOW + relativedelta(years=-3)

STATE = [
    ('ONGOING', 'Ongoing'),
    ('CURRENT_PAST', 'Current_past'),
    ('LAST_PAST', 'Last_past'),
    ('LAST_LAST_PAST', 'Last_last_past'),
    ('SCHEDULED', 'Scheduled'),
    ('PAST', 'Past')
]

GAME = [
    ('Overwatch', 'Overwatch'),
    ('LOL', 'LOL'),
]

TOURNAMENT_TYPE = [
    ('Single Elimination', 'Single Elimination'),   # 1패 하면 탈락하는 토너먼트
    ('Double Elimination', 'Double Elimination'),   # 패배시 패자전에서 한번더 기회있는 토너먼트
    ('Round Robin', 'Round Robin'),                 # 모든 상대팀과 N번 경기를 치룬다
]


class Competition(models.Model):
    competition_text = models.CharField(max_length=100)
    competition_name = models.CharField(max_length=600)
    competition_game = models.CharField(max_length=50)
    origin_image = models.ImageField(upload_to="competition/images", blank=True)
    formatted_image = ImageSpecField([Adjust(contrast=1.2, sharpness=1.1), ResizeToFill(1200, 600)],
                                     source='origin_image', format='JPEG', options={'quality': 100})
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    edit_date = models.DateTimeField('date edited', auto_now=True)
    date_start = models.DateTimeField('date_start')
    date_end = models.DateTimeField('date_end')
    attend_start = models.DateTimeField('attend_start')
    attend_end = models.DateTimeField('attend_end')
    state = models.CharField(max_length=50, choices=STATE, default='none')
    page_num = models.IntegerField(default=0)

    master = models.ForeignKey(User, null=True, on_delete=models.CASCADE,verbose_name='대회관리자') # 작성자
    is_public = models.BooleanField(default=True, verbose_name='공개 대회')
    tournament_type = models.IntegerField(default=-1, verbose_name='대회 방식') # -1=싱글, -2=더블 / 양수 1이상=라운드로빈(모든팀이 서로 값만큼 경기)
    required_tier = models.CharField(max_length=200, verbose_name='참가 최소 티어')
    total_teams = models.IntegerField(default=8, verbose_name='전체 모집 팀', validators=[MinValueValidator(2),
                                       MaxValueValidator(128)]) # 대회 참가팀수, 마감시 모집종료
    current_teams = models.IntegerField(default=0, verbose_name='현재 모집 팀') # 대회 참가팀수, 마감시 모집종료
    rounds = models.IntegerField(default=7, verbose_name='전체 라운드수',null=True,
                                 validators=[MinValueValidator(1),MaxValueValidator(8)])
    # 전체 라운드수는  single elimination 에서 2인대회 일때 1로 최소 ,128인대회일때 7로 최대)
    # dobule이면 패자전이 각각 진행되므로 1라운드 추가
                                                
    def __str__(self):
        return '{}'.format(self.competition_name)

    @staticmethod
    def total_competition():
        return Competition.objects.count()

    def get_image_url(self):
        return '%s%s' %(settings.MEDIA_URL, self.formatted_image)

    def delete(self, *args, **kwargs):
        self.origin_image.delete()
        self.formatted_image.delete()
        super(Competition, self).delete(*args, **kwargs)

    def can_attend(self):
        return self.attend_start.strftime('%Y-%m-%d') <= NOW.strftime('%Y-%m-%d') \
               and  self.attend_end.strftime('%Y-%m-%d') >= NOW.strftime('%Y-%m-%d')

@receiver(pre_save, sender=Competition)
def competition_save_state(sender, instance, update_fields, **kwargs):
    if instance.date_start.strftime('%Y-%m-%d') > NOW.strftime('%Y-%m-%d'):
        instance.state = 'SCHEDULED'
    elif instance.date_end.strftime('%Y-%m-%d') < NOW.strftime('%Y-%m-%d'):
        instance.state = 'CURRENT_PAST'
    elif instance.date_end.strftime('%Y-%m-%d') < NOW.strftime('%Y-%m-%d'):
        instance.state = 'LAST_PAST'
    elif instance.date_end.strftime('%Y-%m-%d') < NOW.strftime('%Y-%m-%d'):
        instance.state = 'LAST_LAST_PAST'
    else:
        instance.state = 'ONGOING'

@receiver(pre_save, sender=Competition)
def practice_save(sender, instance, update_fields, **kwargs):
    instance.master_name = instance.master.name

class CompetitionParticipate(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    team_number = models.IntegerField(default=-1)   # 대회에서 몇번 팀인가 -> 대진표에 사용, 랜덤으로 유니크 배정
    avg_tier = models.IntegerField(default=0, null=True)
    win = models.IntegerField(default=0)   # 승
    lose = models.IntegerField(default=0)   # 패

    def __str__(self):
        return '{}-{}'.format(self.competition, self.team)

class Match(models.Model):
    game = models.CharField(max_length=50)
    competition = models.ForeignKey(Competition, null=True, on_delete=models.CASCADE)  # 어느 대회의 경기인가
    number = models.IntegerField(default=1, verbose_name='경기 번호') # pk 아님, 각 대회에서 몇번째경기인가, 대진표그리는데 사용
    round = models.IntegerField(default=1, verbose_name='라운드')

    team1 = models.ForeignKey(Team, null=True, on_delete=models.CASCADE, related_name='team1')
    team2 = models.ForeignKey(Team, null=True, on_delete=models.CASCADE, related_name='team2')
    date = models.DateTimeField('경기일시', editable=True, null=True,)
    result = models.IntegerField(default=0, verbose_name='경기 결과') # (-1 부전승, 0 경기전, 1 1팀승리, 2 2팀승리 , 3 무승부)

    result_lol = models.ForeignKey('ResultLOL',blank=True, null=True, on_delete=models.CASCADE)
    result_ow = models.ForeignKey('ResultOW',blank=True, null=True, on_delete=models.CASCADE)

    @staticmethod
    def total_match():
        return Match.objects.count()

# 매치 코멘트
class MatchComment(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    create_date = models.DateTimeField(auto_now_add=True)
    modify_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} : {}'.format(self.author, self.content)


#롤 경기 정보, 관리자가 수기로 입력
class ResultLOL(models.Model):
    math = models.ForeignKey(Match, null=True, on_delete=models.CASCADE)  # 어느 경기 정보인가
    ''' 킬, 데스 어시, 아이템 ... 등등 추가예정'''


#오버워치 정보, 관리자가 수기로 입력
class ResultOW(models.Model):
    math = models.ForeignKey(Match, null=True, on_delete=models.CASCADE)  # 어느 경기 정보인가
    ''' 맵, 라운드별 점수, , 영웅, 명중률... 등등 추가예정'''

# 매치 코멘트
class MatchComment(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    create_date = models.DateTimeField(auto_now_add=True)
    modify_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} : {}'.format(self.author, self.content)
