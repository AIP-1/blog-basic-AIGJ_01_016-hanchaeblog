/**
 * 릴리즈 노트 (/releases)
 * 내용은 assets/releases.json 에서 읽는다. 업데이트할 때 그 파일의 맨 앞에 새 릴리즈를 더한다.
 */
const CHANGE_TYPES = {
  new: '새 기능',
  improved: '좋아진 점',
  fixed: '고친 것',
  known: '알려진 문제',
};

function releaseHTML(release, isLatest) {
  // 종류별로 묶어 정해진 순서대로 보여 준다
  const groups = Object.keys(CHANGE_TYPES)
    .map((type) => ({ type, items: release.changes.filter((c) => c.type === type) }))
    .filter((group) => group.items.length);

  return `
    <article class="release card" id="v${escapeHTML(release.version)}">
      <header class="release-head">
        <span class="release-version">v${escapeHTML(release.version)}</span>
        ${isLatest ? '<span class="release-latest">최신</span>' : ''}
        <time class="release-date" datetime="${escapeHTML(release.date)}">${formatLongDate(`${release.date}T00:00:00+09:00`)}</time>
      </header>
      <h2 class="release-title">${escapeHTML(release.title)}</h2>
      ${groups.map((group) => `
        <section class="release-group release-${group.type}">
          <h3>${CHANGE_TYPES[group.type]}</h3>
          <ul>${group.items.map((c) => `<li>${escapeHTML(c.text)}</li>`).join('')}</ul>
        </section>`).join('')}
    </article>`;
}

async function main() {
  bindVillageSearch(document.getElementById('village-search'));
  await renderHeaderNav(document.getElementById('header-nav'));

  const releases = await loadReleases();
  const list = document.getElementById('release-list');
  list.innerHTML = releases.length
    ? releases.map((release, i) => releaseHTML(release, i === 0)).join('')
    : '<p class="empty">아직 적어 둔 릴리즈가 없어요.</p>';

  // 이 화면을 열었으면 최신 릴리즈를 본 것으로 기록한다 (버튼의 점을 끈다)
  if (releases.length) markReleaseSeen(releases[0].version);
}

runPage(main);
