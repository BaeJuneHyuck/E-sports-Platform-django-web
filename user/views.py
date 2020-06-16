from django.views.generic import CreateView, DetailView, ListView

from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from user.forms import UserRegistrationForm, LoginForm, UserMypageForm
from django.contrib import messages
from django.views.generic.base import TemplateView
from django.views.generic.edit import UpdateView
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect

# email 발송
from django.contrib.auth.tokens import default_token_generator
from esportsPlatform import settings
from django.views.generic import CreateView, FormView
from .mixins import VerifyEmailMixin
from .forms import VerificationEmailForm
from team.models import TeamInvitation
# mongodb
import pymongo

from .models import OW_BattleTag
import json


class UserRegistrationView(VerifyEmailMixin, CreateView):
    template_name = 'user/user_model.html'
    model = get_user_model()
    form_class = UserRegistrationForm
    success_url = '/user/login/'
    verify_url = '/user/verify/'

    def form_valid(self, form):
        response = super().form_valid(form)
        if form.instance:
            self.send_verification_email(form.instance)
        return response


class UserLoginView(LoginView):
    authentication_form = LoginForm
    template_name = 'user/login_form.html'

    def form_invalid(self, form):
        messages.error(self.request, '로그인에 실패하였습니다.', extra_tags='danger')
        return super().form_invalid(form)


class UserMypageView(UpdateView):
    model = get_user_model()
    template_name = 'user/mypage.html'
    form_class= UserMypageForm

    def get(self, request):
        form = UserMypageForm(instance=request.user)
        invitations= TeamInvitation.objects.filter(invited_pk=request.user.pk).filter(checked=False)[:5]

        args = {'form': form, 'invitations':invitations}
        return render(request, self.template_name, args)

    def post(self, request):
        form = UserMypageForm(request.POST, instance=request.user)
        invitations= TeamInvitation.objects.filter(invited_pk=request.user.pk).filter(checked=False)[:5]
        if form.is_valid():
            form.save()
            return redirect('/user/mypage/')

        args = {'form': form,  'invitations':invitations}
        return render(request, self.template_name, args)

class UserMypageOWView(UpdateView):
    model = get_user_model()
    template_name = 'user/mypage_OW.html'

    def get(self, request):
        data = OW_BattleTag.objects.filter(battle_tag=request.user.overwid)
        if data.count() == 0:
            OW_BattleTag.objects.create(battle_tag=request.user.overwid)
        obj = OW_BattleTag.objects.get(battle_tag=request.user.overwid)
        obj.get_data()
        data = OW_BattleTag.objects.filter(battle_tag=request.user.overwid)
        json_data = json.loads(obj.data)
        top_heroes = json_data['competitiveStats']['topHeroes']
        for hero, time in top_heroes.items():
            t = int(time['timePlayed'].replace(":", ""))
            time['timePlayed'] = ((t//10000)*60) + (t//100)%100
        top_heroes = sorted(top_heroes.items(), key=lambda x: x[1]['timePlayed'], reverse=True)
        args = {'data': data, 'top_heroes': top_heroes}
        return render(request, self.template_name, args)


class UserlolpageView(ListView):
    model = get_user_model()
    template_name = 'user/leagueoflegends.html'

    def get(self, request, *args, **kwargs):
        username = 'team6'
        password = 'TEAM6'
        client = pymongo.MongoClient('mongodb://%s:%s@ec2-52-78-106-39.ap-northeast-2.compute.amazonaws.com:27017/lol' % (username, password))

        db = client.lol
        loldb = db.lol

        cur_user = request.user
        lolid = self.model.objects.get(email=cur_user.email)
        records = loldb.find({"nickName" : lolid.lolid})
        jsonToDic = []
        for record in records:
            del (record['_id'])
            jsonToDic.append(record)
        sortedDic = sorted(jsonToDic, key=lambda jsonToDic: (jsonToDic['startTime']),reverse=True)
        avg = self.getavg(sortedDic)
        win = self.winGmae(sortedDic)
        lose = self.loseGmae(sortedDic)
        args = {'records':sortedDic, 'avg' : avg, 'win' : win, 'lose' : lose}
        client.close()
        return render(request, self.template_name, args)

    def getavg(self, jsonToDic):
        Container = dict()
        gamenum = len(jsonToDic)
        killsum = 0
        deathsum = 0
        asssum = 0
        pwardsum = 0
        ratiosum = 0
        wardsum = 0
        cssum = 0
        timesum = 0
        dmgsum = 0
        for lol in jsonToDic:
            killsum += int(lol['kill'])
            deathsum += int(lol['death'])
            asssum += int(lol['assist'])
            pwardsum += int(lol['pinkward'])
            ratiosum += int(lol['killratio'])
            wardsum += int(lol['wardSet']) + int(lol['wardDel'])
            cssum += int(lol['cs'])
            timesum += int(lol['playTime'])
            dmgsum += int(lol['damage'])

        avgcs = cssum / gamenum
        avgTime = timesum / 60 / gamenum
        Container['latestrank'] = jsonToDic[0]['rank']

        Container['avgKill'] = killsum / gamenum
        Container['svhDeath'] = deathsum / gamenum
        Container['avgAssist'] = asssum / gamenum
        Container['avgRatio'] = ratiosum / gamenum
        Container['avgPward'] = pwardsum / gamenum
        Container['avgWard'] = wardsum / gamenum
        Container['avgCs'] = avgcs
        Container['csPerMin'] = avgcs / avgTime
        Container['avgdmg'] = dmgsum / gamenum

        return Container

    def winGmae(self, jsonToDic):
        maxcnt = 10
        winrecord = []
        for lol in jsonToDic:
            if lol['outCome'] =='win':
                winrecord.append(lol)
                maxcnt -=1
                if maxcnt == 0:
                    break;
        return winrecord

    def loseGmae(self, jsonToDic):
        maxcnt = 10
        loserecord = []
        for lol in jsonToDic:
            if lol['outCome'] =='lose':
                loserecord.append(lol)
                maxcnt -=1
                if maxcnt == 0:
                    break;

        return loserecord


class UserVerificationView(TemplateView):

    model = get_user_model()
    redirect_url = '/user/login/'
    token_generator = default_token_generator

    def get(self, request, *args, **kwargs):
        if self.is_valid_token(**kwargs):
            messages.info(request, '인증이 완료되었습니다.')
        else:
            messages.error(request, '인증이 실패되었습니다.')
        return HttpResponseRedirect(self.redirect_url)   # 인증 성공여부와 상관없이 무조건 로그인 페이지로 이동

    def is_valid_token(self, **kwargs):
        pk = kwargs.get('pk')
        token = kwargs.get('token')
        user = self.model.objects.get(pk=pk)
        is_valid = self.token_generator.check_token(user, token)
        if is_valid:
            user.is_active = True
            user.save()     # 데이터가 변경되면 반드시 save() 메소드 호출
        return is_valid


class ResendVerifyEmailView(VerifyEmailMixin, FormView):
    model = get_user_model()
    form_class = VerificationEmailForm
    success_url = '/user/login/'
    template_name = 'user/resend_verify_email.html'

    def form_valid(self, form):
        email = form.cleaned_data['email']
        try:
            user = self.model.objects.get(email=email)
        except self.model.DoesNotExist:
            messages.error(self.request, '알 수 없는 사용자 입니다.')
        else:
            self.send_verification_email(user)
        return super().form_valid(form)

