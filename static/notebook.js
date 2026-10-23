// One long notebook: every section is a sheet stacked down the page.
// The script only adds conveniences; without it every link still jumps to its section.
(function () {
  var root = document.documentElement;
  root.classList.add('js');
  function arr(x) { return Array.prototype.slice.call(x); }

  // Every page is dated yesterday, from the visitor's own clock (e.g. "Oct 20, 2026").
  var d = new Date();
  d.setDate(d.getDate() - 1);
  var day = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  arr(document.querySelectorAll('.js-date')).forEach(function (el) { el.textContent = day; });

  var tabs = document.getElementById('tabs');
  var sheets = arr(document.querySelectorAll('.book .page'));
  var tabLinks = arr(document.querySelectorAll('[data-tab]'));
  var progress = document.getElementById('progress');
  var toTop = document.getElementById('to-top');
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Smooth scrolling that stops just below the sticky tabs.
  function offset() { return (tabs ? tabs.offsetHeight : 0) + 8; }
  function jump(id, push) {
    var el = document.getElementById(id);
    if (!el) return;
    var y = el.getBoundingClientRect().top + window.pageYOffset - offset();
    window.scrollTo({ top: Math.max(0, y), behavior: reduce ? 'auto' : 'smooth' });
    try { history[push ? 'pushState' : 'replaceState'](null, '', id === 'index' ? location.pathname + location.search : '#' + id); } catch (e) {}
    if (el.matches('.page, article.role')) { el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash'); }
  }
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href^="#"]');
    if (!a) return;
    var id = a.getAttribute('href').slice(1);
    if (!document.getElementById(id)) return;
    e.preventDefault();
    jump(id, true);
  });

  // Which sheet is being read: highlight its tab, keep the tab in view, fill the progress line.
  var current = null;
  function update() {
    var line = offset() + window.innerHeight * 0.25;
    var active = sheets[0];
    sheets.forEach(function (s) { if (s.getBoundingClientRect().top <= line) active = s; });
    var id = active && active.id;
    if (id !== current) {
      current = id;
      tabLinks.forEach(function (a) {
        var on = a.getAttribute('data-tab') === id;
        a.classList.toggle('on', on);
        if (on) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
        if (on && a.parentNode.scrollTo) {
          var p = a.parentNode, x = a.offsetLeft - (p.clientWidth - a.offsetWidth) / 2;
          p.scrollTo({ left: Math.max(0, x), behavior: reduce ? 'auto' : 'smooth' });
        }
      });
    }
    var max = document.documentElement.scrollHeight - window.innerHeight;
    if (progress) progress.style.transform = 'scaleX(' + (max > 0 ? Math.min(1, window.pageYOffset / max) : 0) + ')';
    if (toTop) toTop.classList.toggle('show', window.pageYOffset > window.innerHeight * 0.8);
  }
  var ticking = false;
  window.addEventListener('scroll', function () {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () { ticking = false; update(); });
  }, { passive: true });
  window.addEventListener('resize', update);
  update();

  // Opened with a link like …/#projects or #role-nielsen: land just below the tabs.
  if (location.hash.length > 1) {
    var id = location.hash.slice(1);
    var land = function () {
      var el = document.getElementById(id);
      if (el) window.scrollTo({ top: el.getBoundingClientRect().top + window.pageYOffset - offset(), behavior: 'instant' });
    };
    setTimeout(land, 0);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(land);  // fonts can shift the page
  }

  // Headings get their ink underline drawn as each sheet comes into view.
  if ('IntersectionObserver' in window && !reduce) {
    root.classList.add('ink');
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('drawn'); io.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -15% 0px' });
    arr(document.querySelectorAll('.page > h2')).forEach(function (h) { io.observe(h); });
  }
})();
