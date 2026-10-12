/**
 * 마을 (SCR-01)
 * - 로그인 상태에 따라 헤더 메뉴, 내 자리, 이웃 소식을 바꾼다.
 * - 골목 · 새 기록 · 이웃 소식은 서버에서 받아 온다 (API 명세서 4.9, 4.7).
 * - 지금 많이 읽는 기록 · 북적이는 한채는 순위 API(매 정각 계산)가 생기면 채운다.
 */
const seat = document.getElementById('seat');
const neighbors = document.getElementById('neighbors');
const topicList = document.getElementById('topic-list');
const alleyPosts = document.getElementById('alley-posts');
const FRESH_STEP = 8;
let freshCursor = null;

// ----- 내 자리 -----
function renderSeat(user, myBlog) {
  if (!user) {
    const login = Links.login();
    seat.innerHTML = `
      <h2>마을에 들어오세요</h2>
      <p class="seat-desc">로그인하면 내 한채를 짓고, 이웃을 맺고, 기록에 공감을 남길 수 있어요.</p>
      <a class="btn btn-primary btn-block" href="${login}">로그인</a>
      ${SOCIAL_LOGIN_READY ? `<div class="social">
        <a class="btn btn-secondary" href="/accounts/kakao/login/?next=/">카카오</a>
        <a class="btn btn-secondary" href="/accounts/google/login/?next=/">구글</a>
        <a class="btn btn-secondary" href="/accounts/naver/login/?next=/">네이버</a>
      </div>` : ''}
      <p class="seat-join">처음이신가요? <a class="text-link" href="/login?tab=signup">이메일로 가입하기</a></p>`;
    neighbors.hidden = true;
    return;
  }

  const nickname = escapeHTML(user.nickname);
  const home = myBlog
    ? `<a class="text-link" href="${Links.yard(myBlog.address)}">${escapeHTML(myBlog.name)} · 이웃 ${myBlog.subscriber_count}</a>`
    : '<span class="seat-desc">아직 지은 한채가 없어요</span>';
  const actions = myBlog
    ? `<a class="btn btn-secondary" href="${Links.yard(myBlog.address)}">내 한채</a>
       <a class="btn btn-primary" href="${Links.write()}">글쓰기</a>`
    : `<a class="btn btn-primary me-build" href="${Links.build()}">한채 짓기</a>`;
  seat.innerHTML = `
    <div class="me">
      <div class="me-avatar" aria-hidden="true"></div>
      <div class="me-info">
        <h2>${nickname}</h2>
        ${home}
      </div>
    </div>
    <div class="me-actions">${actions}</div>
    <div class="me-links">
      <button type="button" id="me-button">내 정보</button>
      <button type="button" id="logout-button">로그아웃</button>
    </div>`;
  neighbors.hidden = false;

  document.getElementById('me-button').addEventListener('click', () => {
    alert('내 정보는 아직 준비 중이에요.');
  });
  document.getElementById('logout-button').addEventListener('click', async () => {
    await Auth.logOut();
    location.reload();
  });
}

// ----- 골목 -----
function alleyCardHTML(post) {
  return `
    <a class="alley-card card" href="${Links.post(post.blog.address, post.no)}">
      ${thumbHTML(post.thumbnail_url, 'thumb-img alley-thumb')}
      <span class="alley-text">
        <span class="alley-title">${escapeHTML(post.title)}</span>
        <span class="alley-excerpt">${escapeHTML(post.excerpt)}</span>
        <span class="alley-blog">${escapeHTML(post.blog.name)}</span>
      </span>
    </a>`;
}

async function selectTopic(button) {
  topicList.querySelectorAll('button').forEach((b) => {
    b.setAttribute('aria-pressed', String(b === button));
  });
  const { items: posts } = await Store.topicPosts(button.dataset.slug, { limit: 6 });
  alleyPosts.innerHTML = posts.length
    ? posts.map(alleyCardHTML).join('')
    : `<p class="empty">${escapeHTML(button.textContent)} 골목에는 아직 기록이 없어요.</p>`;
}

async function loadTopics() {
  try {
    const topics = await Store.getTopics();
    topicList.innerHTML = topics
      .map((t) => `<button type="button" data-slug="${escapeHTML(t.slug)}" aria-pressed="false">${escapeHTML(t.name)}</button>`)
      .join('');
    const first = topicList.querySelector('button');
    if (first) await selectTopic(first);
  } catch (err) {
    topicList.innerHTML = '<p class="empty">골목을 불러오지 못했어요. 잠시 뒤 다시 열어 주세요.</p>';
  }
}

topicList.addEventListener('click', (e) => {
  const button = e.target.closest('button');
  if (button) selectTopic(button);
});

document.getElementById('alley-more').addEventListener('click', () => {
  alert('골목 모아 보기는 아직 준비 중이에요.');
});

// ----- 이웃 소식 -----
async function renderNeighborPosts() {
  const { items: posts } = await Store.neighborFeed({ limit: 3 });
  document.getElementById('neighbor-posts').innerHTML = posts.length
    ? posts.map((p) => `
        <a class="neighbor-card" href="${Links.post(p.blog.address, p.no)}">
          <span class="neighbor-meta">${escapeHTML(p.blog.name)} · ${timeAgo(p.published_at)}</span>
          <span class="neighbor-title">${escapeHTML(p.title)}</span>
        </a>`).join('')
    : '<p class="empty">이웃을 맺으면 이웃 한채의 새 기록이 여기에 보여요.</p>';
}

// ----- 새 기록 (커서로 더 불러오기) -----
function freshRowHTML(p) {
  return `
    <a class="post-row" href="${Links.post(p.blog.address, p.no)}">
      <div class="post-row-text">
        <span class="post-row-title">${escapeHTML(p.title)}</span>
        <span class="post-row-excerpt">${escapeHTML(p.excerpt)}</span>
        <span class="post-row-meta">${escapeHTML(p.blog.name)} · ${escapeHTML(roomName(p.category))} · ${timeAgo(p.published_at)}</span>
      </div>
      ${thumbHTML(p.thumbnail_url, 'thumb-img fresh-thumb')}
    </a>`;
}

async function loadFresh() {
  const box = document.getElementById('fresh-posts');
  const { items, next_cursor: next } = await Store.newPosts({ cursor: freshCursor, limit: FRESH_STEP });
  const more = document.getElementById('fresh-more');
  if (more) more.remove();
  if (!freshCursor && !items.length) {
    box.innerHTML = '<p class="empty">아직 마을에 쌓인 기록이 없어요. 첫 기록을 남겨 보세요.</p>';
    return;
  }
  box.insertAdjacentHTML('beforeend', items.map(freshRowHTML).join(''));
  freshCursor = next;
  if (next) {
    box.insertAdjacentHTML('beforeend', '<button type="button" class="btn btn-secondary fresh-more" id="fresh-more">새 기록 더 불러오기</button>');
    document.getElementById('fresh-more').addEventListener('click', loadFresh);
  }
}

// ----- 사이드바: 순위 · 북적이는 한채 -----
// 순위 API(GET /api/rankings/*)는 매 정각 계산하는 작업과 함께 만든다
function renderRankingsPending() {
  document.getElementById('rank-list').innerHTML = '<li class="empty">순위는 매 정각에 계산해요. 아직 준비 중이에요.</li>';
  document.getElementById('house-list').innerHTML = '<p class="empty">북적이는 한채는 아직 준비 중이에요.</p>';
}

async function main() {
  bindVillageSearch(document.getElementById('village-search'));
  const { user } = await renderHeaderNav(document.getElementById('header-nav'));
  const myBlog = user ? await Store.getMyBlog() : null;
  renderSeat(user, myBlog);

  // 한채가 있으면 어귀의 한채 짓기 버튼을 내 한채로
  if (myBlog) {
    const build = document.querySelector('.entry-actions .btn');
    build.textContent = '내 한채 가기';
    build.href = Links.yard(myBlog.address);
  }

  await Promise.all([
    loadTopics(),
    user ? renderNeighborPosts() : null,
    loadFresh(),
  ]);
  renderRankingsPending();
}

runPage(main);
