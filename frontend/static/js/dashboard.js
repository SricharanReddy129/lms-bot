/* ── Helpers ── */
function emptyState(message) {
  return `<p class="text-muted text-center py-3">${message}</p>`;
}

function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '--';
}

function capitalize(str) {
  return str ? str.charAt(0).toUpperCase() + str.slice(1) : '--';
}

function buildTable(headers, rows) {
  if (!rows.length) return emptyState('No records found.');

  const ths = headers.map(h => `<th>${h}</th>`).join('');
  const trs = rows.map(cells => {
    const tds = cells.map(c => `<td>${c ?? '--'}</td>`).join('');
    return `<tr>${tds}</tr>`;
  }).join('');

  return `
    <div class="card shadow-sm">
      <div class="card-body p-0">
        <table class="table table-hover mb-0">
          <thead class="table-dark"><tr>${ths}</tr></thead>
          <tbody>${trs}</tbody>
        </table>
      </div>
    </div>`;
}

/* ── Section navigation ── */
const sectionLoaders = {
  'balance':      loadBalance,
  'apply':        () => {},          // form is static
  'pending':      loadMyPending,
  'holidays':     loadHolidays,
  'history':      () => loadHistory('approved'),
  'team-pending': loadTeamPending,
  'approve':      loadApproveReject,
};

function navigateToSection(sectionId) {
  document.querySelectorAll('.content-section').forEach(s => s.classList.add('d-none'));
  const target = document.getElementById('section-' + sectionId);
  if (target) target.classList.remove('d-none');

  document.querySelectorAll('[data-section]').forEach(link => {
    link.classList.toggle('active', link.dataset.section === sectionId);
  });

  const loader = sectionLoaders[sectionId];
  if (loader) loader();
}

/* ── Data loaders ── */
async function loadBalance() {
  try {
    const data = await apiFetch('/api/v1/leaves/balance');
    document.getElementById('bal-earned').textContent   = data.earned_leaves   ?? '--';
    document.getElementById('bal-sick').textContent     = data.sick_leaves     ?? '--';
    document.getElementById('bal-parental').textContent = data.parental_leaves ?? '--';
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

async function loadHolidays() {
  try {
    const data = await apiFetch('/api/v1/holidays');
    const tbody = document.getElementById('holidays-tbody');
    if (!data.length) {
      tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted py-3">No holidays found.</td></tr>';
      return;
    }
    tbody.innerHTML = data.map(h => `
      <tr>
        <td class="ps-3">${h.sno}</td>
        <td>${h.holiday_name}</td>
        <td>${formatDate(h.holiday_date)}</td>
      </tr>`).join('');
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

async function loadMyPending() {
  try {
    const data = await apiFetch('/api/v1/leaves/pending');
    const container = document.getElementById('pending-table-container');
    container.innerHTML = buildTable(
      ['Leave ID', 'Type', 'Start Date', 'End Date', 'Reason'],
      data.map(r => [
        r.leave_id,
        capitalize(r.leave_type),
        formatDate(r.start_date),
        formatDate(r.end_date),
        r.reason || '—',
      ])
    );
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

async function loadTeamPending() {
  try {
    const data = await apiFetch('/api/v1/leaves/pending');
    const container = document.getElementById('team-pending-container');
    container.innerHTML = buildTable(
      ['Employee', 'Type', 'Start Date', 'End Date', 'Reason'],
      data.map(r => [
        r.employee_name,
        capitalize(r.leave_type),
        formatDate(r.start_date),
        formatDate(r.end_date),
        r.reason || '—',
      ])
    );
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

async function loadApproveReject() {
  try {
    const data = await apiFetch('/api/v1/leaves/pending');
    const container = document.getElementById('approve-reject-container');

    if (!data.length) {
      container.innerHTML = emptyState('No pending leaves to action.');
      return;
    }

    const rows = data.map(r => `
      <tr>
        <td class="ps-3">
          <input type="checkbox" class="form-check-input leave-checkbox"
                 data-leave-id="${r.leave_id}" data-employee="${r.employee_name}">
        </td>
        <td>${r.leave_id}</td>
        <td>${r.employee_name}</td>
        <td>${capitalize(r.leave_type)}</td>
        <td>${formatDate(r.start_date)}</td>
        <td>${formatDate(r.end_date)}</td>
        <td>${r.reason || '—'}</td>
      </tr>`).join('');

    container.innerHTML = `
      <div class="card shadow-sm">
        <div class="card-body p-0">
          <table class="table table-hover mb-0">
            <thead class="table-dark">
              <tr>
                <th class="ps-3"></th>
                <th>Leave ID</th><th>Employee</th><th>Type</th>
                <th>Start</th><th>End</th><th>Reason</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      </div>`;
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

function collectSelectedLeaves() {
  const checked = document.querySelectorAll('.leave-checkbox:checked');
  if (!checked.length) {
    showToast('Please select at least one leave.', 'warning');
    return null;
  }
  return Array.from(checked).map(cb => ({
    leave_id: parseInt(cb.dataset.leaveId),
    employee: cb.dataset.employee,
  }));
}

async function approveLeaves(leaveIds) {
  const btn = document.getElementById('btn-bulk-approve');
  btn.disabled = true;
  btn.textContent = 'Processing…';
  try {
    const res = await apiFetch('/api/v1/leaves/approve', {
      method: 'POST',
      body: JSON.stringify({ leave_ids: leaveIds }),
    });
    showToast(res.message || 'Leaves approved successfully.', 'success');
    loadApproveReject();
  } catch (err) {
    showToast(err.message, 'danger');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-check-lg me-1"></i> Approve Selected';
  }
}

function openRejectModal(leaves) {
  const list = document.getElementById('rejection-reasons-list');
  list.innerHTML = leaves.map(l => `
    <div class="mb-3">
      <label class="form-label fw-semibold">
        Leave #${l.leave_id} — ${l.employee}
      </label>
      <textarea class="form-control reject-reason"
                data-leave-id="${l.leave_id}"
                rows="2"
                placeholder="Reason for rejection…"
                required></textarea>
    </div>`).join('');

  const modal = new bootstrap.Modal(document.getElementById('rejectModal'));
  modal.show();
}

async function confirmReject() {
  const textareas = document.querySelectorAll('.reject-reason');
  const rejections = [];
  let valid = true;

  textareas.forEach(ta => {
    const reason = ta.value.trim();
    if (!reason) {
      valid = false;
      ta.classList.add('is-invalid');
    } else {
      ta.classList.remove('is-invalid');
      rejections.push({ leave_id: parseInt(ta.dataset.leaveId), reason });
    }
  });

  if (!valid) {
    showToast('Please provide a reason for every selected leave.', 'warning');
    return;
  }

  const btn = document.getElementById('confirm-reject-btn');
  btn.disabled = true;
  btn.textContent = 'Processing…';

  try {
    const res = await apiFetch('/api/v1/leaves/reject', {
      method: 'PUT',
      body: JSON.stringify({ rejections }),
    });

    bootstrap.Modal.getInstance(document.getElementById('rejectModal')).hide();
    showToast(res.message || 'Leaves rejected successfully.', 'success');
    loadApproveReject();
  } catch (err) {
    showToast(err.message, 'danger');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Confirm Rejection';
  }
}

async function loadHistory(tab) {
  const approvedContainer = document.getElementById('history-approved-container');
  const rejectedContainer = document.getElementById('history-rejected-container');

  document.getElementById('tab-approved').classList.toggle('active', tab === 'approved');
  document.getElementById('tab-rejected').classList.toggle('active', tab === 'rejected');
  approvedContainer.classList.toggle('d-none', tab !== 'approved');
  rejectedContainer.classList.toggle('d-none', tab !== 'rejected');

  try {
    if (tab === 'approved') {
      const data = await apiFetch('/api/v1/leaves/history/approved');
      approvedContainer.innerHTML = buildTable(
        ['Employee', 'Type', 'Start Date', 'End Date'],
        (data.data || []).map(r => [
          r.employee_name,
          capitalize(r.leave_type),
          formatDate(r.start_date),
          formatDate(r.end_date),
        ])
      );
    } else {
      const data = await apiFetch('/api/v1/leaves/history/rejected');
      rejectedContainer.innerHTML = buildTable(
        ['Employee', 'Type', 'Start Date', 'End Date', 'Your Reason', 'Rejection Reason'],
        (data.data || []).map(r => [
          r.employee_name,
          capitalize(r.leave_type),
          formatDate(r.start_date),
          formatDate(r.end_date),
          r.applicant_reason || '—',
          r.approver_reason,
        ])
      );
    }
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

/* ── Init ── */
document.addEventListener('DOMContentLoaded', function () {
  if (!requireAuth()) return;

  const user = getUser();

  document.getElementById('user-name-display').textContent = 'Hello, ' + user.name;

  const badge = document.getElementById('user-role-badge');
  if (user.role === 'approver') {
    badge.textContent = 'Manager';
    badge.classList.add('bg-warning', 'text-dark');
    document.getElementById('nav-team-pending').classList.remove('d-none');
    document.getElementById('nav-approve').classList.remove('d-none');
  } else {
    badge.textContent = 'Employee';
    badge.classList.add('bg-secondary');
  }

  // Nav click handlers
  document.querySelectorAll('[data-section]').forEach(link => {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      navigateToSection(this.dataset.section);
    });
  });

  // History tabs
  document.getElementById('tab-approved').addEventListener('click', function (e) {
    e.preventDefault();
    loadHistory('approved');
  });
  document.getElementById('tab-rejected').addEventListener('click', function (e) {
    e.preventDefault();
    loadHistory('rejected');
  });

  // Apply leave form
  document.getElementById('apply-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    const startVal  = document.getElementById('apply-start').value;
    const endVal    = document.getElementById('apply-end').value;
    const typeVal   = document.getElementById('apply-type').value;
    const reasonVal = document.getElementById('apply-reason').value.trim();
    const alertEl   = document.getElementById('apply-alert');
    const btn       = document.getElementById('apply-btn');

    if (endVal < startVal) {
      alertEl.className = 'alert alert-danger py-2 mb-3';
      alertEl.textContent = 'End date must be on or after start date.';
      return;
    }

    alertEl.classList.add('d-none');
    btn.disabled = true;
    btn.textContent = 'Submitting…';

    try {
      const res = await apiFetch('/api/v1/leaves/apply', {
        method: 'POST',
        body: JSON.stringify({
          start_date: startVal,
          end_date:   endVal,
          leave_type: typeVal,
          reason:     reasonVal || null,
        }),
      });
      alertEl.className = 'alert alert-success py-2 mb-3';
      alertEl.textContent = res.status || 'Application submitted successfully.';
      document.getElementById('apply-form').reset();
    } catch (err) {
      alertEl.className = 'alert alert-danger py-2 mb-3';
      alertEl.textContent = err.message;
    } finally {
      btn.disabled = false;
      btn.textContent = 'Submit Application';
    }
  });

  // Approve / Reject buttons
  document.getElementById('btn-bulk-approve').addEventListener('click', function () {
    const leaves = collectSelectedLeaves();
    if (!leaves) return;
    approveLeaves(leaves.map(l => l.leave_id));
  });

  document.getElementById('btn-bulk-reject').addEventListener('click', function () {
    const leaves = collectSelectedLeaves();
    if (!leaves) return;
    openRejectModal(leaves);
  });

  document.getElementById('confirm-reject-btn').addEventListener('click', confirmReject);

  // Default section
  navigateToSection('balance');
});
