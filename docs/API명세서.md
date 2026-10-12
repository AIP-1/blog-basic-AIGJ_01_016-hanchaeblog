# 한채 API 명세서

## 문서 정보

| 항목 | 내용 |
| --- | --- |
| 문서명 | 한채 API 명세서 |
| 버전 | 0.1 (초안) |
| 작성자 | Minju |
| 작성일 | 2026-10-08 |
| 기준 문서 | `docs/기능명세서.md` v0.10, Crowfoot ERD 「한채 블로그 플랫폼」(v45), 한채 와이어프레임 |
| 범위 | 기능명세서 7장의 **1차 기능**. 2차 기능은 8장에 목록만 둔다 |

### 변경 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
| --- | --- | --- | --- |
| 0.1 | 2026-10-08 | Minju | 최초 작성. 공통 규칙, 데이터 모양, 영역별 API, 화면별 API 표 |

---

## 1. 구조

```
브라우저 (HTML · CSS · JS)                         서버 (Django)
  한채도메인/            ← 마을 화면들                 한채도메인/api/...   ← JSON API
  {주소}.한채도메인/      ← 한채 화면들   ── fetch ──▶  한채도메인/accounts/... ← 소셜 로그인 (화면 이동)
                                                      MySQL (Crowfoot ERD)
```

- 화면은 프론트엔드(JS)가 그리고, 서버는 JSON만 준다.
- API는 모두 서비스 주소 아래 `/api`에 있다. 한채 화면(서브도메인)도 `https://한채도메인/api/...`를 부른다.
- 한채는 URL에서 **한채 주소**(`{address}`, 예: `minju`)로, 기록은 **한채 안의 글 번호**(`{no}`)로 가리킨다 (기능명세서 선택 7.5). DB의 내부 ID(`posts.id`)는 API에 드러내지 않는다.

---

## 2. 공통 규칙

### 2.1 요청과 응답

| 항목 | 규칙 |
| --- | --- |
| 형식 | 요청 · 응답 본문은 JSON (`Content-Type: application/json`). 이미지 업로드만 `multipart/form-data` |
| 이름 | 필드 이름은 `snake_case` |
| 시각 | UTC, ISO 8601 (`2026-10-08T05:00:00Z`). 한국 시간으로 바꾸는 일은 화면이 한다 |
| 빈 값 | 값이 없으면 `null`. 목록이 비면 `[]` |
| 성공 코드 | 조회 · 수정 `200`, 생성 `201`, 본문 없는 성공(삭제 등) `204` |

### 2.2 로그인과 보안

| 항목 | 규칙 |
| --- | --- |
| 로그인 상태 | Django 세션 쿠키. 쿠키 도메인을 `.한채도메인`으로 두어 모든 한채 서브도메인에서 로그인이 유지된다. 유지 기간 2주(마지막 사용 기준) |
| CSRF | 바꾸는 요청(`POST` `PATCH` `PUT` `DELETE`)은 헤더 `X-CSRFToken`에 `csrftoken` 쿠키 값을 넣는다. 쿠키는 `GET /api/auth/csrf`로 받는다 |
| 다른 출처 | 서브도메인 화면에서 부르므로 CORS는 `https://*.한채도메인`만 허용하고 `credentials`를 허용한다. 프론트는 `fetch(url, { credentials: 'include' })` |
| 방문자 구분 | 조회수 중복을 거르려고 서버가 비회원에게도 `hc_vid` 쿠키(무작위 값)를 준다. DB에는 해시해서 `post_views.viewer_key`에 넣는다 |

### 2.3 권한 표기

| 표기 | 뜻 | 없을 때 |
| --- | --- | --- |
| 모두 | 로그인하지 않아도 된다 | — |
| 회원 | 로그인해야 한다 | `401 AUTH_REQUIRED` |
| 주인 | 그 한채의 주인이어야 한다 | 로그인 안 함 `401`, 주인 아님 `403 FORBIDDEN` |
| 작성자 | 그 댓글 · 방명록을 쓴 사람이어야 한다 | `403 FORBIDDEN` |
| 관리자 | 역할이 `ADMIN`이어야 한다 | `403 FORBIDDEN` |

**볼 수 없는 것은 404**: 남의 비공개 · 이웃 공개 기록, 관리자가 숨긴 기록, 이용 제한된 회원의 한채, 허문 한채는 모두 `404 NOT_FOUND`로 답해 있다는 사실도 숨긴다 (통합 명세 3.3, 4.1).

### 2.4 오류 응답

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력한 내용을 확인해 주세요.",
    "fields": { "title": "제목은 1~100자로 써 주세요." }
  }
}
```

| 상태 | `code` | 언제 |
| --- | --- | --- |
| 400 | `VALIDATION_ERROR` | 입력 형식 · 길이가 맞지 않음. `fields`에 칸별 이유 |
| 401 | `AUTH_REQUIRED` | 로그인이 필요함. 화면은 로그인으로 보내고 돌아올 주소를 `next`로 넘긴다 |
| 401 | `LOGIN_FAILED` | 이메일 · 비밀번호가 맞지 않음 |
| 403 | `FORBIDDEN` | 권한 없음 |
| 403 | `SUSPENDED` | 이용 제한된 회원. `detail`에 `{ "reason", "ends_at" }` |
| 403 | `EMAIL_NOT_VERIFIED` | 메일 인증 전 |
| 404 | `NOT_FOUND` | 없거나 볼 수 없음 |
| 409 | `CONFLICT` | 이미 있음 (주소 · 닉네임 중복, 이미 한채가 있음) |
| 413 | `FILE_TOO_LARGE` | 이미지 10MB 초과 |
| 415 | `UNSUPPORTED_FILE` | jpg · png · gif · webp가 아님 |
| 422 | `NOT_ALLOWED` | 규칙상 안 되는 동작 (내 글에 공감, 내 한채와 이웃 맺기 등) |
| 500 | `SERVER_ERROR` | 예상하지 못한 오류. 내부 정보는 담지 않는다 |

### 2.5 목록 나누기

| 방식 | 쓰는 곳 | 요청 | 응답 |
| --- | --- | --- | --- |
| **페이지** | 한채 안 목록(마당 · 방 · 태그 · 한채 안 검색), 마을 검색, 방명록 | `?page=1&size=10` (`size` 기본 10, 최대 50) | `{ "items": [...], "page": 1, "size": 10, "total": 24, "total_pages": 3 }` |
| **커서** | 계속 쌓이는 목록(새 기록, 골목, 이웃 소식) | `?cursor=...&limit=20` (`limit` 최대 50) | `{ "items": [...], "next_cursor": "..." }` 마지막이면 `next_cursor: null` |

- 마지막 페이지를 넘으면 오류가 아니라 빈 `items`를 준다 (통합 명세 4.4).
- 커서는 `(published_at, id)`를 묶은 값이라, 더 불러오는 사이에 새 글이 올라와도 같은 글이 두 번 나오거나 빠지지 않는다.

### 2.6 중복 요청 막기

연달아 눌러도 한 번만 처리한다 (통합 명세 8.3).

- **기록 발행 · 댓글 · 방명록**: 화면이 작성 화면을 열 때 UUID를 하나 만들어 `client_token`으로 보낸다. 같은 토큰이 다시 오면 새로 만들지 않고 처음 만든 것을 `200`으로 돌려준다 (ERD `client_token` 유일 키).
- **공감 · 이웃 맺기**: `PUT`(하기)과 `DELETE`(취소)로 나눠, 몇 번을 보내도 결과가 같다.

---

## 3. 데이터 모양

여러 API가 함께 쓰는 응답 조각이다. 아래 표의 필드명은 이 이름으로 가리킨다.

### 3.1 `UserSummary` 회원 요약

```json
{ "nickname": "민주", "profile_image_url": "https://.../p.webp", "blog_address": "minju" }
```

`blog_address`는 그 회원의 한채 주소(없으면 `null`). 댓글 · 방명록 작성자를 눌러 그 사람의 한채로 가는 데 쓴다. 탈퇴한 회원은 `{ "nickname": null, "profile_image_url": null, "blog_address": null, "withdrawn": true }`이고 화면에는 "떠난 사람"으로 보인다.

### 3.2 `BlogSummary` 한채 요약

```json
{
  "address": "minju",
  "name": "민주의 한채",
  "description": "개발과 여행을 기록합니다",
  "profile_image_url": null,
  "owner": { "nickname": "민주", "profile_image_url": null, "blog_address": "minju" },
  "subscriber_count": 12
}
```

### 3.3 `PostSummary` 기록 요약 (목록용)

```json
{
  "blog": { "address": "minju", "name": "민주의 한채" },
  "no": 7,
  "title": "처마 끝에 앉은 첫 기록",
  "excerpt": "본문에서 서식을 뺀 150자 요약",
  "thumbnail_url": "https://.../t.webp",
  "category": { "id": 3, "name": "개발" },
  "topic": { "slug": "it", "name": "IT·개발" },
  "published_at": "2026-10-08T05:00:00Z",
  "like_count": 4,
  "comment_count": 2,
  "visibility": "PUBLIC"
}
```

- `category`가 `null`이면 마루(방 없음), `topic`이 `null`이면 골목을 고르지 않은 기록이다.
- `thumbnail_url`은 대표 이미지, 없으면 본문 첫 이미지의 작은 이미지, 둘 다 없으면 `null`.
- `visibility`는 주인이 자기 목록을 볼 때만 `PRIVATE`가 나올 수 있다. 다른 사람에게는 공개 기록만 온다.

### 3.4 `Comment` 댓글 · 방명록

```json
{
  "id": 51,
  "author": { "nickname": "서현", "profile_image_url": null, "blog_address": "seohyun" },
  "content": "잘 읽었어요",
  "created_at": "2026-10-08T06:00:00Z",
  "edited_at": null,
  "can_edit": false,
  "can_delete": true
}
```

`can_edit`(작성자만), `can_delete`(작성자 또는 그 한채 주인)는 보는 사람 기준으로 서버가 계산해 준다. 화면은 이 값으로 수정 · 삭제 버튼을 보인다. 관리자가 숨긴 댓글은 `content: null, "hidden": true`로 오고 "관리자가 숨긴 댓글"로 보인다.

---

## 4. 영역별 API (1차)

### 4.1 AUTH 회원 · 로그인

| 메서드 · 주소 | 권한 | 하는 일 | 기능 | 테이블 |
| --- | --- | --- | --- | --- |
| `GET /api/auth/csrf` | 모두 | CSRF 쿠키를 준다. 앱을 열 때 한 번 | COM-01 | — |
| `GET /api/auth/me` | 모두 | 지금 로그인한 사람. 비회원이면 `{ "user": null }` | AUTH-02, AUTH-04 | users, blogs |
| `POST /api/auth/signup` | 모두 | 이메일 가입. 인증 메일을 보낸다 | AUTH-01 | users, account_emailaddress |
| `POST /api/auth/email/verify` | 모두 | 메일의 인증 키로 이메일 인증 | AUTH-01 | account_emailaddress |
| `POST /api/auth/login` | 모두 | 이메일 로그인 | AUTH-01 | users |
| `GET /accounts/{provider}/login/?next=` | 모두 | 소셜 로그인 시작(화면 이동). `provider`는 `kakao` `google` `naver`. 끝나면 `next`로 돌아온다. 처음이면 자동 가입 | AUTH-01 | socialaccount_socialaccount |
| `POST /api/auth/logout` | 회원 | 로그아웃 | AUTH-02 | — |
| `GET /api/auth/nickname-available?nickname=` | 모두 | 닉네임을 쓸 수 있는지 | AUTH-05 | users |
| `PATCH /api/me` | 회원 | 닉네임 · 프로필 이미지 수정 | AUTH-05 | users |

**`GET /api/auth/me` 응답** — 헤더와 "글쓰기 · 내 한채" 버튼이 이 값으로 갈 곳을 정한다 (기능명세서 6.2).

```json
{
  "user": {
    "nickname": "민주",
    "email": "minju@example.com",
    "profile_image_url": null,
    "role": "MEMBER",
    "blog_address": "minju"
  }
}
```

`blog_address`가 `null`이면 한채가 없는 회원이다 → 글쓰기 · 내 한채를 누르면 한채 짓기로 보낸다 (AUTH-04).

**`POST /api/auth/signup` 요청**

```json
{
  "email": "minju@example.com",
  "password": "8자 이상",
  "nickname": "민주",
  "agree_terms": true,
  "agree_privacy": true,
  "over_14": true
}
```

규칙: 비밀번호 8자 이상, 닉네임 2~20자 · 중복 불가, 세 동의 값은 모두 `true`여야 한다 (ERD REQ-002). 응답 `201` `{ "email_verification_sent": true }`.

**`POST /api/auth/login`** 요청 `{ "email", "password" }` → `200` `{ "user": ... }`(`/api/auth/me`와 같은 모양). 실패 `401 LOGIN_FAILED`, 메일 인증 전 `403 EMAIL_NOT_VERIFIED`, 이용 제한 `403 SUSPENDED`.

**`PATCH /api/me`** 요청 `{ "nickname"?, "profile_image_id"? }`. 프로필 이미지는 먼저 `POST /api/images`로 올리고 받은 `id`를 넣는다. `null`이면 이미지를 지운다.

### 4.2 BLOG 한채

| 메서드 · 주소 | 권한 | 하는 일 | 기능 | 테이블 |
| --- | --- | --- | --- | --- |
| `GET /api/blogs/address-available?address=` | 회원 | 한채 주소를 쓸 수 있는지 | BLOG-01 | blogs |
| `POST /api/blogs` | 회원 | 한채 짓기 | BLOG-01 | blogs |
| `GET /api/blogs/{address}` | 모두 | 대문 정보 | BLOG-02, SUB-03 | blogs, users, subscriptions |
| `PATCH /api/blogs/{address}` | 주인 | 한채 이름 · 소개 · 프로필 이미지 수정 | BLOG-02 | blogs |

**`GET /api/blogs/address-available?address=minju`**

```json
{ "available": false, "reason": "TAKEN" }
```

`reason`: `INVALID`(영문 소문자 · 숫자 · 하이픈 4~32자가 아님), `TAKEN`(쓰는 중이거나 허문 한채의 주소 — 영구 예약), `RESERVED`(`www` `api` `admin` `login` 같은 서비스 예약어). 쓸 수 있으면 `{ "available": true, "reason": null }`.

**`POST /api/blogs`** 요청 `{ "address", "name", "description"? }` → `201` `BlogSummary`. 이미 살아 있는 한채가 있으면 `409 CONFLICT`(회원당 한 채), 주소를 못 쓰면 `400`(`fields.address`).

**`GET /api/blogs/{address}`** 응답: `BlogSummary` + 보는 사람 기준 값

```json
{
  "address": "minju",
  "name": "민주의 한채",
  "description": "개발과 여행을 기록합니다",
  "profile_image_url": null,
  "owner": { "nickname": "민주", "profile_image_url": null, "blog_address": "minju" },
  "subscriber_count": 12,
  "post_count": 24,
  "is_owner": false,
  "is_subscribed": true
}
```

`post_count`는 보는 사람이 볼 수 있는 기록만 센다. `is_owner`가 `true`면 대문의 버튼이 "이웃 맺기" 대신 "글쓰기 · 한채 관리"가 된다.

### 4.3 POST 기록 · 이미지 · 골목

| 메서드 · 주소 | 권한 | 하는 일 | 기능 | 테이블 |
| --- | --- | --- | --- | --- |
| `GET /api/blogs/{address}/posts` | 모두 | 한채 안 기록 목록 (마당 · 방 · 태그 · 한채 안 검색 · 기록 관리) | BLOG-03, CAT-02, TAG-02, SRCH-01, MNG-01 | posts, categories, post_tags, tags |
| `GET /api/blogs/{address}/posts/{no}` | 모두 | 기록 하나 | POST-04, POST-10 | posts, tags, post_likes |
| `POST /api/blogs/{address}/posts/{no}/views` | 모두 | 조회 한 번 기록 | POST-09 | post_views, posts |
| `POST /api/blogs/{address}/posts` | 주인 | 기록 발행 | POST-01, POST-06, POST-07, POST-11, TAG-01 | posts, post_tags, tags, post_images |
| `PATCH /api/blogs/{address}/posts/{no}` | 주인 | 기록 수정 (공개 범위 바꾸기 포함) | POST-02, POST-06 | posts, post_tags, tags |
| `DELETE /api/blogs/{address}/posts/{no}` | 주인 | 기록 삭제 | POST-03 | posts (+ 댓글 · 공감 함께) |
| `POST /api/images` | 회원 | 이미지 올리기 | POST-05, AUTH-05, BLOG-02 | images |
| `GET /api/topics` | 모두 | 골목 10개 | POST-11, HOME-03 | topics |

**`GET /api/blogs/{address}/posts`** 거르는 값(함께 쓰지 않고 하나만 쓴다)

| 쿼리 | 뜻 | 화면 |
| --- | --- | --- |
| (없음) | 모든 기록 | 마당 SCR-06 |
| `category={id}` | 그 방의 기록. `category=none`이면 마루 | 방 SCR-07 |
| `tag={이름}` | 그 태그가 붙은 기록 | 태그별 기록 SCR-08 |
| `q={검색어}` | 제목 · 본문 · 태그에서 찾기. 앞뒤 공백을 빼고, 비면 `400` | 이 한채에서 찾기 SCR-21 |
| `visibility=PUBLIC\|PRIVATE` | 주인만. 기록 관리에서 공개 범위로 거르기 | 기록 관리 SCR-15 |

페이지 방식(`page`, `size` 기본 10), 최신순(처음 발행한 시각). 응답 `items`는 `PostSummary`. 주인이 보면 `PRIVATE` 기록도 섞여 오고, 각 항목에 `view_count`가 더 붙는다.

**`GET /api/blogs/{address}/posts/{no}`** 응답: `PostSummary` +

```json
{
  "content": "<p>정제한 HTML 본문</p>",
  "tags": ["한옥", "기록"],
  "view_count": 120,
  "liked_by_me": false,
  "is_owner": false,
  "prev": { "no": 6, "title": "이전 기록 제목" },
  "next": null
}
```

- `prev` · `next`는 같은 한채에서 보는 사람이 볼 수 있는 앞뒤 기록이다. 없으면 `null` (POST-10).
- 볼 수 없는 기록은 `404`. 조회수는 이 요청으로 오르지 않는다. 화면이 기록을 연 뒤 `POST .../views`를 따로 부른다.

**`POST /api/blogs/{address}/posts/{no}/views`** → `204`. 같은 방문자(`hc_vid` 또는 회원)가 30분 안에 다시 부르면 기록하지 않는다 (ERD REQ-008). 주인 본인의 조회는 세지 않는다.

**`POST /api/blogs/{address}/posts`** 요청

```json
{
  "title": "처마 끝에 앉은 첫 기록",
  "content": "<p>본문 HTML</p>",
  "category_id": 3,
  "topic_slug": "it",
  "tags": ["한옥", "기록"],
  "visibility": "PUBLIC",
  "cover_image_id": null,
  "image_ids": [101, 102],
  "client_token": "6f1c2b9e-0d7a-4c55-9a77-1f2e3d4c5b6a"
}
```

| 필드 | 규칙 |
| --- | --- |
| `title` | 앞뒤 공백을 뺀 뒤 1~100자. 필수 |
| `content` | 필수. 서버가 허용한 태그만 남기고 정제한다(스크립트 제거) |
| `category_id` | 그 한채의 방. `null`이면 마루 |
| `topic_slug` | 골목. `null`이면 고르지 않음 |
| `tags` | 최대 10개. 영문 대소문자만 다르면 같은 태그. 없던 이름이면 새로 만든다 |
| `visibility` | `PUBLIC` 또는 `PRIVATE` (1차). `SUBSCRIBERS`(이웃 공개)는 2차 |
| `cover_image_id` | 대표 이미지. `null`이면 본문 첫 이미지 |
| `image_ids` | 본문에 넣은 이미지들. 글과 이미지를 잇는다 |
| `client_token` | 2.6 참고 |

응답 `201` `{ "no": 7, "url": "https://minju.한채도메인/7" }`. 화면은 이 주소로 간다.

**`PATCH /api/blogs/{address}/posts/{no}`** 요청은 발행과 같은 필드에서 바꿀 것만 보낸다(`client_token` 없음). 글 번호, 처음 발행 시각, 공감 · 댓글 · 조회 수, 목록 순서는 바뀌지 않는다.

**`DELETE /api/blogs/{address}/posts/{no}`** → `204`. 댓글 · 공감이 함께 사라지고, 글 번호는 다시 쓰지 않는다.

**`POST /api/images`** (`multipart/form-data`, 필드 `file`) → `201`

```json
{ "id": 101, "url": "https://.../101.webp", "thumb_url": "https://.../101_thumb.webp", "width": 1600, "height": 900 }
```

jpg · png · gif · webp, 10MB 이하. 서버가 목록용 작은 이미지를 함께 만들고, 휴대폰 사진의 방향을 바로잡는다. 실패하면 `413` 또는 `415`.

**`GET /api/topics`** → `[{ "slug": "daily", "name": "일상" }, ...]` 10개, 정해진 순서.

### 4.4 CAT 방 · TAG 태그

| 메서드 · 주소 | 권한 | 하는 일 | 기능 | 테이블 |
| --- | --- | --- | --- | --- |
| `GET /api/blogs/{address}/categories` | 모두 | 방 안내 (방 목록과 기록 수) | BLOG-04, CAT-02 | categories, posts |
| `POST /api/blogs/{address}/categories` | 주인 | 방 만들기 | CAT-01 | categories |
| `PATCH /api/blogs/{address}/categories/{id}` | 주인 | 방 이름 바꾸기 | CAT-01 | categories |
| `PUT /api/blogs/{address}/categories/order` | 주인 | 방 순서 바꾸기 | CAT-04 | categories |
| `DELETE /api/blogs/{address}/categories/{id}` | 주인 | 방 없애기. 기록은 마루로 | CAT-01 | categories, posts |
| `GET /api/blogs/{address}/tags` | 모두 | 이 한채의 태그 목록 | TAG-03 | tags, post_tags |

**`GET /api/blogs/{address}/categories`** 응답

```json
{
  "total_count": 24,
  "rooms": [
    { "id": 3, "name": "개발", "post_count": 10 },
    { "id": 4, "name": "여행", "post_count": 8 }
  ],
  "uncategorized_count": 0
}
```

`rooms`는 주인이 정한 순서. 개수는 보는 사람이 볼 수 있는 기록만 센다. `uncategorized_count`가 0이면 화면은 마루를 숨긴다.

- `POST` 요청 `{ "name" }`: 1~20자, 같은 한채에서 겹칠 수 없음(`409`). 곁방(`parent_id`)은 2차.
- `PUT .../order` 요청 `{ "ids": [4, 3, 5] }`: 그 한채의 방 id를 빠짐없이 원하는 순서로.
- `DELETE` 응답 `200` `{ "moved_to_uncategorized": 8 }`. 확인 창 문구에 쓴다.

**`GET /api/blogs/{address}/tags`** → `[{ "name": "한옥", "post_count": 3 }, ...]` 많이 쓴 순. 볼 수 있는 기록에 붙은 태그만.

### 4.5 CMT 댓글 · 방명록

| 메서드 · 주소 | 권한 | 하는 일 | 기능 | 테이블 |
| --- | --- | --- | --- | --- |
| `GET /api/blogs/{address}/posts/{no}/comments` | 모두 | 기록의 댓글 (오래된 순) | CMT-01 | comments, users |
| `POST /api/blogs/{address}/posts/{no}/comments` | 회원 | 댓글 쓰기 | CMT-01 | comments |
| `PATCH /api/comments/{id}` | 작성자 | 댓글 고치기 | CMT-03 | comments |
| `DELETE /api/comments/{id}` | 작성자 · 주인 | 댓글 지우기 | CMT-01, CMT-02 | comments |
| `GET /api/blogs/{address}/guestbook` | 모두 | 방명록 (최신순, 페이지) | CMT-04 | guestbook_entries, users |
| `POST /api/blogs/{address}/guestbook` | 회원 | 방명록 남기기 | CMT-04 | guestbook_entries |
| `PATCH /api/guestbook/{id}` | 작성자 | 방명록 고치기 | CMT-04 | guestbook_entries |
| `DELETE /api/guestbook/{id}` | 작성자 · 주인 | 방명록 지우기 | CMT-04 | guestbook_entries |

- 댓글 목록은 한 기록의 댓글을 모두 준다(`{ "items": [Comment], "count": 3 }`). 방명록은 페이지 방식.
- 쓰기 요청 `{ "content", "client_token" }`: 앞뒤 공백을 뺀 1~1,000자, 글자만(HTML 없음). 응답 `201` `Comment`.
- 고치기 요청 `{ "content" }` → `200` `Comment`(`edited_at`이 채워짐). 남의 것은 주인이라도 고칠 수 없다.

### 4.6 SOC 공감

| 메서드 · 주소 | 권한 | 하는 일 | 기능 | 테이블 |
| --- | --- | --- | --- | --- |
| `PUT /api/blogs/{address}/posts/{no}/like` | 회원 | 공감하기 | SOC-01 | post_likes |
| `DELETE /api/blogs/{address}/posts/{no}/like` | 회원 | 공감 취소 | SOC-01 | post_likes |

응답 둘 다 `200` `{ "liked": true, "like_count": 5 }`. 이미 공감한 상태에서 `PUT`을 또 보내도 결과는 같다. 내 기록이면 `422 NOT_ALLOWED`. 공유(SOC-02, 주소 복사)는 화면에서만 하고 API가 없다.

### 4.7 SUB 이웃

| 메서드 · 주소 | 권한 | 하는 일 | 기능 | 테이블 |
| --- | --- | --- | --- | --- |
| `PUT /api/blogs/{address}/subscription` | 회원 | 이웃 맺기 | SUB-01 | subscriptions |
| `DELETE /api/blogs/{address}/subscription` | 회원 | 이웃 끊기 | SUB-01 | subscriptions |
| `GET /api/me/subscriptions` | 회원 | 내 이웃 한채 목록 | SUB-01 | subscriptions, blogs |
| `GET /api/me/feed` | 회원 | 이웃 소식 (이웃 한채의 새 기록) | SUB-02 | posts, subscriptions |

- 맺기 · 끊기 응답 `200` `{ "subscribed": true, "subscriber_count": 13 }`. 내 한채면 `422 NOT_ALLOWED`.
- `GET /api/me/subscriptions` → 페이지 방식, `items`는 `BlogSummary`, 이웃 맺은 최신순.
- `GET /api/me/feed` → 커서 방식, `items`는 `PostSummary`, 최신순. 볼 수 없는 기록은 빠진다. 마을에서는 `limit=3`으로 부른다. 이웃이 없으면 빈 `items`.

### 4.8 SRCH 마을에서 찾기

| 메서드 · 주소 | 권한 | 하는 일 | 기능 | 테이블 |
| --- | --- | --- | --- | --- |
| `GET /api/search/posts?q=&sort=&page=` | 모두 | 마을 전체의 공개 기록 찾기 | SRCH-02 | posts, tags, blogs |
| `GET /api/search/blogs?q=&page=` | 모두 | 한채 찾기 (이름 · 소개) | SRCH-02 | blogs |

- `sort`: `relevance`(정확도, 기본) 또는 `latest`. 페이지 방식.
- 기록 결과는 `PostSummary`(어느 한채 · 어느 방인지 포함), 한채 결과는 `BlogSummary`.
- 검색 화면은 두 API를 함께 불러 "기록" · "한채" 탭의 개수(`total`)를 보여 준다.
- 한채 안 검색(SRCH-01)은 4.3의 `GET /api/blogs/{address}/posts?q=`를 쓴다.

### 4.9 HOME 마을

| 메서드 · 주소 | 권한 | 하는 일 | 기능 | 테이블 |
| --- | --- | --- | --- | --- |
| `GET /api/home/new-posts?cursor=&limit=` | 모두 | 새 기록 (마을 전체 공개 기록, 최신순) | HOME-01 | posts, blogs |
| `GET /api/rankings/posts?limit=` | 모두 | 지금 많이 읽는 기록 | HOME-02 | ranking_snapshots, ranking_entries |
| `GET /api/rankings/blogs?limit=` | 모두 | 북적이는 한채 | HOME-04 | ranking_snapshots, ranking_entries |
| `GET /api/topics/{slug}/posts?cursor=&limit=` | 모두 | 골목의 기록 (최신순) | HOME-03 | posts, topics |

**`GET /api/rankings/posts?limit=10`** 응답

```json
{
  "window_end": "2026-10-08T05:00:00Z",
  "basis": "1H",
  "items": [
    { "position": 1, "score": 132, "post": { "...": "PostSummary" } }
  ]
}
```

- 서버가 매 정각에 계산해 저장한 값을 그대로 준다. 다음 정각까지 같은 순위다.
- `basis`: `1H`(최근 1시간), `24H`(1시간 조회가 없어 24시간으로 대신), `EMPTY`(둘 다 없음, `items: []`). 화면은 "○시 기준 · 최근 1시간/24시간"을 표시한다 (기능명세서 9.2).
- `GET /api/rankings/blogs` 항목은 `{ "position", "score", "blog": BlogSummary, "top_post": { "no", "title" } }`. `top_post`는 카드의 "대표 기록"이다.
- 숨긴 기록, 볼 수 없게 된 기록 · 한채는 응답할 때 빠진다.

### 4.10 ADMIN · COM

| 메서드 · 주소 | 권한 | 하는 일 | 기능 |
| --- | --- | --- | --- |
| `/api/admin/*` | 관리자 | 1차에는 관리 기능이 없고, 이 경로 전체를 관리자만 들어오게 막아 둔다. 화면(SCR-19)은 `GET /api/auth/me`의 `role`로 들어갈지 정한다 | ADMIN-01 |
| (모든 API) | — | 2.3 권한, 2.4 오류 응답을 따른다. 버튼을 숨겨도 서버가 다시 검사한다 | COM-01, COM-02 |

---

## 5. 화면별 API

화면을 열 때 부르는 것(**열 때**)과 사용자가 무언가 할 때 부르는 것(**할 때**)을 나눴다. 모든 화면은 처음에 `GET /api/auth/me`로 헤더를 그린다(아래 표에서는 생략).

### 마을

| 화면 | 열 때 | 할 때 |
| --- | --- | --- |
| **SCR-01 마을** | `GET /api/rankings/posts?limit=10` · `GET /api/rankings/blogs?limit=4` · `GET /api/topics` → 첫 골목 `GET /api/topics/{slug}/posts?limit=6` · `GET /api/home/new-posts?limit=20` · (로그인 + 이웃 있음) `GET /api/me/feed?limit=3` | 골목 탭 바꾸기 `GET /api/topics/{slug}/posts?limit=6` · 새 기록 더 불러오기 `GET /api/home/new-posts?cursor=` |
| **SCR-02 마을에서 찾기** | `GET /api/search/posts?q=` · `GET /api/search/blogs?q=` | 정렬 · 페이지 바꾸기 (같은 API) · 결과 없으면 `GET /api/rankings/posts?limit=5` 추천 |
| **SCR-03 골목** | `GET /api/topics` · `GET /api/topics/{slug}/posts` | 더 불러오기 `?cursor=` |
| **SCR-05 로그인** | — | `POST /api/auth/login` · 소셜 `GET /accounts/{provider}/login/?next=` · 가입 `POST /api/auth/signup` · 인증 `POST /api/auth/email/verify` |

### 한채

한채 화면(SCR-06~10, 21)은 공통으로 대문과 방 안내를 그린다: `GET /api/blogs/{address}` · `GET /api/blogs/{address}/categories` · `GET /api/blogs/{address}/tags`. 대문의 이웃 맺기는 `PUT · DELETE /api/blogs/{address}/subscription`.

| 화면 | 열 때 (공통 외) | 할 때 |
| --- | --- | --- |
| **SCR-06 마당** | `GET /api/blogs/{address}/posts?page=1` | 페이지 바꾸기 |
| **SCR-07 방** | `GET /api/blogs/{address}/posts?category={id}` | 페이지 바꾸기 |
| **SCR-08 태그별 기록** | `GET /api/blogs/{address}/posts?tag={이름}` | 페이지 바꾸기 |
| **SCR-09 기록** | `GET /api/blogs/{address}/posts/{no}` → `POST .../views` · `GET .../comments` | 공감 `PUT · DELETE .../like` · 댓글 `POST .../comments`, `PATCH · DELETE /api/comments/{id}` · 삭제(주인) `DELETE .../posts/{no}` |
| **SCR-10 방명록** | `GET /api/blogs/{address}/guestbook?page=1` | `POST .../guestbook` · `PATCH · DELETE /api/guestbook/{id}` |
| **SCR-21 이 한채에서 찾기** | `GET /api/blogs/{address}/posts?q=` | 페이지 바꾸기 |

### 회원

| 화면 | 열 때 | 할 때 |
| --- | --- | --- |
| **SCR-11 내 정보** | (`/api/auth/me`로 충분) | 닉네임 확인 `GET /api/auth/nickname-available` · 사진 `POST /api/images` · 저장 `PATCH /api/me` · 로그아웃 `POST /api/auth/logout` |
| **SCR-12 이웃 소식** | `GET /api/me/feed` · (이웃 탭) `GET /api/me/subscriptions` | 더 불러오기 · 이웃 끊기 `DELETE /api/blogs/{address}/subscription` |
| **SCR-13 한채 짓기** | (한채가 이미 있으면 `/api/auth/me`의 `blog_address`로 그 마당에 보냄) | 주소 확인 `GET /api/blogs/address-available` (입력 멈추고 0.3초 뒤) · 짓기 `POST /api/blogs` |

### 한채 관리 (주인)

| 화면 | 열 때 | 할 때 |
| --- | --- | --- |
| **SCR-14 글쓰기** | `GET /api/blogs/{address}/categories` · `GET /api/topics` · (수정이면) `GET /api/blogs/{address}/posts/{no}` | 사진 `POST /api/images` · 발행 `POST /api/blogs/{address}/posts` · 수정 `PATCH .../posts/{no}` · 새 방 `POST .../categories` |
| **SCR-15 기록 관리** | `GET /api/blogs/{address}/posts?page=1` (주인이라 비공개 포함) | 공개 범위 바꾸기 `PATCH .../posts/{no}` (`{ "visibility" }`) · 삭제 `DELETE .../posts/{no}` |
| **SCR-17 방 관리** | `GET /api/blogs/{address}/categories` | `POST` · `PATCH` · `DELETE .../categories/{id}` · 순서 `PUT .../categories/order` |
| **SCR-18 한채 관리** | `GET /api/blogs/{address}` | 사진 `POST /api/images` · 저장 `PATCH /api/blogs/{address}` |

### 기타

| 화면 | 열 때 | 할 때 |
| --- | --- | --- |
| **SCR-19 마을 관리** | `GET /api/auth/me`로 `role`이 `ADMIN`인지 확인 (1차는 빈 관리 화면) | — |
| **SCR-20 오류** | — | API가 `404`면 "길을 잃었어요", `403`이면 "들어갈 수 없는 곳이에요" |

SCR-04(마을 소식판), SCR-16(댓글 · 방명록 관리)은 2차 화면이라 8장에 둔다.

---

## 6. 1차 API 한눈에 보기

| 영역 | 개수 | API |
| --- | --- | --- |
| AUTH | 9 | csrf, me, signup, email/verify, login, 소셜, logout, nickname-available, PATCH me |
| BLOG | 4 | address-available, POST blogs, GET · PATCH blog |
| POST | 8 | 목록, 상세, views, 발행, 수정, 삭제, images, topics |
| CAT · TAG | 6 | 방 목록 · 만들기 · 이름 · 순서 · 없애기, 태그 목록 |
| CMT | 8 | 댓글 목록 · 쓰기 · 고치기 · 지우기, 방명록 목록 · 쓰기 · 고치기 · 지우기 |
| SOC | 2 | 공감 하기 · 취소 |
| SUB | 4 | 이웃 맺기 · 끊기, 내 이웃, 이웃 소식 |
| SRCH | 2 | 기록 찾기, 한채 찾기 |
| HOME | 4 | 새 기록, 인기 기록, 북적이는 한채, 골목 기록 |
| **합계** | **47** | (+ `/api/admin/*` 접근 제어) |

---

## 7. 결정 사항과 남은 것

### 7.1 이 문서에서 정한 것

| 항목 | 결정 | 이유 |
| --- | --- | --- |
| 기록 가리키는 법 | `/api/blogs/{address}/posts/{no}` (한채 주소 + 한채 안 번호) | 화면 주소(`{address}.한채도메인/{no}`)와 같은 짝이라 바꿔 끼우기 쉽다. 내부 ID를 드러내지 않는다 |
| 댓글 · 방명록 고치기 · 지우기 | `/api/comments/{id}`처럼 짧은 주소 | 댓글 id만으로 찾을 수 있고, 권한은 서버가 댓글에서 한채를 찾아 검사한다 |
| 조회 기록 | 상세 조회(`GET`)와 분리한 `POST .../views` | `GET`은 아무것도 바꾸지 않아야 하고, 미리 불러오기 · 새로고침으로 조회수가 새는 것을 막는다 |
| 기록 관리 목록 | 따로 두지 않고 한채 기록 목록을 주인이 부르면 비공개도 포함 | API 수를 줄인다. 임시저장(2차)이 생기면 `status=DRAFT` 거르기를 더한다 |
| 목록 나누기 | 한채 안은 페이지, 마을의 쌓이는 목록은 커서 | 통합 명세 4.4 (한채 목록 10개 페이지, 더보기 목록은 중복 · 누락 없이) |
| API 주소 | 서비스 주소 한 곳(`한채도메인/api`) | 서브도메인마다 API를 두지 않아 CORS · 쿠키 설정이 한 번으로 끝난다 |
| 백엔드 | Django + Django REST Framework + django-allauth (기능명세서 1.5, 0.11) | 기준 ERD가 Django 구조다 |

### 7.2 남은 것

| 항목 | 내용 |
| --- | --- |
| 서비스 도메인 | 미정. 정해지면 쿠키 도메인 · CORS 허용 출처에 넣는다 |
| 본문 HTML 허용 태그 | 정제할 때 남길 태그 · 속성 목록(문단, 제목, 굵게, 목록, 인용, 코드, 링크, 이미지)을 구현 때 확정 |
| 예약어 목록 | 한채 주소로 못 쓰는 단어(`www` `api` `admin` `login` `static` `mail` …)를 구현 때 확정 |

---

## 8. 2차 API (목록만)

만들 때 이 문서에 자세히 더한다.

| 기능 | API (안) | 새로 필요한 ERD |
| --- | --- | --- |
| AUTH-06 탈퇴 | `DELETE /api/me` | — (users 행 남김) |
| BLOG-07 한채 허물기 | `DELETE /api/blogs/{address}` | — (blogs.deleted_at) |
| POST-08 임시저장 | `GET /api/blogs/{address}/posts?status=DRAFT`, 발행 API에 `status` | — (posts.status) |
| POST-12 이웃 공개 | `visibility: "SUBSCRIBERS"` | 반영됨 (v45) |
| CAT-03 곁방 | 방 만들기에 `parent_id` | — (categories.parent_id) |
| CAT-05 닫힌 방 | 방 수정에 `is_private` | categories.is_private |
| CMT-05 답글 | 댓글 쓰기에 `parent_id` | comments.parent_id |
| SOC-03 저장 | `PUT · DELETE /api/blogs/{address}/posts/{no}/save`, `GET /api/me/saved` | saves |
| SUB-04 알림 | `GET /api/me/notifications`, `POST /api/me/notifications/read` | notifications |
| SUB-05 서로 이웃 | `GET /api/blogs/{address}`에 `subscribes_me` | — |
| SUB-06 추천 한채 | `GET /api/home/recommended-blogs` | — |
| HOME-05 마을 소식판 | 4.9 순위 API에 `limit` 없이 | — |
| MNG-02 댓글 · 방명록 관리 | `GET /api/blogs/{address}/manage/comments` | — |
| MNG-03 다녀간 사람 | `GET /api/blogs/{address}/manage/stats` | blog_visits |
| ADMIN-02~04 | `/api/admin/users/{id}/sanctions`, `/api/admin/posts/{id}/hide`, `/api/reports` | user_sanctions, admin_logs (있음), reports |
