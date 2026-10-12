# 한채

한 사람이 한 채의 집을 짓고, 그 안에 기록을 쌓고, 이웃의 집을 찾아가는 블로그 서비스.

| 폴더 · 파일 | 내용 |
| --- | --- |
| `*.html` · `css/` · `js/` · `assets/` | 화면 (디자인 시스템 「한채」) |
| `backend/` | Django API ([backend/README.md](backend/README.md)) |
| `Dockerfile` · `docker-compose.yml` | 배포 이미지, 노트북에서 띄워 보기 |
| `deploy/` · `.github/workflows/deploy.yml` | 학교 서버 배포 ([deploy/README.md](deploy/README.md)) |
| `docs/` | 기능명세서, API 명세서 |

## 노트북에서 Docker 로 띄워 보기

Docker Desktop 을 켠 뒤 저장소 루트에서:

```bash
docker compose up --build       # http://localhost:8000
```

- 학교 서버와 같은 배포 이미지 · 운영 설정(`DEBUG=0`) · MySQL 8.0.41 로 뜬다. DB 는 빈 상태에서 시작해 `migrate` 가 테이블을 만든다.
- 가입하면 인증 메일이 실제로 가지 않고 로그에 찍힌다. 링크 찾기: `docker compose logs app | grep verify-email`
- 끄기 `docker compose down` (DB · 사진은 남는다), 처음부터 다시 `docker compose down -v`

## 개발 서버로 띄우기

코드를 고치면서 바로 보려면 Docker 없이 Django 개발 서버를 쓴다. 준비는 [backend/README.md](backend/README.md).

```bash
cd backend && .venv/bin/python manage.py runserver   # http://127.0.0.1:8000
```
