CREATE TABLE `sanction_histories` (
	`id`	BIGINT	NOT NULL	COMMENT 'PK, AI',
	`admin_member_id`	BIGINT	NOT NULL	COMMENT 'FK, AI 서비스 처리한 관리자',
	`report_id`	BIGINT	NULL	COMMENT 'FK, AI, 신고로 시작된 경우',
	`target_type`	VARCHAR(20)	NOT NULL	COMMENT 'MEMBER / BLOG / POST / COMMENT/GUESTBOOK',
	`target_id`	BIGINT	NOT NULL	COMMENT '타겟 테이블에서의 아이디',
	`action_type`	VARCHAR(20)	NOT NULL	COMMENT 'SUSPEND(회원 정지) / UNSUSPEND(정지 해제) / HIDE(숨김) / UNHIDE(숨김 해제) / RESTRICT(블로그 이용 제한) / UNRESTRICT(제한 해제)',
	`reason_type`	VARCHAR(20)	NOT NULL	COMMENT '제재 사유 정해야함',
	`until_at`	DATETIME	NULL,
	`created_at`	DATETIME	NOT NULL
);

CREATE TABLE `report_histories` (
	`id`	VARCHAR(255)	NOT NULL	COMMENT 'PK, AI',
	`reporter_member_id`	BIGINT	NOT NULL	COMMENT 'FK,  AI',
	`target_type`	VARCHAR(20)	NOT NULL	COMMENT 'POST / COMMENT / BLOG',
	`target_id`	BIGINT	NOT NULL	COMMENT '본인것은 신고 불가',
	`reason_code`	VARCHAR(20)	NOT NULL	COMMENT '사유목록 정해야함',
	`reason_detail`	VARCHAR(500)	NULL,
	`status`	VARCHAR(20)	NOT NULL	COMMENT 'PENDING(대기)/ACTION(조치 필요)/DISMISSED(종료/기각)',
	`handled_at`	DATETIME	NULL,
	`created_at`	DATETIME	NOT NULL
);

CREATE TABLE `members` (
	`id`	BIGINT	NOT NULL	COMMENT 'PK, AI',
	`email`	VARCHAR(255)	NULL	COMMENT '소셜 로그인일경우 null',
	`password`	VARCHAR(100)	NULL	COMMENT '이메일 인증 방식일 떄만  해시로 저장(소셜 로그인일 경우 null)',
	`nickname`	VARCHAR(50)	NOT NULL	COMMENT '닉네임, 중복허용 안함',
	`profile_image_url`	VARCHAR(500)	NULL	COMMENT '이미지 url',
	`role`	VARCHAR(20)	NOT NULL	DEFAULT USER	COMMENT 'USER(일반 회원) / ADMIN(사이트 관리자), 기본 USER',
	`account_status`	VARCHAR(20)	NOT NULL	COMMENT 'ACTIVE (활성)/ SUSPENDED(일시 중지) / WITHDRAWN(탈퇴), 기본 ACTIVE',
	`suspended_until`	DATETIME	NULL	COMMENT 'SUSPENDED인데 NULL이면 영구 정지',
	`created_at`	DATETIME	NOT NULL	COMMENT '회원 가입 일시',
	`deleted_at`	DATETIME	NULL	COMMENT '회원 탈퇴시 소프트 삭제(회원 행은 지우지 않고 status = WITHDRAWN과 함께 남긴다)'
);

CREATE TABLE `tags` (
	`tag_id`	BIGINT	NOT NULL	COMMENT 'PK',
	`blog_id`	BIGINT	NOT NULL	COMMENT 'FK, 태그는 블로그 단위(TAG-01)',
	`name`	VARCHAR(30)	NOT NULL	COMMENT '블로그 안에서 유일. 길이는 명세에 없어 임시값',
	`created_at`	DATETIME	NOT NULL,
	`updated_at`	DATETIME	NOT NULL	COMMENT '이름 변경(TAG-04)'
);

CREATE TABLE `categories` (
	`category_id`	BIGINT	NOT NULL	COMMENT 'PK',
	`parent_id`	BIGINT	NULL	COMMENT 'FK, NULL이면 최상위. 한 단계까지만(CAT-03)',
	`blog_id`	BIGINT	NOT NULL	COMMENT 'FK',
	`name`	VARCHAR(20)	NOT NULL	COMMENT '1~20자. 같은 상위 안에서 유일',
	`sort_order`	INT	NOT NULL	COMMENT 'CAT-04',
	`is_private`	BOOLEAN	NOT NULL	COMMENT 'CAT-05. 기본 FALSE',
	`updated_at`	DATETIME	NOT NULL
);

CREATE TABLE `comment` (
	`id`	BIGINT	NOT NULL,
	`content`	VARCHAR(1000)	NOT NULL,
	`is_secret`	BOOLEAN	NOT NULL,
	`updated_at`	DATETIME	NOT NULL,
	`deleted_at`	DATETIME	NULL	COMMENT '답글  있으면 '삭제된 댓글' 표시',
	`hidden_at`	DATETIME	NULL	COMMENT ''관리자가 숨긴 댓글'',
	`parent_id`	BIGINT	NULL	COMMENT 'FK → comments 자기 참조. 답글은 한 단계만',
	`post_id`	BIGINT	NOT NULL	COMMENT 'PK, 플랫폼 전체에서 유일한 글 번호. 글 주소에 사용'
);

CREATE TABLE `banned_words` (
	`id`	BIGINT	NOT NULL,
	`word`	BIGINT	NOT NULL,
	`blog ID`	BIGINT	NOT NULL	COMMENT 'FK → blogs. UNIQUE(blog_id, word)'
);

CREATE TABLE `guestbooks` (
	`id`	BIGINT	NOT NULL,
	`content`	VARCHAR(1000)	NOT NULL	COMMENT '규칙은 댓글과 같음',
	`updated_at`	DATETIME	NOT NULL,
	`deleted_at`	DATETIME	NULL,
	`hidden_at`	DATETIME	NULL	COMMENT '파트 1 신고,제재 대상',
	`blogID`	BIGINT	NOT NULL	COMMENT 'FK → blogs. 글이 아니라 블로그에 남김',
	`memberID`	BIGINT	NOT NULL	COMMENT 'FK → members. 작성자'
);

CREATE TABLE `notice_histories` (
	`id`	BIGINT	NOT NULL	COMMENT 'PK, AI',
	`admin_member_id`	BIGINT	NOT NULL	COMMENT 'FK, AI',
	`title`	VARCHAR(100)	NOT NULL	COMMENT '공지 제목',
	`content`	TEXT	NOT NULL	COMMENT '공지 내용',
	`created_at`	DATETIME	NOT NULL	COMMENT '공지 일시'
);

CREATE TABLE `notifications` (
	`id`	BIGINT	NOT NULL,
	`type`	VARCHAR(20)	NOT NULL	COMMENT 'comment/like/subscribe,new_post',
	`is_read`	BOOLEAN	NOT NULL,
	`memberID`	BIGINT	NOT NULL	COMMENT 'PK, AI',
	`target_type`	VARCHAR(20)	NOT NULL	COMMENT 'POST/COMMENT/BLOG',
	`target_id`	BIGINT	NOT NULL	COMMENT 'target_type에 따라 글/댓글/블로그 ID (FK 아님)'
);

CREATE TABLE `blogs` (
	`id`	BIGINT	NOT NULL	COMMENT 'PK, AI',
	`member_id`	BIGINT	NOT NULL	COMMENT 'FK, AI',
	`moved_to_blog_id`	BIGINT	NOT NULL	COMMENT 'FK, AI',
	`name`	VARCHAR(40)	NOT NULL	COMMENT '블로그 이름',
	`description`	VARCHAR(500)	NULL	COMMENT '블로그 소개',
	`skin`	VARCHAR(20)	NULL	COMMENT '블로그 스킨',
	`profile_image_url`	VARCHAR(500)	NULL	COMMENT '블로그 배경  이미지 url',
	`background_image_url`	VARCHAR(500)	NULL	COMMENT '블로그 배경  이미지 url',
	`address`	VARCHAR(32)	NOT NULL	COMMENT '사용자에게 보여지는 블로그 주소',
	`is_primary`	BOOLEAN	NOT NULL	COMMENT '대표 블로그 여부, 회원당 하나',
	`status`	VARCHAR(20)	NOT NULL	COMMENT 'ACTIVE/RESTRICTED(제한, ADMIN 기능)',
	`created_at`	DATETIME	NOT NULL	COMMENT '블로그 생성 일시',
	`deleted_at`	DATETIME	NULL	COMMENT '블로그 삭제시 소프트 삭제',
	`hidden_at`	DATETIME	NULL	COMMENT '서비스 관리자가 블로그 숨길 수 있음'
);

CREATE TABLE `sidebar_modules` (
	`id`	BIGINT	NOT NULL	COMMENT 'PK, AI',
	`module_type`	VARCHAR((20)	NOT NULL
);

CREATE TABLE `topics` (
	`topic_id`	BIGINT	NOT NULL	COMMENT 'PK',
	`name`	VARCHAR(20)	NOT NULL	COMMENT 'UK, IT, 여행 등',
	`sort_order`	INT	NOT NULL,
	`updated_at`	DATETIME	NOT NULL
);

CREATE TABLE `popular_posts` (
	`id`	BIGINT	NOT NULL	COMMENT 'PK',
	`ranking`	INT	NOT NULL	COMMENT 'rank는 MySQL 8 예약어라 피함',
	`view_count`	INT	NOT NULL	COMMENT '집계 기간(직전 1시간) 조회 수',
	`aggregated_at`	DATETIME	NOT NULL	COMMENT '정각. UNIQUE(aggregated_at, ranking)',
	`post_id`	BIGINT	NOT NULL	COMMENT 'PK, 플랫폼 전체에서 유일한 글 번호. 글 주소에 사용'
);

CREATE TABLE `post_views` (
	`post_view_id`	BIGINT	NOT NULL	COMMENT 'PK',
	`post_id`	BIGINT	NOT NULL	COMMENT 'FK',
	`member_id`	BIGINT	NOT NULL	COMMENT 'FK, 비회원이면 NULL',
	`viewer_key`	VARCHAR(64)	NOT NULL	COMMENT '비회원 구분용(쿠키 등). 중복 조회 판단',
	`created_at`	DATETIME	NOT NULL	COMMENT '조회한 시각. 인덱스(created_at, post_id)'
);

CREATE TABLE `blog_sidebar_modules` (
	`module_id`	BIGINT	NOT NULL	COMMENT 'PK, FK',
	`blog_id`	BIGINT	NOT NULL	COMMENT 'PK, FK, 블로그별 사이드바 구성',
	`position`	INT	NOT NULL	COMMENT '위에서부터 순서',
	`enabled`	BOOLEAN	NOT NULL	COMMENT '사이드바 커스텀 화면에서 각각의 모듈 활성화 가능(PROFILE·CATEGORY는 무조건 활성화)'
);

CREATE TABLE `likes` (
	`id`	BIGINT	NOT NULL	COMMENT 'PK, AI',
	`post_id`	BIGINT	NOT NULL	COMMENT 'PK, 플랫폼 전체에서 유일한 글 번호. 글 주소에 사용'
);

CREATE TABLE `saves` (
	`id`	BIGINT	NOT NULL	COMMENT 'members',
	`post_id`	BIGINT	NOT NULL	COMMENT 'PK, 플랫폼 전체에서 유일한 글 번호. 글 주소에 사용'
);

CREATE TABLE `posts` (
	`post_id`	BIGINT	NOT NULL	COMMENT 'PK, 플랫폼 전체에서 유일한 글 번호. 글 주소에 사용',
	`topic_id`	BIGINT	NULL	COMMENT 'FK',
	`category_id`	BIGINT	NULL	COMMENT 'FK',
	`blog_id`	BIGINT	NOT NULL	COMMENT 'FK, 블로그 이사(BLOG-06) 때 변경',
	`title`	VARCHAR(100)	NOT NULL	COMMENT '발행 시 1~100자. 임시저장은 빈 문자열 허용',
	`content`	MEDIUMTEXT	NOT NULL	COMMENT 'HTML. 스크립트 제거 후 저장',
	`thumbnail_url`	VARCHAR(500)	NULL	COMMENT 'NULL이면 본문 첫 이미지(POST-07)',
	`visibility`	VARCHAR(20)	NOT NULL	COMMENT 'PUBLIC/ PRIVATE/ SUBSCRIBERS. 기본 PURBLIC',
	`is_comment_allowed`	BOOLEAN	NOT NULL	COMMENT '기본 TRUE(CMT-07)',
	`view_count`	INT	NOT NULL	COMMENT '누적 조회수(POST-09), 기본 0',
	`scheduled_at`	DATETIME	NULL	COMMENT '예약 발행 시각(POSt-13)',
	`published_at`	DATETIME	NULL	COMMENT '처음 실제로 공개된 시각. 수정해도 불변. 목록 정렬 기준',
	`status`	VARCHAR(20)	NOT NULL	COMMENT 'DRAFT/ SCHEDULED/ PUBLISHED',
	`created_at`	DATETIME	NOT NULL	COMMENT '발행 시각이 같을때 정렬 보조 기준',
	`updated_at`	DATETIME	NOT NULL,
	`hidden_at`	DATETIME	NULL	COMMENT '서비스 관리자 숨김(ADMIN-03)'
);

CREATE TABLE `social_accounts` (
	`id`	BIGINT	NOT NULL	COMMENT 'PK, AI',
	`member_id`	BIGINT	NOT NULL	COMMENT 'FK, AI',
	`provider`	VARCHAR(20)	NOT NULL	COMMENT 'KAKAO/GOOGLE',
	`provider_user_id`	VARCHAR(100)	NOT NULL	COMMENT '제공사가 준 사용자 번호, 로그인시 해당 값으로 기존 회원을 조회',
	`created_at`	DATETIME	NOT NULL	COMMENT '로그인/연동 일시'
);

CREATE TABLE `subscriptions` (
	`id`	BIGINT	NOT NULL	COMMENT 'members. 구독하는 회원',
	`blogID`	BIGINT	NOT NULL	COMMENT 'blogs. 자기 블로그는 구독 불가 (SUB-01)'
);

CREATE TABLE `blog_visits` (
	`id`	BIGINT	NOT NULL	COMMENT 'PK',
	`visitor_key`	VARCHAR(64)	NOT NULL	COMMENT '쿠키·IP 해시 등. UNIQUE(blog_id, visitor_key, visit_date)로 하루 한 번',
	`visit_date`	DATE	NOT NULL	COMMENT '한국 시간 기준',
	`blogID`	BIGINT	NOT NULL	COMMENT 'FK → blogs',
	`memberID`	BIGINT	NOT NULL	COMMENT 'FK → members. 비회원은 NULL'
);

CREATE TABLE `blog_blocks` (
	`id`	BIGINT	NOT NULL	COMMENT 'FK → blogs. UNIQUE(blog_id, word)',
	`memberID`	BIGINT	NOT NULL	COMMENT 'PK, AI'
);

CREATE TABLE `images` (
	`image_id`	BIGINT	NOT NULL,
	`post_id`	BIGINT	NULL	COMMENT 'FK, 글 저장 전에 올리면 NULL. 글 삭제 시 SET NULL 후 정리',
	`url`	VARCHAR(500)	NOT NULL,
	`created_at`	DATETIME	NOT NULL
);

CREATE TABLE `post_tags` (
	`post_id`	BIGINT	NOT NULL	COMMENT 'PK,FK, 식별관계',
	`tag_id`	BIGINT	NOT NULL	COMMENT 'PK, FK, 식별관계. 글당 최대 10개(앱에서 검사)'
);

ALTER TABLE `sanction_histories` ADD CONSTRAINT `PK_SANCTION_HISTORIES` PRIMARY KEY (
	`id`
);

ALTER TABLE `report_histories` ADD CONSTRAINT `PK_REPORT_HISTORIES` PRIMARY KEY (
	`id`
);

ALTER TABLE `members` ADD CONSTRAINT `PK_MEMBERS` PRIMARY KEY (
	`id`
);

ALTER TABLE `tags` ADD CONSTRAINT `PK_TAGS` PRIMARY KEY (
	`tag_id`
);

ALTER TABLE `categories` ADD CONSTRAINT `PK_CATEGORIES` PRIMARY KEY (
	`category_id`
);

ALTER TABLE `comment` ADD CONSTRAINT `PK_COMMENT` PRIMARY KEY (
	`id`
);

ALTER TABLE `banned_words` ADD CONSTRAINT `PK_BANNED_WORDS` PRIMARY KEY (
	`id`
);

ALTER TABLE `guestbooks` ADD CONSTRAINT `PK_GUESTBOOKS` PRIMARY KEY (
	`id`
);

ALTER TABLE `notice_histories` ADD CONSTRAINT `PK_NOTICE_HISTORIES` PRIMARY KEY (
	`id`
);

ALTER TABLE `notifications` ADD CONSTRAINT `PK_NOTIFICATIONS` PRIMARY KEY (
	`id`
);

ALTER TABLE `blogs` ADD CONSTRAINT `PK_BLOGS` PRIMARY KEY (
	`id`
);

ALTER TABLE `sidebar_modules` ADD CONSTRAINT `PK_SIDEBAR_MODULES` PRIMARY KEY (
	`id`
);

ALTER TABLE `topics` ADD CONSTRAINT `PK_TOPICS` PRIMARY KEY (
	`topic_id`
);

ALTER TABLE `popular_posts` ADD CONSTRAINT `PK_POPULAR_POSTS` PRIMARY KEY (
	`id`
);

ALTER TABLE `post_views` ADD CONSTRAINT `PK_POST_VIEWS` PRIMARY KEY (
	`post_view_id`
);

ALTER TABLE `blog_sidebar_modules` ADD CONSTRAINT `PK_BLOG_SIDEBAR_MODULES` PRIMARY KEY (
	`module_id`,
	`blog_id`
);

ALTER TABLE `likes` ADD CONSTRAINT `PK_LIKES` PRIMARY KEY (
	`id`,
	`post_id`
);

ALTER TABLE `saves` ADD CONSTRAINT `PK_SAVES` PRIMARY KEY (
	`id`,
	`post_id`
);

ALTER TABLE `posts` ADD CONSTRAINT `PK_POSTS` PRIMARY KEY (
	`post_id`
);

ALTER TABLE `social_accounts` ADD CONSTRAINT `PK_SOCIAL_ACCOUNTS` PRIMARY KEY (
	`id`
);

ALTER TABLE `subscriptions` ADD CONSTRAINT `PK_SUBSCRIPTIONS` PRIMARY KEY (
	`id`,
	`blogID`
);

ALTER TABLE `blog_visits` ADD CONSTRAINT `PK_BLOG_VISITS` PRIMARY KEY (
	`id`
);

ALTER TABLE `blog_blocks` ADD CONSTRAINT `PK_BLOG_BLOCKS` PRIMARY KEY (
	`id`,
	`memberID`
);

ALTER TABLE `images` ADD CONSTRAINT `PK_IMAGES` PRIMARY KEY (
	`image_id`
);

ALTER TABLE `post_tags` ADD CONSTRAINT `PK_POST_TAGS` PRIMARY KEY (
	`post_id`,
	`tag_id`
);

ALTER TABLE `blog_sidebar_modules` ADD CONSTRAINT `FK_sidebar_modules_TO_blog_sidebar_modules_1` FOREIGN KEY (
	`module_id`
)
REFERENCES `sidebar_modules` (
	`id`
);

ALTER TABLE `blog_sidebar_modules` ADD CONSTRAINT `FK_blogs_TO_blog_sidebar_modules_1` FOREIGN KEY (
	`blog_id`
)
REFERENCES `blogs` (
	`id`
);

ALTER TABLE `likes` ADD CONSTRAINT `FK_members_TO_likes_1` FOREIGN KEY (
	`id`
)
REFERENCES `members` (
	`id`
);

ALTER TABLE `likes` ADD CONSTRAINT `FK_posts_TO_likes_1` FOREIGN KEY (
	`post_id`
)
REFERENCES `posts` (
	`post_id`
);

ALTER TABLE `saves` ADD CONSTRAINT `FK_members_TO_saves_1` FOREIGN KEY (
	`id`
)
REFERENCES `members` (
	`id`
);

ALTER TABLE `saves` ADD CONSTRAINT `FK_posts_TO_saves_1` FOREIGN KEY (
	`post_id`
)
REFERENCES `posts` (
	`post_id`
);

ALTER TABLE `subscriptions` ADD CONSTRAINT `FK_members_TO_subscriptions_1` FOREIGN KEY (
	`id`
)
REFERENCES `members` (
	`id`
);

ALTER TABLE `subscriptions` ADD CONSTRAINT `FK_blogs_TO_subscriptions_1` FOREIGN KEY (
	`blogID`
)
REFERENCES `blogs` (
	`id`
);

ALTER TABLE `blog_blocks` ADD CONSTRAINT `FK_blogs_TO_blog_blocks_1` FOREIGN KEY (
	`id`
)
REFERENCES `blogs` (
	`id`
);

ALTER TABLE `blog_blocks` ADD CONSTRAINT `FK_members_TO_blog_blocks_1` FOREIGN KEY (
	`memberID`
)
REFERENCES `members` (
	`id`
);

ALTER TABLE `post_tags` ADD CONSTRAINT `FK_posts_TO_post_tags_1` FOREIGN KEY (
	`post_id`
)
REFERENCES `posts` (
	`post_id`
);

ALTER TABLE `post_tags` ADD CONSTRAINT `FK_tags_TO_post_tags_1` FOREIGN KEY (
	`tag_id`
)
REFERENCES `tags` (
	`tag_id`
);

