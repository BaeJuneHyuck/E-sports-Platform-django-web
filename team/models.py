from django.db import models
from user.models import User

class Team(models.Model):
    """
    공개된 팀의 경우 - 유저가 검색해서 가입하면 자동가입 + 팀원 초대기능 으로 초대 가능
    비공개된경우 초대기능을 통해서만 가입가능
    팀장은 visible 설정을통해 게시판 노출 여부를 설정가능
    """
    name = models.CharField(max_length=200,verbose_name='팀명' )
    master = models.ForeignKey(User, on_delete=models.CASCADE,verbose_name='팀장')
    game = models.CharField(max_length=600)
    text = models.CharField(max_length=600)
    visible = models.BooleanField(default=True, verbose_name='공개팀')
    def __str__(self):
        return '{}'.format(self.name)


class TeamInvitation(models.Model):
    """
    초대정보, 팀원이 팀원이 아닌 유저를 초대가능
    팀정보, 초대한사람pk, 초대받은사람pk 정보를 가지고잇고
    초대받은 사람이 거절하면 초대는 DB에서 삭제하고 끝
    초대받은 사람이 승인하면 초대는 DB에서 삭제하고 TeamRelation에 유저 추가
    즉 DB에 이 정보가 있으면 아직 초대 결과가 정해지지 않은것으로 간주하고 유저에게 보여준다
    """
    team_pk = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name='팀' )
    inviter_pk = models.ForeignKey(User, on_delete=models.CASCADE,verbose_name='초대한 유저',  related_name='inviter')
    invited_pk = models.ForeignKey(User, on_delete=models.CASCADE,verbose_name='초대받은 유저',  related_name='target')
    
    def __str__(self):
        return '[{}] 팀의 {}가 {}를 초대'.format(self.team_pk, self.inviter_pk, self.invited_pk)

class TeamRelation(models.Model):
    team_pk = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name='팀' )
    user_pk = models.ForeignKey(User, on_delete=models.CASCADE,verbose_name='팀원')

    def __str__(self):
        return '[{}] {}'.format(self.team_pk, self.user_pk)
