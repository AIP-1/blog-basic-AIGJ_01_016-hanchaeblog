/**
 * 방 관리 (SCR-17) /rooms
 * 방 만들기 · 이름 바꾸기(그 자리에서) · ▲▼ 순서 · 없애기(기록은 마루로).
 */
const list = document.getElementById('room-list');
const addForm = document.getElementById('room-add');
const addInput = document.getElementById('room-name');
const addError = document.getElementById('room-add-error');
let address = '';
let rooms = [];
let maruCount = 0;
let totalCount = 0;
let editingId = null;
let orderSaving = Promise.resolve(); // ▲▼ 를 빨리 눌러도 저장은 차례대로

function render() {
  list.innerHTML = rooms.map((r, i) => {
    const order = `
      <span class="room-order">
        <button type="button" data-move="-1" aria-label="‘${escapeHTML(r.name)}’ 위로"${i === 0 ? ' disabled' : ''}>▲</button>
        <button type="button" data-move="1" aria-label="‘${escapeHTML(r.name)}’ 아래로"${i === rooms.length - 1 ? ' disabled' : ''}>▼</button>
      </span>`;
    const body = r.id === editingId
      ? `
        <form class="room-edit" data-rename novalidate>
          <input class="input" type="text" maxlength="20" value="${escapeHTML(r.name)}" aria-label="방 이름">
          <button type="submit" class="btn btn-primary">저장</button>
          <button type="button" class="btn btn-secondary" data-cancel>취소</button>
          <p class="form-error-line" role="alert"></p>
        </form>`
      : `
        <span class="room-name"><strong>${escapeHTML(r.name)}</strong><span>기록 ${r.post_count}</span></span>
        <span class="room-tools">
          <button type="button" class="text-link" data-edit>이름 바꾸기</button>
          <button type="button" class="text-link delete" data-delete>없애기</button>
        </span>`;
    return `<li class="room-row" data-id="${r.id}">${order}${body}</li>`;
  }).join('') + `
    <li class="room-maru">
      <span class="room-maru-dot" aria-hidden="true">·</span>
      <span><strong>마루</strong> · 기록 ${maruCount} — 방을 고르지 않은 기록이 모이는 곳이라 바꾸거나 없앨 수 없어요.</span>
    </li>`;

  if (editingId) {
    const input = list.querySelector('[data-rename] input');
    input.focus();
    input.select();
  }

  document.getElementById('room-preview').innerHTML = `
    <li class="is-total"><span>전체 기록</span><span>${totalCount}</span></li>
    ${rooms.map((r) => `<li><span>${escapeHTML(r.name)}</span><span>${r.post_count}</span></li>`).join('')}
    ${maruCount ? `<li class="is-maru"><span>마루</span><span>${maruCount}</span></li>` : ''}`;
}

async function load() {
  const result = await Store.getRooms(address);
  rooms = result.rooms;
  maruCount = result.uncategorized_count;
  totalCount = result.total_count;
  render();
}

function fieldMessage(err) {
  return (err.fields && err.fields.name) || err.firstMessage || err.message;
}

addForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  addError.textContent = '';
  const name = addInput.value.trim();
  if (!name) {
    addError.textContent = '방 이름을 1~20자로 써 주세요.';
    addInput.focus();
    return;
  }
  try {
    await Store.addRoom(address, name);
    addInput.value = '';
    await load();
  } catch (err) {
    addError.textContent = fieldMessage(err);
    addInput.focus();
  }
});

list.addEventListener('click', async (e) => {
  const row = e.target.closest('[data-id]');
  if (!row) return;
  const id = Number(row.dataset.id);
  const room = rooms.find((r) => r.id === id);

  const move = e.target.closest('[data-move]');
  if (move) {
    const from = rooms.indexOf(room);
    const to = from + Number(move.dataset.move);
    if (to < 0 || to >= rooms.length) return;
    [rooms[from], rooms[to]] = [rooms[to], rooms[from]];
    render();
    list.querySelector(`[data-id="${id}"] [data-move="${move.dataset.move}"]`)?.focus();
    const ids = rooms.map((r) => r.id);
    orderSaving = orderSaving.then(() => Store.orderRooms(address, ids)).catch(async (err) => {
      alert(err.firstMessage || err.message);
      await load();
    });
    return;
  }

  if (e.target.closest('[data-edit]')) {
    editingId = id;
    render();
    return;
  }

  if (e.target.closest('[data-cancel]')) {
    editingId = null;
    render();
    return;
  }

  if (e.target.closest('[data-delete]')) {
    const ok = await confirmDialog({
      title: `‘${room.name}’ 방을 없앨까요?`,
      text: room.post_count
        ? `이 방의 기록 ${room.post_count}개는 지워지지 않고 마루로 옮겨져요.`
        : '이 방에는 기록이 없어요.',
      confirmLabel: '없애기',
      danger: true,
    });
    if (!ok) return;
    try {
      await Store.deleteRoom(address, id);
      await load();
    } catch (err) {
      alert(err.firstMessage || err.message);
    }
  }
});

list.addEventListener('submit', async (e) => {
  const form = e.target.closest('[data-rename]');
  if (!form) return;
  e.preventDefault();
  const input = form.querySelector('input');
  const error = form.querySelector('.form-error-line');
  const name = input.value.trim();
  if (!name) {
    error.textContent = '방 이름을 1~20자로 써 주세요.';
    return;
  }
  try {
    await Store.renameRoom(address, editingId, name);
    editingId = null;
    await load();
  } catch (err) {
    error.textContent = fieldMessage(err);
    input.focus();
  }
});

list.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && editingId) {
    editingId = null;
    render();
  }
});

async function main() {
  bindVillageSearch(document.getElementById('village-search'));
  const owner = await requireOwner();
  if (!owner) return;
  const { blog } = owner;
  address = blog.address;
  await renderHeaderNav(document.getElementById('header-nav'));

  document.getElementById('gate').innerHTML = ownerGateHTML(blog);
  document.getElementById('breadcrumb').innerHTML = `
    <a href="/">마을</a><span aria-hidden="true">›</span>
    <a href="${Links.yard(blog.address)}">${escapeHTML(blog.name)}</a><span aria-hidden="true">›</span>
    <span aria-current="page">방 관리</span>`;
  document.getElementById('tabs').innerHTML = manageTabsHTML('rooms');

  await load();
  document.getElementById('gate').hidden = false;
  document.getElementById('house').hidden = false;
}

runPage(main);
