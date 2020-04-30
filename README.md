# 2020_Applied_Design_Lab_team6
PNU 2020 Applied Design and Lab. team 6 



프로젝트 설정법
 1. cmd에서 최상위 디렉터리로 이동
 2. python manage.py makemigrations 으로 테이블 만들기(테이블 없음 오류나면 명령어 뒤에 테이블 이름넣어서 각각 만들어보세요)
 3. python manage.py migrate로 마이그레이션 실행
 4. python manage.py createsuperuser로 관리자 계정 생성
 5. python manage.py runserver로 실행
 6. localhost:8000/admin 들어가서 관리자계정으로 접속, 테이블 확인
 

추가 db파일(db.sqlite3)은 제외하고 commit, push하기
