/**
 * 없는 주소 (404.html, SCR-20)
 * 화면 모양은 404.html 에 있고, 여기서는 헤더의 로그인 상태만 채운다.
 */
async function main() {
  bindVillageSearch(document.getElementById('village-search'));
  await renderHeaderNav(document.getElementById('header-nav'));
}

runPage(main);
