(function () {
  const LANG_KEY = 'ppc_lang';
  const SUPPORTED = ['en', 'uk', 'ru'];

  function t(lang, key) {
    const parts = key.split('.');
    let obj = translations[lang] || translations.en;
    for (const p of parts) {
      if (obj == null) return null;
      obj = obj[p];
    }
    if (obj == null && lang !== 'en') return t('en', key);
    return (typeof obj === 'string') ? obj : null;
  }

  const NAV_MAP = {
    'index.html': 'nav.home', 'services.html': 'nav.services',
    'cases.html': 'nav.cases', 'blog.html': 'nav.blog',
    'resources.html': 'nav.resources', 'contact.html': 'nav.cta'
  };
  const FOOTER_MAP = {
    'services.html': 'footer_links.services', 'cases.html': 'footer_links.cases',
    'resources.html': 'footer_links.resources', 'contact.html': 'footer_links.contact',
    'blog.html': 'footer_links.blog'
  };

  function applyLang(lang) {
    if (!SUPPORTED.includes(lang)) lang = 'en';
    document.documentElement.lang = lang;
    localStorage.setItem(LANG_KEY, lang);

    // Text replacements
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const val = t(lang, el.getAttribute('data-i18n'));
      if (val != null) el.textContent = val;
    });

    // HTML replacements (for elements with <strong> etc.)
    document.querySelectorAll('[data-i18n-html]').forEach(el => {
      const val = t(lang, el.getAttribute('data-i18n-html'));
      if (val != null) el.innerHTML = val;
    });

    // Placeholder replacements
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
      const val = t(lang, el.getAttribute('data-i18n-ph'));
      if (val != null) el.placeholder = val;
    });

    // Nav links by href
    document.querySelectorAll('.nav-links a').forEach(a => {
      const key = NAV_MAP[a.getAttribute('href')];
      if (key) { const v = t(lang, key); if (v) a.textContent = v; }
    });

    // Footer links by href
    document.querySelectorAll('.footer-links a').forEach(a => {
      const key = FOOTER_MAP[a.getAttribute('href')];
      if (key) { const v = t(lang, key); if (v) a.textContent = v; }
    });

    // Article "Back to Blog" links
    document.querySelectorAll('[data-i18n-back]').forEach(el => {
      const v = t(lang, 'article.back'); if (v) el.textContent = v;
    });

    // Article language notice
    const notice = document.getElementById('lang-notice');
    if (notice) {
      const msg = t(lang, 'article.notice');
      notice.textContent = (lang !== 'en' && msg) ? msg : '';
      notice.style.display = (lang !== 'en' && msg) ? 'block' : 'none';
    }

    // Footer copyright specialist label
    document.querySelectorAll('.footer-copy').forEach(el => {
      const v = t(lang, 'footer.specialist');
      if (v) el.textContent = '© 2026 Max Tokarev. ' + v;
    });

    // Lang button active state
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
    });
  }

  function init() {
    applyLang(localStorage.getItem(LANG_KEY) || 'en');
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.addEventListener('click', function () { applyLang(this.getAttribute('data-lang')); });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
