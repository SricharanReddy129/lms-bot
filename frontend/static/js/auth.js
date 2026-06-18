/* ── Token storage ── */
function getToken() {
  return localStorage.getItem('lms_token');
}

function getUser() {
  const raw = localStorage.getItem('lms_user');
  return raw ? JSON.parse(raw) : null;
}

function saveSession(data) {
  localStorage.setItem('lms_token', data.access_token);
  localStorage.setItem('lms_user', JSON.stringify({
    employee_id: data.employee_id,
    name: data.name,
    role: data.role,
  }));
}

function clearSession() {
  localStorage.removeItem('lms_token');
  localStorage.removeItem('lms_user');
}

function requireAuth() {
  if (!getToken()) {
    window.location.href = '/';
    return false;
  }
  return true;
}

/* ── Fetch wrapper ── */
function authHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + getToken(),
  };
}

async function apiFetch(path, options = {}) {
  const merged = {
    ...options,
    headers: { ...authHeaders(), ...(options.headers || {}) },
  };
  const response = await fetch(path, merged);

  if (response.status === 401) {
    clearSession();
    window.location.href = '/';
    throw new Error('Session expired');
  }

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || 'Request failed');
  }

  return data;
}

/* ── Toast notifications ── */
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const bgClass = type === 'success' ? 'bg-success'
                : type === 'danger'  ? 'bg-danger'
                : type === 'warning' ? 'bg-warning text-dark'
                : 'bg-secondary';

  const id = 'toast-' + Date.now();
  const html = `
    <div id="${id}" class="toast align-items-center text-white ${bgClass} border-0" role="alert">
      <div class="d-flex">
        <div class="toast-body">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    </div>`;

  container.insertAdjacentHTML('beforeend', html);
  const el = document.getElementById(id);
  const toast = new bootstrap.Toast(el, { delay: 3500 });
  toast.show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
}

/* ── Auth guard + logout (runs on every page) ── */
(function () {
  const path = window.location.pathname;
  const isLoginPage = path === '/' || path === '/login';

  if (isLoginPage) {
    if (getToken()) window.location.href = '/dashboard';
  } else {
    if (!getToken()) window.location.href = '/';
  }

  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      clearSession();
      window.location.href = '/';
    });
  }
})();
