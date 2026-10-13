/**
 * 여러 화면이 함께 쓰는 도구: 주소 만들기, 날짜, 글자 이스케이프, 헤더 메뉴
 */

// ----- 주소 -----
// 로컬에서는 한채 주소를 ?address= 로 넘긴다.
// 서브도메인({주소}.한채도메인)으로 바꿀 때는 이 묶음만 고치면 된다.
const Links = {
  village: () => '/',
  login: (next) => (next ? `/login?next=${encodeURIComponent(next)}` : '/login'),
  build: () => '/build',
  yard(address, filter = {}) {
    const params = new URLSearchParams({ address });
    Object.entries(filter).forEach(([key, value]) => {
      if (value !== undefined && value !== null) params.set(key, value);
    });
    return `/yard?${params}`;
  },
  post: (address, no) => `/post?address=${encodeURIComponent(address)}&no=${no}`,
  write: (no) => (no ? `/write?no=${no}` : '/write'),
  here: () => location.pathname + location.search,
};

// 같은 사이트 안의 주소면 그 경로를, 아니면 마을('/')을 돌려준다
function safeNext(value) {
  if (!value) return '/';
  try {
    const url = new URL(value, location.origin);
    return url.origin === location.origin ? url.pathname + url.search + url.hash : '/';
  } catch (e) {
    return '/';
  }
}

// 소셜 로그인 버튼을 보일지. 제공사 앱 키를 등록하고 서버의 SOCIAL_LOGIN=1 을 켠 뒤 true 로
const SOCIAL_LOGIN_READY = false;

// ----- 글자 -----
function escapeHTML(text) {
  return String(text ?? '').replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[ch]);
}

// 방 이름. category 가 null 이면 마루(방 없음)
function roomName(category) {
  return category ? category.name : '마루';
}

// 기록 발행 · 댓글의 중복 요청 막기 토큰 (API 명세서 2.6)
function newClientToken() {
  if (crypto.randomUUID) return crypto.randomUUID();
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.floor(Math.random() * 16);
    return (c === 'x' ? r : (r % 4) + 8).toString(16);
  });
}

// ----- 날짜 (저장은 UTC, 보여 줄 때 한국 시간) -----
const KST = { timeZone: 'Asia/Seoul' };

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ko-KR', { ...KST, month: 'long', day: 'numeric' });
}

function formatLongDate(iso) {
  return new Date(iso).toLocaleDateString('ko-KR', { ...KST, year: 'numeric', month: 'long', day: 'numeric' });
}

function formatDateTime(iso) {
  return new Date(iso).toLocaleString('ko-KR', { ...KST, month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false });
}

// 방금 · 12분 전 · 3시간 전 · 어제 · 10월 8일
function timeAgo(iso) {
  const minutes = Math.floor((Date.now() - new Date(iso)) / 60000);
  if (minutes < 1) return '방금';
  if (minutes < 60) return `${minutes}분 전`;
  if (minutes < 60 * 24) return `${Math.floor(minutes / 60)}시간 전`;
  if (minutes < 60 * 48) return '어제';
  return formatDate(iso);
}

// ----- 썸네일 -----
// 사진이 있으면 <img>, 없으면 빗금 자리
function thumbHTML(src, className) {
  if (src) return `<img class="${className}" src="${escapeHTML(src)}" alt="">`;
  return `<div class="${className} thumb" aria-hidden="true"></div>`;
}

// ----- 릴리즈 노트 -----
// 내용은 assets/releases.json. 맨 앞이 최신이다
const SEEN_RELEASE_KEY = 'hanchae.seenRelease';
let releasesPromise = null;

function loadReleases() {
  if (!releasesPromise) {
    releasesPromise = fetch('/assets/releases.json', { cache: 'no-cache' })
      .then((res) => {
        if (!res.ok) throw new Error('릴리즈 노트를 불러오지 못했어요.');
        return res.json();
      })
      .then((data) => data.releases || []);
  }
  return releasesPromise;
}

// 이 브라우저에서 본 최신 버전 (저장소를 못 쓰면 없는 것으로)
function seenRelease() {
  try {
    return localStorage.getItem(SEEN_RELEASE_KEY);
  } catch (e) {
    return null;
  }
}

function markReleaseSeen(version) {
  try {
    localStorage.setItem(SEEN_RELEASE_KEY, version);
  } catch (e) {
    // 저장소를 못 쓰면 다음에도 점이 보일 뿐이다
  }
}

// 아직 보지 않은 새 릴리즈가 있으면 헤더의 '릴리즈' 버튼에 점을 단다
async function markNewRelease() {
  const button = document.querySelector('.hc-release');
  if (!button || button.getAttribute('aria-current') === 'page') return;
  try {
    const [latest] = await loadReleases();
    if (latest && latest.version !== seenRelease()) {
      button.classList.add('has-new');
      button.setAttribute('aria-label', `릴리즈 (새 소식 v${latest.version})`);
    }
  } catch (e) {
    // 점을 못 달아도 버튼은 그대로 쓸 수 있다
  }
}

// ----- 헤더 메뉴 -----
// 로그인 전: 로그인 / 로그인 뒤: 내 한채(없으면 한채 짓기) · 글쓰기
async function renderHeaderNav(nav) {
  markNewRelease();
  const user = await Auth.currentUser();
  if (!user) {
    nav.innerHTML = `<a class="btn btn-secondary" href="${Links.login(Links.here())}">로그인</a>`;
    return { user: null };
  }
  nav.innerHTML = user.blog_address
    ? `<a class="plain" href="${Links.yard(user.blog_address)}">내 한채</a>
       <a class="btn btn-primary" href="${Links.write()}">글쓰기</a>`
    : `<a class="btn btn-primary" href="${Links.build()}">한채 짓기</a>`;
  return { user };
}

// 대문의 이웃 맺기 · 끊기 버튼. 로그인 전이면 로그인으로 보낸다
function bindNeighborButton(button, blog, onCount) {
  let subscribed = blog.is_subscribed;
  const paint = () => {
    button.className = `btn ${subscribed ? 'btn-secondary' : 'btn-primary'}`;
    button.setAttribute('aria-pressed', String(subscribed));
    button.textContent = subscribed ? '이웃이에요' : '이웃 맺기';
  };
  paint();
  button.addEventListener('click', async () => {
    if (!(await Auth.currentUser())) {
      location.href = Links.login(Links.here());
      return;
    }
    button.disabled = true;
    try {
      const result = await Store.setNeighbor(blog.address, !subscribed);
      subscribed = result.subscribed;
      paint();
      onCount(result.subscriber_count);
    } catch (err) {
      alert(err.message);
    } finally {
      button.disabled = false;
    }
  });
}

// 다른 화면으로 넘어가는 중에 끊긴 요청은 오류가 아니다
let leavingPage = false;
window.addEventListener('beforeunload', () => { leavingPage = true; });
window.addEventListener('pageshow', () => { leavingPage = false; });

// 화면 시작 함수를 감싸 실패해도 빈 화면으로 멈추지 않게 오류 안내를 보여 준다
function runPage(main) {
  main().catch((err) => {
    if (leavingPage) return;
    console.error(err);
    const notice = document.createElement('main');
    notice.className = 'notice card';
    notice.innerHTML = `
      <h1>화면을 불러오지 못했어요</h1>
      <p>${escapeHTML(err.firstMessage || err.message || '잠시 뒤 다시 시도해 주세요.')}</p>
      <button type="button" class="btn btn-primary">다시 불러오기</button>`;
    notice.querySelector('button').addEventListener('click', () => location.reload());
    // 반쯤 그려진 본문은 숨기고 안내를 그 자리에
    document.querySelectorAll('body > main, body > .house, body > .village, body > .gate, body > form').forEach((el) => {
      el.hidden = true;
    });
    const footer = document.querySelector('body > footer');
    document.body.insertBefore(notice, footer);
  });
}

// 헤더의 마을 검색은 마을에서 찾기(SCR-02)가 생기기 전까지 막아 둔다
function bindVillageSearch(form) {
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    alert('마을에서 찾기는 아직 준비 중이에요.');
  });
}
