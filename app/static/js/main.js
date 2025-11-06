(function () {
  'use strict';

  // Update footer year
  document.addEventListener('DOMContentLoaded', function () {
    const yearEl = document.getElementById('year');
    if (yearEl) yearEl.textContent = new Date().getFullYear();

    // Auto-dismiss flash messages after 5 seconds
    const alerts = document.querySelectorAll('#flash-container .alert');
    alerts.forEach((alert) => {
      setTimeout(() => {
        const alertInstance = bootstrap.Alert.getOrCreateInstance(alert);
        alertInstance.close();
      }, 5000);
    });

    // Enable tooltips & popovers
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
      return new bootstrap.Popover(popoverTriggerEl);
    });
  });

  // Confirmation helper
  window.showConfirmModal = function (title, message, onConfirm, confirmText) {
    const modalEl = document.getElementById('confirmModal');
    if (!modalEl) { return window.confirm(message || title); }
    const titleEl = modalEl.querySelector('#confirmModalTitle');
    const msgEl = modalEl.querySelector('#confirmModalMessage');
    const btn = modalEl.querySelector('#confirmModalBtn');
    if (titleEl && title) titleEl.textContent = title;
    if (msgEl && message) msgEl.textContent = message;
    if (btn && confirmText) btn.textContent = confirmText;
    const m = bootstrap.Modal.getOrCreateInstance(modalEl);
    const handler = function () {
      try { onConfirm && onConfirm(); } catch (e) { console.error(e); }
      btn.removeEventListener('click', handler);
      m.hide();
    };
    btn.addEventListener('click', handler, { once: true });
    m.show();
    return false;
  };

  // Back-compat wrapper
  window.confirmAction = function (message, onConfirm) {
    return window.showConfirmModal('Confirm', message, onConfirm, 'Confirm');
  };

  // Loading overlay helpers
  window.showLoading = function (message) {
    const ov = document.getElementById('loading-overlay');
    if (!ov) return;
    const txt = document.getElementById('loading-overlay-text');
    if (txt && message) txt.textContent = message;
    ov.classList.remove('d-none');
    document.body.setAttribute('aria-busy', 'true');
  };
  window.hideLoading = function () {
    const ov = document.getElementById('loading-overlay');
    if (!ov) return;
    ov.classList.add('d-none');
    document.body.removeAttribute('aria-busy');
  };

  // ===== Circulation helpers =====
  window.clearCirculationFilters = function () {
    const url = new URL(window.location.href);
    url.searchParams.delete('query');
    url.searchParams.delete('status');
    url.searchParams.delete('member_id');
    url.searchParams.delete('page');
    window.location.href = url.pathname;
  };

  // ===== Members helpers =====
  window.confirmStatusChange = function (memberId, currentStatus, newStatus) {
    const friendly = {
      active: 'Activate',
      suspended: 'Suspend',
      expired: 'Mark as Expired',
    };
    const action = friendly[newStatus] || ('Change to ' + newStatus);
    let extra = '';
    if (newStatus === 'suspended') extra = '\nThis will prevent the member from borrowing books.';
    if (newStatus === 'expired') extra = '\nThe member will need to renew to borrow again.';
    const msg = `${action} member ${memberId}?\n(Current: ${currentStatus})${extra}`;
    return window.showConfirmModal('Confirm Status Change', msg, null, 'Confirm');
  };

  window.copyMemberIdToClipboard = function (memberId) {
    if (!navigator.clipboard) return false;
    navigator.clipboard.writeText(memberId).then(function () {
      // Optionally show a quick tooltip/alert
    }).catch(function (e) { console.error(e); });
    return true;
  };

  window.clearMembersFilters = function () {
    const url = new URL(window.location.href);
    url.searchParams.delete('query');
    url.searchParams.delete('status');
    url.searchParams.delete('page');
    window.location.href = url.pathname;
  };

  // ===== Auth helpers =====
  window.togglePasswordVisibility = function (fieldId) {
    const input = document.getElementById(fieldId);
    if (!input) return;
    const isPassword = input.getAttribute('type') === 'password';
    input.setAttribute('type', isPassword ? 'text' : 'password');
  };

  function passwordStrengthScore(pwd) {
    let score = 0;
    if (!pwd) return 0;
    if (pwd.length >= 8) score += 1;
    if (/[A-Z]/.test(pwd)) score += 1;
    if (/[a-z]/.test(pwd)) score += 1;
    if (/\d/.test(pwd)) score += 1;
    if (/[^A-Za-z0-9]/.test(pwd)) score += 1;
    return Math.min(score, 5);
  }

  document.addEventListener('DOMContentLoaded', function () {
    // Autofocus first input in auth forms
    const firstInput = document.querySelector('form input[autofocus]');
    if (firstInput) firstInput.focus();

    // Register page password strength
    const regPwd = document.getElementById('reg_password');
    const bar = document.getElementById('pwdStrengthBar');
    const text = document.getElementById('pwdStrengthText');
    if (regPwd && bar && text) {
      regPwd.addEventListener('input', function () {
        const score = passwordStrengthScore(regPwd.value);
        const pct = (score / 5) * 100;
        bar.style.width = pct + '%';
        let cls = 'bg-danger', label = 'Weak';
        if (score >= 4) { cls = 'bg-success'; label = 'Strong'; }
        else if (score === 3) { cls = 'bg-warning'; label = 'Medium'; }
        bar.className = 'progress-bar ' + cls;
        text.textContent = label;
      });
    }
  });

  // Preserve scroll position across pagination
  document.addEventListener('click', function (e) {
    const target = e.target.closest('.pagination a.page-link');
    if (target) {
      sessionStorage.setItem('scrollYBeforePageChange', String(window.scrollY));
    }
  });

  document.addEventListener('DOMContentLoaded', function () {
    const saved = sessionStorage.getItem('scrollYBeforePageChange');
    if (saved) {
      sessionStorage.removeItem('scrollYBeforePageChange');
      window.scrollTo({ top: parseInt(saved, 10) || 0, behavior: 'instant' });
    }
    // Initialize tooltips for disabled buttons
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
  });

  // Form loading/validation hooks
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('form.needs-loading').forEach(function (form) {
      form.addEventListener('submit', function () {
        const btn = form.querySelector('button[type="submit"], input[type="submit"]');
        if (btn) {
          btn.setAttribute('disabled', 'disabled');
          const spinner = btn.querySelector('.spinner-border');
          const text = btn.querySelector('.btn-text');
          if (spinner) spinner.classList.remove('d-none');
          if (text) text.textContent = (btn.getAttribute('data-loading-text') || 'Processing...');
        }
        window.showLoading();
      });
    });

    document.querySelectorAll('form.needs-validation').forEach(function (form) {
      form.setAttribute('novalidate', 'novalidate');
      form.addEventListener('submit', function (e) {
        if (!form.checkValidity()) {
          e.preventDefault();
          e.stopPropagation();
          form.classList.add('was-validated');
          const firstInvalid = form.querySelector(':invalid');
          if (firstInvalid) { firstInvalid.focus(); firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
        }
      });
      form.addEventListener('input', function (e) {
        const el = e.target;
        if (!(el instanceof HTMLElement)) return;
        if (el.checkValidity()) { el.classList.remove('is-invalid'); el.classList.add('is-valid'); }
        else { el.classList.remove('is-valid'); /* don't force invalid on each keystroke */ }
      }, true);
      form.addEventListener('blur', function (e) {
        const el = e.target;
        if (!(el instanceof HTMLElement)) return;
        if (el.checkValidity()) { el.classList.add('is-valid'); el.classList.remove('is-invalid'); }
        else { el.classList.add('is-invalid'); el.classList.remove('is-valid'); }
      }, true);
    });

    const amtInput = document.getElementById('payment_amount');
    if (!amtInput) return;
    const max = parseFloat(amtInput.closest('form')?.querySelector('.form-text')?.textContent?.replace(/[^0-9.]/g, '') || '0');
    amtInput.addEventListener('input', function () {
      const ok = window.validatePaymentAmount(amtInput.value, max);
      if (!ok) {
        amtInput.classList.add('is-invalid');
      } else {
        amtInput.classList.remove('is-invalid');
      }
    });

    // Confirm on submit using data attributes
    const form = amtInput.closest('form');
    if (form) {
      form.addEventListener('submit', function (e) {
        const loanId = form.getAttribute('data-loan-id');
        const balance = parseFloat(form.getAttribute('data-balance') || '0');
        const amount = parseFloat(amtInput.value || '0');
        if (!window.validatePaymentAmount(amount, balance)) {
          e.preventDefault();
          amtInput.classList.add('is-invalid');
          return false;
        }
        const ok = window.confirmFinePayment(loanId, amount, balance);
        if (!ok) {
          e.preventDefault();
          return false;
        }
        return true;
      });
    }
  });

  // ===== Reports helpers =====
  window.getChartColors = function (count) {
    const base = ['#0d6efd', '#198754', '#ffc107', '#dc3545', '#0dcaf0', '#6c757d'];
    if (count <= base.length) return base.slice(0, count);
    const extra = [];
    for (let i = 0; i < count - base.length; i++) {
      const hue = Math.floor((360 / Math.max(1, count)) * i);
      extra.push(`hsl(${hue}, 65%, 55%)`);
    }
    return base.concat(extra);
  };

  window.clearDateRange = function () {
    const s = document.getElementById('start_date');
    const e = document.getElementById('end_date');
    if (s) s.value = '';
    if (e) e.value = '';
    const form = (s && s.form) || (e && e.form) || document.querySelector('.date-range-form');
    if (form) form.submit();
  };

  window.confirmExport = function (format, reportName) {
    const msg = `Export ${reportName} as ${format}?`;
    return window.confirm(msg);
  };

  window.initResponsiveCharts = function () {
    let timer = null;
    window.addEventListener('resize', function () {
      if (timer) clearTimeout(timer);
      timer = setTimeout(function () {
        // Chart.js is responsive by default; this is a placeholder for any custom handling.
      }, 300);
    });
  };

  window.printReport = function () { window.print(); };

  window.formatChartData = function (data, type) {
    if (!data) return { labels: [], datasets: [] };
    const colors = window.getChartColors(1);
    const ds = [{ label: (type || 'Series'), data: data.values || [], borderColor: colors[0], backgroundColor: colors[0] }];
    return { labels: data.labels || [], datasets: ds };
  };

})();
