/**
 * 한채 관리 (SCR-18) /settings
 * 한채 이름(현판) · 주인 소개를 바꾼다. 주인 사진은 내 정보의 프로필 사진을 쓴다.
 */
const form = document.getElementById('settings-form');
const nameInput = document.getElementById('blog-name-input');
const introInput = document.getElementById('blog-intro-input');
const errorBox = document.getElementById('form-error');
const saved = document.getElementById('saved');
let me = null;
let isDirty = false;

function renderPreview() {
  document.getElementById('preview-name').textContent = nameInput.value.trim() || '한채 이름';
  document.getElementById('preview-intro').textContent = introInput.value.trim() || '주인 소개가 여기에 보여요';
  document.getElementById('name-count').textContent = `${nameInput.value.length} / 40`;
  document.getElementById('intro-count').textContent = `${introInput.value.length} / 200`;
}

[nameInput, introInput].forEach((input) => {
  input.addEventListener('input', () => {
    isDirty = true;
    saved.hidden = true;
    renderPreview();
  });
});

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  errorBox.textContent = '';
  const name = nameInput.value.trim();
  if (!name) {
    errorBox.textContent = '한채 이름을 1~40자로 써 주세요.';
    nameInput.focus();
    return;
  }
  const button = document.getElementById('save-button');
  button.disabled = true;
  try {
    const blog = await Store.updateBlog(me.blog_address, { name, description: introInput.value.trim() });
    // 위의 작은 대문도 새 이름으로
    document.getElementById('gate').innerHTML = ownerGateHTML(blog);
    isDirty = false;
    saved.hidden = false;
  } catch (err) {
    errorBox.textContent = err.firstMessage || err.message;
  } finally {
    button.disabled = false;
  }
});

window.addEventListener('beforeunload', (e) => {
  if (!isDirty) return;
  e.preventDefault();
  e.returnValue = '';
});

async function main() {
  bindVillageSearch(document.getElementById('village-search'));
  const owner = await requireOwner();
  if (!owner) return;
  me = owner.user;
  const { blog } = owner;
  await renderHeaderNav(document.getElementById('header-nav'));

  document.getElementById('gate').innerHTML = ownerGateHTML(blog);
  document.getElementById('breadcrumb').innerHTML = `
    <a href="/">마을</a><span aria-hidden="true">›</span>
    <a href="${Links.yard(blog.address)}">${escapeHTML(blog.name)}</a><span aria-hidden="true">›</span>
    <span aria-current="page">한채 관리</span>`;
  document.getElementById('tabs').innerHTML = manageTabsHTML('settings');
  document.getElementById('cancel-link').href = Links.yard(blog.address);

  document.getElementById('owner-photo').innerHTML = avatarHTML(me.profile_image_url);
  document.getElementById('preview-photo').innerHTML = avatarHTML(me.profile_image_url);
  document.getElementById('preview-nickname').textContent = me.nickname;
  nameInput.value = blog.name;
  introInput.value = blog.description || '';
  renderPreview();

  document.getElementById('gate').hidden = false;
  document.getElementById('house').hidden = false;
}

runPage(main);
