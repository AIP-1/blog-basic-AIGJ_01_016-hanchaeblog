#!/usr/bin/env bash
# 서버에서 실행된다 (GitHub Actions 가 SSH 로 부른다).
# ~/hanchae 에 놓인 이미지 파일을 불러와, 예전 컨테이너를 내리고 새 컨테이너를 띄운다.
set -euo pipefail

APP_DIR="$HOME/hanchae"
NAME="hanchae-backend"
cd "$APP_DIR"
chmod 600 hanchae.env

APP_PORT="$(grep '^APP_PORT=' hanchae.env | cut -d= -f2-)"
if [ -z "$APP_PORT" ]; then
  echo "APP_PORT 가 비어 있어요. GitHub Secrets 의 APP_PORT 를 확인하세요." >&2
  exit 1
fi

echo "[1/4] 이미지 불러오기"
gunzip -c hanchae-backend.tar.gz | docker load

echo "[2/4] 예전 컨테이너 내리기"
docker rm -f "$NAME" >/dev/null 2>&1 || true

echo "[3/4] 새 컨테이너 띄우기 (포트 $APP_PORT → 8000)"
mkdir -p "$APP_DIR/media"
docker run -d \
  --name "$NAME" \
  --restart unless-stopped \
  --env-file "$APP_DIR/hanchae.env" \
  -p "$APP_PORT:8000" \
  -v "$APP_DIR/media:/app/media" \
  hanchae-backend:latest

echo "[4/4] 뜨는지 확인 (API 와 첫 화면)"
# 첫 배포는 빈 DB 에 테이블을 만드느라(migrate) 오래 걸릴 수 있어 2분까지 기다린다
for i in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:$APP_PORT/api/topics" >/dev/null 2>&1 \
    && curl -fsS "http://127.0.0.1:$APP_PORT/" >/dev/null 2>&1; then
    echo "배포 완료: /api/topics 와 / 응답 확인"
    docker image prune -f >/dev/null 2>&1 || true
    rm -f hanchae-backend.tar.gz
    exit 0
  fi
  sleep 2
done

echo "2분 안에 응답이 없어요. 아래 로그를 확인하세요." >&2
docker logs --tail 80 "$NAME" >&2
exit 1
