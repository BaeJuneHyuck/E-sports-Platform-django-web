from datetime import datetime
import timedelta
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import sqlite3

def LoLCrawling(Container,soup):
    nickName = []
    gameId = []
    outCome = []
    gameType = []
    startTime = []
    playTime = []
    champion= []
    mainRune = []
    subRune = []
    dSpell = []
    fSpell = []
    level = []
    killratio = []
    kill = []
    death = []
    assist = []
    cs = []
    baron = []
    dragon = []
    tower = []
    damage = []
    pinkWard = []
    wardSet = []
    wardDel = []
    deadgame = []

    for i in soup.select('.GameItemWrap > div'):
        startTime.append(i.attrs['data-game-time'])
        gameId.append(i.attrs['data-game-id'])
        outCome.append(i.attrs['data-game-result'])

    for i in soup.select('.GameType'):
        gameType.append(i.text.replace('\n','').replace('\t',''))
    for i in soup.select('.GameLength'):
        a = i.text.replace('분 ', ':').replace('초', '')
        b = a.split(":")
        c = 60*int(b[0]) + int(b[1])
        playTime.append(c)
    for i in soup.select('.GameSettingInfo .ChampionName'):
        champion.append(i.text.replace('\n','').replace('\t','').replace(" ", ""))

    flg = 0
    for i in soup.select('.SummonerSpell .Spell .Image.tip'):
        if flg == 0:
            dSpell.append(i.attrs['alt'])
            flg = 1
        else:
            fSpell.append(i.attrs['alt'])
            flg = 0

    flg = 0
    for i in soup.select('.Runes .Rune .Image.tip'):
        if flg == 0:
            mainRune.append(i.attrs['alt'])
            flg = 1
        else:
            subRune.append(i.attrs['alt'])
            flg = 0

    for i in soup.select('div[class=Stats] div[class=Level]'):
        level.append(i.text.replace('\n','').replace('\t','').replace("레벨", ""))

    for i in soup.select('.Stats .CKRate.tip'):
        killratio.append(i.text.replace("킬관여 ", "").replace("\t", "").replace("\n", "").replace("%", ""))

    for i in soup.select('div[class=KDA] .KDA .Kill'):
        kill.append(i.text)
    for i in soup.select('div[class=KDA] .KDA .Death'):
        death.append(i.text)
    for i in soup.select('div[class=KDA] .KDA .Assist'):
        assist.append(i.text)

    for i in soup.select('div[class=Stats] div[class=CS]'):
        needs = i.text.split()
        cs.append(needs[0])

    cnt = 0
    for i in soup.select('div[class=ObjectScore]'):
        if cnt == 6:
            cnt = 0
        if (cnt % 6) ==0:
            baron.append(i.text.replace('\n','').replace('\t',''))
            cnt += 1
        elif (cnt % 6) ==1:
            dragon.append(i.text.replace('\n', '').replace('\t', ''))
            cnt += 1
        elif (cnt % 6) ==2:
            tower.append(i.text.replace('\n', '').replace('\t', ''))
            cnt += 1
        else:
            cnt += 1
            continue

    for i in soup.findAll("tr", {"class":{"Row first isRequester", "Row isRequester", "Row last isRequester"}}):
        name = i.find_next("a", {"class" :{"Link"}})
        dmg = i.find_next("div", {"class" :{"ChampionDamage"}})
        pWard = i.find_next("span", {"class" :{"SightWard"}})
        ward = i.find_next("div", {"class" :{"Stats"}})
        nickName.append(name.text)
        damage.append(dmg.text.replace(",",""))
        pinkWard.append(pWard.text)
        wardlist = ward.text.replace("\n", "").replace("\t","").replace(" ", "").split("/")
        wardSet.append(wardlist[0])
        wardDel.append(wardlist[1])

    # for i in soup.select('.Row.isRequester'):
    Container['nickName'] = nickName
    Container['startTime'] = startTime
    Container['gameId'] = gameId
    Container['outCome'] = outCome
    Container['gameType'] = gameType
    Container['playTime'] = playTime
    Container['champion'] = champion
    Container['dSpell'] = dSpell
    Container['fSpell'] = fSpell
    Container['mainRune'] = mainRune
    Container['subRune'] = subRune
    Container['level'] = level
    Container['killratio'] = killratio
    Container['kill'] = kill
    Container['death'] = death
    Container['assist'] = assist
    Container['cs'] =cs
    Container['baron'] = baron
    Container['dragon'] = dragon
    Container['tower'] = tower
    Container['damage'] = damage
    Container['pinkward'] = pinkWard
    Container['wardSet'] = wardSet
    Container['wardDel'] = wardDel


    for i in range(len(Container['playTime'])):
        if Container['playTime'][i] < 600:
            deadgame.append(i)

    for i in range(len(deadgame)):
        baron.insert(i, 0)
        dragon.insert(i, 0)
        tower.insert(i, 0)

    return Container

def parseOPGG(Name):
    Container = {}

    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")

    driver = webdriver.Chrome(options = options)
    url = 'https://www.op.gg/summoner/userName=' + Name
    driver.get(url)

    try:
        start = time.time()
        chooseSoleRank(driver)
        clickbuttonloop(driver)
        openStats(driver)
        time.sleep(5)

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
    except Exception as drivererr:
        print("errer Exception:", drivererr)
        driver.quit()
        return 1
    try:
        LoLCrawling(Container, soup)

    except Exception as noSummonr:
        print("errer Exception:", noSummonr)
        print("존재하지 않는 소환사입니다.")
        driver.quit()
        return 2

    driver.quit()
    return Container

def chooseSoleRank(driver):
    driver.find_element_by_id('right_gametype_soloranked').click()
    time.sleep(3)

def openStats(driver):
    details = driver.find_elements_by_xpath("//span[contains(@class,'__spSite __spSite-194 Off')]")
    for i in details:
        driver.execute_script("arguments[0].click();", i)

    details = driver.find_elements_by_xpath("//span[contains(@class,'__spSite __spSite-196 Off')]")
    for i in details:
        driver.execute_script("arguments[0].click();", i)

    details = driver.find_elements_by_xpath("//span[contains(@class,'__spSite __spSite-198 Off')]")
    for i in details:
        driver.execute_script("arguments[0].click();", i)

def clickbuttonloop(driver):
    for i in range(1):
        try:
            driver.find_element_by_class_name('GameMoreButton.Box').click()
            time.sleep(2)
        except Exception as error:
            return

if __name__ == "__main__":
    Name = input("검색을 원하는 닉네임을 입력해 주세요.\n")

    Dic = parseOPGG(Name)
    if(Dic == 1):
        print("error_driver")
        exit(0)
    elif(Dic == 2):
        print("error_no_user")
        exit(0)

    db = sqlite3.connect('db.sqlite3')


    df = pd.DataFrame(Dic)
    df.to_sql('user_lol_record', db, if_exists='append', index = False)