/**
 * 마을에서 찾기 (SCR-02) /search?q=한옥
 * search?q=&type=blogs        한채 탭
 * search?q=&sort=latest       기록을 최신순으로
 * 기록 · 한채 두 API 를 함께 불러 탭에 개수를 보인다 (API 명세서 4.8).
 */
const params = new URLSearchParams(location.search);
const q = (params.get('q') || '').trim();
const type = params.get('type') === 'blogs' ? 'blogs' : 'posts';
const sort = params.get('sort') === 'latest' ? 'latest' : 'relevance';
const page = Number(params.get('page')) || 1;

// 찾은 낱말을 노랗게. 원래 글에서 나눈 뒤 조각마다 이스케이프한다 (&amp; 같은 글자가 깨지지 않게)
function highlight(text) {
  const needle = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return String(text || '')
    .split(new RegExp(`(${needle})`, 'gi'))
    .map((part, i) => (i % 2 ? `<mark>${escapeHTML(part)}</mark>` : escapeHTML(part)))
    .join('');
}

function blogRowHTML(b, compact) {
  return `
    <a class="search-blog${compact ? ' is-compact' : ''}" href="${Links.yard(b.address)}">
      ${avatarHTML(b.profile_image_url)}
      <span class="search-blog-text">
        <span class="hyeonpan hyeonpan-sm">${highlight(b.name)}</span>
        <span class="search-blog-meta">${escapeHTML(b.owner.nickname || '떠난 사람')} · 이웃 ${b.subscriber_count}${b.description ? ` · ${highlight(b.description)}` : ''}</span>
      </span>
    </a>`;
}

function emptyHTML(what) {
  return `
    <div class="search-empty">
      <strong>‘${escapeHTML(q)}’과 맞는 ${what}이 없어요</strong>
      <span>낱말을 줄이거나 다른 말로 찾아 보세요. 나만 보기 기록은 찾지 않아요.</span>
      <a class="text-link" href="/">마을로 돌아가기</a>
    </div>`;
}

function renderTabs(postTotal, blogTotal) {
  const tab = (key, label, total) => `<a href="${Links.search(q, { type: key })}"${key === type ? ' aria-current="page"' : ''}>${label} <span class="tab-count">${total}</span></a>`;
  document.getElementById('search-tabs').innerHTML = tab('posts', '기록', postTotal) + tab('blogs', '한채', blogTotal);
}

function renderPosts(result, blogs) {
  const sortChip = (key, label) => `<a href="${Links.search(q, { sort: key })}"${key === sort ? ' aria-current="true"' : ''}>${label}</a>`;
  document.getElementById('search-main').innerHTML = `
    <div class="sort-chips" role="group" aria-label="정렬">${sortChip('relevance', '정확도순')}${sortChip('latest', '최신순')}</div>
    ${result.items.length ? result.items.map((p) => villagePostRowHTML(p, highlight(p.title))).join('') : emptyHTML('기록')}
    <nav class="pager" aria-label="페이지">${pagerHTML(result, (p) => Links.search(q, { sort, page: p }))}</nav>`;

  // 옆에는 찾은 한채 몇 곳을 미리
  document.getElementById('search-side').innerHTML = blogs.total
    ? `
      <section class="card search-side-card" aria-labelledby="side-blogs">
        <div class="giwa giwa-thin" aria-hidden="true"></div>
        <div class="dancheong-band" aria-hidden="true"></div>
        <div class="search-side-body">
          <div class="search-side-head"><h2 id="side-blogs">찾은 한채</h2><span>이름 · 소개에서 찾았어요</span></div>
          ${blogs.items.map((b) => blogRowHTML(b, true)).join('')}
          ${blogs.total > blogs.items.length ? `<a class="text-link search-side-more" href="${Links.search(q, { type: 'blogs' })}">한채 ${blogs.total}곳 모두 보기</a>` : ''}
        </div>
      </section>`
    : '';
}

function renderBlogs(result) {
  document.getElementById('search-main').innerHTML = `
    ${result.items.length ? `<div class="search-blogs">${result.items.map((b) => blogRowHTML(b, false)).join('')}</div>` : emptyHTML('한채')}
    <nav class="pager" aria-label="페이지">${pagerHTML(result, (p) => Links.search(q, { type: 'blogs', page: p }))}</nav>`;
  document.getElementById('search-side').innerHTML = '';
}

async function main() {
  bindVillageSearch(document.getElementById('village-search'));
  await renderHeaderNav(document.getElementById('header-nav'));
  if (!q) {
    location.replace('/');
    return;
  }
  document.title = `‘${q}’ 찾기 · 한채`;
  document.getElementById('search-title').textContent = `‘${q}’ 찾은 결과`;

  if (type === 'posts') {
    const [posts, blogs] = await Promise.all([
      Store.searchPosts({ q, sort, page }),
      Store.searchBlogs({ q, size: 3 }),
    ]);
    renderTabs(posts.total, blogs.total);
    renderPosts(posts, blogs);
  } else {
    const [blogs, posts] = await Promise.all([
      Store.searchBlogs({ q, page }),
      Store.searchPosts({ q, page: 1 }),
    ]);
    renderTabs(posts.total, blogs.total);
    renderBlogs(blogs);
  }
  document.getElementById('house').hidden = false;
}

runPage(main);
