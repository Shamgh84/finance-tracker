// ---------- مدیریت توکن‌ها ----------
const Auth = {
  get access() { return localStorage.getItem('access_token'); },
  get refresh() { return localStorage.getItem('refresh_token'); },

  save(tokens) {
    if (tokens.access) localStorage.setItem('access_token', tokens.access);
    if (tokens.refresh) localStorage.setItem('refresh_token', tokens.refresh);
  },

  clear() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  logout() {
    Auth.clear();
    window.location.href = '/login/';
  },

  requireLogin() {
    if (!Auth.refresh) window.location.href = '/login/';
  },
};

async function refreshAccessToken() {
  if (!Auth.refresh) return false;
  const res = await fetch('/api/auth/token/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: Auth.refresh }),
  });
  if (!res.ok) return false;
  Auth.save(await res.json());
  return true;
}

// ---------- درخواست به API (با توکن و تمدید خودکار) ----------
async function apiFetch(url, options = {}) {
  const build = () => ({
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
      ...(Auth.access ? { Authorization: `Bearer ${Auth.access}` } : {}),
    },
  });

  let res = await fetch(url, build());
  if (res.status === 401 && (await refreshAccessToken())) {
    res = await fetch(url, build());
  }
  if (res.status === 401) {
    Auth.logout();
    throw new Error('unauthorized');
  }
  return res;
}

// ---------- ابزارهای نمایش خطا ----------
const FIELD_LABELS = {
  username: 'نام کاربری',
  email: 'ایمیل',
  password: 'رمز عبور',
  password2: 'تکرار رمز عبور',
  category: 'دسته',
  amount: 'مبلغ',
  date: 'تاریخ',
  description: 'توضیحات',
  year: 'سال',
  month: 'ماه',
  limit_amount: 'سقف بودجه',
  alert_threshold: 'درصد هشدار',
  non_field_errors: '',
};

function formatErrors(data) {
  if (!data || typeof data !== 'object') return 'خطای نامشخصی رخ داد.';
  if (typeof data.detail === 'string') return data.detail;
  return Object.entries(data)
    .map(([field, value]) => {
      const message = Array.isArray(value) ? value.join(' ') : String(value);
      const label = FIELD_LABELS[field];
      return label ? `${label}: ${message}` : message;
    })
    .join('\n');
}

function showError(element, message) {
  element.textContent = message;
  element.classList.remove('hidden');
}

function hideError(element) {
  element.textContent = '';
  element.classList.add('hidden');
}

// ---------- ابزارهای عمومی ----------
const $ = (id) => document.getElementById(id);

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text ?? '';
  return div.innerHTML;
}

// واحد پول؛ برای ریال، مقدار زیر را به 'ریال' تغییر بده
const CURRENCY = 'تومان';

function formatMoney(value) {
  const number = Number(value).toLocaleString('fa-IR', { maximumFractionDigits: 0 });
  return `${number} ${CURRENCY}`;
}

// تاریخ میلادی (YYYY-MM-DD) را به شمسی نمایش می‌دهد
function formatDate(iso) {
  if (!iso) return '';
  const [year, month, day] = iso.split('-').map(Number);
  return new Date(year, month - 1, day).toLocaleDateString('fa-IR');
}

// ---------- فیلد مبلغ با جداکننده‌ی هزارگان ----------
function normalizeDigits(text) {
  return String(text)
    .replace(/[۰-۹]/g, (d) => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d))
    .replace(/[٠-٩]/g, (d) => '٠١٢٣٤٥٦٧٨٩'.indexOf(d));
}

function bindMoneyInput(input) {
  const native = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value');
  const digitsOf = (text) => normalizeDigits(text).split('.')[0].replace(/\D/g, '');
  const show = (digits) => digits.replace(/\B(?=(\d{3})+(?!\d))/g, ',');

  // خواندن مقدار فقط رقم‌ها را می‌دهد و نوشتن مقدار، آن را با جداکننده نشان می‌دهد
  Object.defineProperty(input, 'value', {
    configurable: true,
    get() { return digitsOf(native.get.call(input)); },
    set(v) { native.set.call(input, show(digitsOf(v))); },
  });
  input.addEventListener('input', () => {
    native.set.call(input, show(digitsOf(native.get.call(input))));
  });
}

document.querySelectorAll('input[data-money]').forEach(bindMoneyInput);

// ---------- پیام‌های شناور (جایگزین alert) ----------
function toast(message, type = 'info') {
  let box = document.getElementById('toast-box');
  if (!box) {
    box = document.createElement('div');
    box.id = 'toast-box';
    document.body.appendChild(box);
  }
  const item = document.createElement('div');
  item.className = `toast toast-${type}`;
  item.textContent = message;
  box.appendChild(item);
  setTimeout(() => {
    item.classList.add('toast-out');
    setTimeout(() => item.remove(), 300);
  }, 3500);
}

// همه‌ی alertهای برنامه از این به بعد به صورت پیام شناور نمایش داده می‌شوند
window.alert = (message) => toast(message, 'error');

// ---------- نمایش و پنهان کردن رمز عبور (آیکون چشم) ----------
const EYE_PATHS = "<path d='M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z'/><circle cx='12' cy='12' r='3'/>";
const EYE_ICON =
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${EYE_PATHS}</svg>`;
const EYE_OFF_ICON =
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${EYE_PATHS}<line x1="3" y1="3" x2="21" y2="21"/></svg>`;

function addPasswordToggles() {
  document.querySelectorAll('input[type="password"]').forEach((input) => {
    if (input.dataset.toggleAdded) return;
    input.dataset.toggleAdded = '1';

    const wrapper = document.createElement('div');
    wrapper.className = 'password-field';
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'password-toggle';
    button.setAttribute('aria-label', 'نمایش رمز عبور');
    button.innerHTML = EYE_ICON;
    button.addEventListener('click', () => {
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      button.innerHTML = show ? EYE_OFF_ICON : EYE_ICON;
      button.setAttribute('aria-label', show ? 'پنهان کردن رمز عبور' : 'نمایش رمز عبور');
    });
    wrapper.appendChild(button);
  });
}

addPasswordToggles();
// ---------- حالت شب ----------
const THEME_ICONS = {
  moon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>',
  sun: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>',
};

function currentTheme() {
  return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
}

function updateThemeButtons() {
  const dark = currentTheme() === 'dark';
  document.querySelectorAll('.theme-toggle').forEach((button) => {
    button.innerHTML = dark ? THEME_ICONS.sun : THEME_ICONS.moon;
    button.setAttribute('aria-label', dark ? 'حالت روز' : 'حالت شب');
    button.title = dark ? 'حالت روز' : 'حالت شب';
  });
}

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  try { localStorage.setItem('theme', theme); } catch (error) { /* ذخیره نشد؛ مهم نیست */ }
  updateThemeButtons();
  window.dispatchEvent(new CustomEvent('themechange', { detail: theme }));
}

function initThemeToggle() {
  // در صفحه‌های ورود و ثبت‌نام نوار بالا نیست، پس یک دکمه‌ی شناور می‌گذاریم
  if (!document.querySelector('.theme-toggle') && document.querySelector('.auth-page')) {
    const floating = document.createElement('button');
    floating.type = 'button';
    floating.className = 'theme-toggle theme-float';
    document.body.appendChild(floating);
  }
  document.querySelectorAll('.theme-toggle').forEach((button) => {
    button.addEventListener('click', () => setTheme(currentTheme() === 'dark' ? 'light' : 'dark'));
  });
  updateThemeButtons();
}

initThemeToggle();