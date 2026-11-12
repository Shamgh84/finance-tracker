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

function formatMoney(value) {
  return Number(value).toLocaleString('fa-IR', { maximumFractionDigits: 0 });
}

// تاریخ میلادی (YYYY-MM-DD) را به شمسی نمایش می‌دهد
function formatDate(iso) {
  if (!iso) return '';
  const [year, month, day] = iso.split('-').map(Number);
  return new Date(year, month - 1, day).toLocaleDateString('fa-IR');
}