/**
 * 로그인 · 가입 (SCR-05)
 * /login?tab=signup 으로 들어오면 가입 탭을 연다.
 * /login?next=/주소 로 들어오면 로그인한 뒤 그 주소로 돌아간다.
 */
const loginForm = document.getElementById('login-form');
const signupForm = document.getElementById('signup-form');
const tabs = document.querySelectorAll('.login-tabs [role="tab"]');
const params = new URLSearchParams(location.search);

// 다른 사이트로 보내지 않도록 같은 사이트 안의 주소(/로 시작)만 받는다
const nextParam = params.get('next') || '/';
const next = nextParam.startsWith('/') && !nextParam.startsWith('//') ? nextParam : '/';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// ----- 탭 -----
function showTab(name) {
  tabs.forEach((tab) => {
    const selected = tab.dataset.tab === name;
    tab.setAttribute('aria-selected', String(selected));
    tab.tabIndex = selected ? 0 : -1;
  });
  loginForm.hidden = name !== 'login';
  signupForm.hidden = name !== 'signup';
}

document.addEventListener('click', (e) => {
  const button = e.target.closest('[data-tab]');
  if (button) showTab(button.dataset.tab);
});

// 탭끼리 좌우 화살표로 옮겨 다닌다
document.querySelector('.login-tabs').addEventListener('keydown', (e) => {
  if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
  const other = [...tabs].find((tab) => tab.getAttribute('aria-selected') !== 'true');
  showTab(other.dataset.tab);
  other.focus();
});

// 소셜 로그인은 끝나면 next 로 돌아온다
document.querySelectorAll('.social-link').forEach((link) => {
  link.href = `/accounts/${link.dataset.provider}/login/?next=${encodeURIComponent(next)}`;
});

// ----- 폼 -----
function showError(form, message) {
  form.querySelector('.form-error').textContent = message;
}

// 성공하면 onSuccess, 실패하면 서버가 준 문장을 보여 준다
async function submitWith(form, action, onSuccess) {
  const button = form.querySelector('.form-submit');
  showError(form, '');
  button.disabled = true;
  try {
    const result = await action();
    if (result.ok) {
      onSuccess();
    } else {
      showError(form, result.message);
    }
  } catch (err) {
    showError(form, err.message);
  } finally {
    button.disabled = false;
  }
}

// 가입하면 인증 메일이 간다. 인증해야 로그인할 수 있으므로 로그인 탭으로 돌려보낸다
function showVerificationSent(email) {
  showTab('login');
  loginForm.elements.email.value = email;
  const notice = document.getElementById('signup-done');
  notice.querySelector('strong').textContent = email;
  notice.hidden = false;
  loginForm.elements.password.focus();
}

loginForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const { email, password } = loginForm.elements;

  if (!EMAIL_PATTERN.test(email.value.trim())) return showError(loginForm, '이메일을 올바르게 입력해 주세요.');
  if (!password.value) return showError(loginForm, '비밀번호를 입력해 주세요.');

  submitWith(loginForm, () => Auth.logIn(email.value, password.value), () => { location.href = next; });
});

signupForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const { nickname, email, password, passwordConfirm, agreeTerms, agreePrivacy, over14 } = signupForm.elements;
  const name = nickname.value.trim();

  if (name.length < 2 || name.length > 20) return showError(signupForm, '닉네임은 2~20자로 입력해 주세요.');
  if (!EMAIL_PATTERN.test(email.value.trim())) return showError(signupForm, '이메일을 올바르게 입력해 주세요.');
  if (password.value.length < 8) return showError(signupForm, '비밀번호는 8자 이상이어야 해요.');
  if (password.value !== passwordConfirm.value) return showError(signupForm, '비밀번호 확인이 맞지 않아요.');
  if (!agreeTerms.checked || !agreePrivacy.checked || !over14.checked) {
    return showError(signupForm, '필수 항목에 모두 동의해 주세요.');
  }

  submitWith(signupForm, () => Auth.signUp({
    nickname: name,
    email: email.value,
    password: password.value,
    agreeTerms: agreeTerms.checked,
    agreePrivacy: agreePrivacy.checked,
    over14: over14.checked,
  }), () => showVerificationSent(email.value.trim()));
});

// 이미 로그인했으면 돌아갈 곳으로 보낸다
Auth.currentUser().then((user) => {
  if (user) location.replace(next);
});
if (params.get('tab') === 'signup') showTab('signup');
if (params.get('verified') === '1') document.getElementById('verified-done').hidden = false;
