(function () {
  const LANG_KEY = 'ppc_lang';
  const SUPPORTED = ['en', 'uk', 'ru'];

  // Resolve dot-path key in translations object
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

  // Nav link href → translation key mapping
  const NAV_MAP = {
    'index.html': 'nav.home',
    'services.html': 'nav.services',
    'cases.html': 'nav.cases',
    'blog.html': 'nav.blog',
    'resources.html': 'nav.resources',
    'contact.html': 'nav.cta'
  };

  function applyLang(lang) {
    if (!SUPPORTED.includes(lang)) lang = 'en';
    document.documentElement.lang = lang;
    localStorage.setItem(LANG_KEY, lang);

    // Generic data-i18n text replacements
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const val = t(lang, el.getAttribute('data-i18n'));
      if (val != null) el.textContent = val;
    });

    // Placeholder replacements
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
      const val = t(lang, el.getAttribute('data-i18n-ph'));
      if (val != null) el.placeholder = val;
    });

    // Nav links by href
    document.querySelectorAll('.nav-links a').forEach(a => {
      const href = a.getAttribute('href');
      const key = NAV_MAP[href];
      if (key) {
        const val = t(lang, key);
        if (val != null) a.textContent = val;
      }
    });

    // Article pages: show language notice if non-English
    const notice = document.getElementById('lang-notice');
    if (notice) {
      const msg = t(lang, 'article.notice');
      if (lang !== 'en' && msg) {
        notice.textContent = msg;
        notice.style.display = 'block';
      } else {
        notice.style.display = 'none';
      }
    }

    // Back to blog link in articles
    document.querySelectorAll('[data-i18n-back]').forEach(el => {
      const val = t(lang, 'article.back');
      if (val != null) el.textContent = val;
    });

    // Active state on lang buttons
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
    });
  }

  function init() {
    const saved = localStorage.getItem(LANG_KEY) || 'en';
    applyLang(saved);
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.addEventListener('click', function () {
        applyLang(this.getAttribute('data-lang'));
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
