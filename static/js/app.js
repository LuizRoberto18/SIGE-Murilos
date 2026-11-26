(() => {
  const body = document.body;
  const menuButton = document.querySelector('[data-menu-toggle]');
  const backdrop = document.querySelector('[data-menu-backdrop]');
  const sidebar = document.querySelector('.sidebar');

  const setMenu = (open) => {
    body.classList.toggle('nav-open', open);
    menuButton?.setAttribute('aria-expanded', String(open));
  };

  menuButton?.addEventListener('click', () => setMenu(!body.classList.contains('nav-open')));
  backdrop?.addEventListener('click', () => setMenu(false));
  sidebar?.addEventListener('click', (event) => {
    if (event.target.closest('a') && window.innerWidth < 992) setMenu(false);
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') setMenu(false);
  });

  const currentPath = window.location.pathname.replace(/\/$/, '') || '/';
  const matchingLinks = [...document.querySelectorAll('.sidebar a[href]')].filter((link) => {
    const path = new URL(link.href, window.location.origin).pathname.replace(/\/$/, '') || '/';
    return path === currentPath || (path !== '/' && currentPath.startsWith(`${path}/`));
  }).sort((first, second) => second.pathname.length - first.pathname.length);
  const activeLink = matchingLinks[0];
  if (activeLink) {
    activeLink.classList.add('active');
    activeLink.setAttribute('aria-current', 'page');
  }

  const dashboardTabs = document.querySelector('[data-dashboard-tabs]');
  if (dashboardTabs) {
    const tabs = [...dashboardTabs.querySelectorAll('[data-dashboard-tab]')];
    const panels = [...document.querySelectorAll('[data-dashboard-panel]')];
    const availableTabs = tabs.map((tab) => tab.dataset.dashboardTab);

    const showDashboardPanel = (name, moveFocus = false) => {
      if (!availableTabs.includes(name)) return;
      tabs.forEach((tab) => {
        const selected = tab.dataset.dashboardTab === name;
        tab.setAttribute('aria-selected', String(selected));
        tab.tabIndex = selected ? 0 : -1;
        if (selected && moveFocus) tab.focus();
      });
      panels.forEach((panel) => {
        panel.hidden = panel.dataset.dashboardPanel !== name;
      });
      window.history.replaceState(null, '', `#${name}`);
    };

    dashboardTabs.classList.add('dashboard-tabs-ready');
    const initialTab = availableTabs.includes(window.location.hash.slice(1)) ? window.location.hash.slice(1) : 'vendas';
    showDashboardPanel(initialTab);
    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => showDashboardPanel(tab.dataset.dashboardTab));
      tab.addEventListener('keydown', (event) => {
        if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
        event.preventDefault();
        const offset = event.key === 'ArrowRight' ? 1 : -1;
        const nextIndex = (index + offset + tabs.length) % tabs.length;
        showDashboardPanel(tabs[nextIndex].dataset.dashboardTab, true);
      });
    });
  }

  document.querySelectorAll('form input:not([type="checkbox"]):not([type="radio"]):not([type="hidden"]), form select, form textarea').forEach((control) => {
    if (control.tagName === 'SELECT') control.classList.add('form-select');
    else control.classList.add('form-control');
  });

  document.querySelectorAll('input[type="number"]').forEach((input) => {
    input.inputMode = input.step === '1' ? 'numeric' : 'decimal';
  });

  document.addEventListener('input', (event) => {
    const input = event.target.closest?.('input[type="number"]');
    if (input) input.dataset.numberEdited = 'true';
  });
  document.addEventListener('focusout', (event) => {
    const input = event.target.closest?.('input[type="number"]');
    if (!input || input.dataset.numberEdited !== 'true') return;
    if (!input.step || input.step === '1' || input.step === 'any' || input.value === '') return;
    const value = Number(input.value);
    if (!Number.isFinite(value)) return;
    input.value = value.toFixed(2).replace(/\.00$/, '').replace(/(\.\d)0$/, '$1');
    delete input.dataset.numberEdited;
  });
})();
