// Flows each section into fixed-size notebook pages, like writing in a real notebook:
// every page has the same number of lines, and writing that does not fit carries over to
// the next page as "(contd.)". Wide screens show two facing pages; narrow screens show one.
// Without JavaScript the sections simply stack down the screen.
(function () {
  var root = document.documentElement;
  var book = document.getElementById('book');
  if (!book) return;
  var sources = Array.prototype.slice.call(book.querySelectorAll('.page'));
  if (!sources.length) return;
  root.classList.add('is-book');
  sources.forEach(function (s) { s.classList.add('src'); });

  var U = parseFloat(getComputedStyle(root).getPropertyValue('--u')) || 28;
  var stage = document.createElement('div');
  stage.className = 'stage';
  book.appendChild(stage);
  var barPrev = document.getElementById('bar-prev');
  var barNext = document.getElementById('bar-next');

  var sheets = [];   // every page, in order
  var views = [];    // pages shown together: [[0, 1], [2, 3], ...] or [[0], [1], ...]
  var view = 0;
  var listSeq = 0;

  function linesThatFit() {
    return Math.max(16, Math.min(30, Math.floor((window.innerHeight - 96) / U)));
  }
  function isSpread() { return window.innerWidth >= 1100; }
  function arr(x) { return Array.prototype.slice.call(x); }
  function gap() { var g = document.createElement('div'); g.className = 'gap'; return g; }
  function isGap(u) { return u.kind === 'block' && u.node.classList && u.node.classList.contains('gap'); }

  // ---- break a section into pieces that can move between pages ----
  // keep: true marks a heading that must stay with what follows it.
  function units(src) {
    var out = [];
    function block(node, keep) { out.push({ kind: 'block', node: node, keep: !!keep }); }
    function list(tpl, items) {
      var id = 'l' + (listSeq++);
      items.forEach(function (item) { out.push({ kind: 'list', tpl: tpl, id: id, node: item }); });
    }
    function shallow(el) { return el.cloneNode(false); }
    var kids = arr(src.children);
    kids.forEach(function (el, i) {
      if (el.matches('.corner, h2, .turn')) return;
      if (el.matches('.gap') && kids[i + 1] && kids[i + 1].matches('.turn')) return;
      if (el.matches('ul, ol')) { list(shallow(el), arr(el.children)); return; }
      if (el.matches('dl')) {
        var pairs = arr(el.querySelectorAll('dt')).map(function (dt) {
          var f = document.createDocumentFragment();
          f.appendChild(dt.cloneNode(true));
          var dd = dt.nextElementSibling;
          if (dd && dd.matches('dd')) f.appendChild(dd.cloneNode(true));
          return f;
        });
        list(shallow(el), pairs);
        return;
      }
      if (el.matches('nav.idx')) {
        var head = shallow(el);
        head.appendChild(el.querySelector('.idx-head').cloneNode(true));
        block(head, true);
        var body = el.querySelector('.idx-body');
        list(shallow(body), arr(body.children));
        return;
      }
      if (el.matches('article.role')) {
        var prev = el.previousElementSibling;
        if (prev && prev.matches('article.role')) block(gap());
        var start = out.length;
        var h = document.createElement('div');
        h.className = 'role-head';
        h.id = el.id;
        arr(el.children).forEach(function (n) { if (n.matches('h3, .sub')) h.appendChild(n.cloneNode(true)); });
        block(h, true);
        arr(el.children).forEach(function (n) {
          if (n.matches('ul')) list(shallow(n), arr(n.children));
          else if (n.matches('.tech')) block(n);
        });
        var group = 'g' + (listSeq++);                       // a job moves to the next page as a whole
        for (var g = start; g < out.length; g++) out[g].group = group;
        return;
      }
      if (el.matches('h3')) { block(el, true); return; }
      block(el);
    });
    return out;
  }

  function newSheet(src, contd) {
    var p = document.createElement('section');
    p.className = 'page sheet';
    p.setAttribute('data-token', src.getAttribute('data-token'));
    p.setAttribute('data-title', src.getAttribute('data-title'));
    if (contd) p.setAttribute('data-contd', '1');
    p.appendChild(src.querySelector('.corner').cloneNode(true));
    var h = document.createElement('h2');
    h.innerHTML = src.querySelector('h2').innerHTML + (contd ? ' <small>(contd.)</small>' : '');
    p.appendChild(h);
    stage.appendChild(p);
    sheets.push(p);
    return p;
  }
  function overflows(p) { return p.scrollHeight > p.clientHeight + 1; }

  // Add a unit to a page; returns the nodes it created so they can be taken back.
  function put(page, u) {
    if (u.kind === 'block') { var n = u.node.cloneNode(true); page.appendChild(n); return [n]; }
    var box = page.lastElementChild, created = null;
    if (!box || box.getAttribute('data-list') !== u.id) {
      box = u.tpl.cloneNode(false);
      box.setAttribute('data-list', u.id);
      page.appendChild(box);
      created = box;
    }
    var piece = u.node.cloneNode(true);
    var nodes = piece.nodeType === 11 ? arr(piece.childNodes) : [piece];
    box.appendChild(piece);
    return created ? [created] : nodes;
  }
  function take(nodes) { nodes.forEach(function (n) { if (n.parentNode) n.parentNode.removeChild(n); }); }

  // ---- lay every section out onto pages ----
  function paginate() {
    var keep = views.length ? currentToken() : null;
    root.style.setProperty('--lines', linesThatFit());
    root.classList.toggle('spread', isSpread());
    stage.innerHTML = '';
    sheets = [];
    stage.classList.add('building');

    sources.forEach(function (src) {
      var page = newSheet(src, false);
      var placed = [];
      units(src).forEach(function (u) {
        var added = put(page, u);
        if (!overflows(page)) { placed.push({ u: u, nodes: added }); return; }
        take(added);
        if (!placed.length) { placed.push({ u: u, nodes: put(page, u) }); return; }  // too big for any page
        // Carry trailing headings over so none is left alone at the foot of a page.
        var k = placed.length;
        while (k > 0 && (placed[k - 1].u.keep || (u.group && placed[k - 1].u.group === u.group))) k--;
        var carry = [];
        if (k > 0) {
          placed.slice(k).forEach(function (x) { take(x.nodes); carry.push(x.u); });
        }
        page = newSheet(src, true);
        placed = [];
        carry.concat([u]).forEach(function (c) {
          if (isGap(c) && !placed.length) return;
          placed.push({ u: c, nodes: put(page, c) });
        });
      });
    });

    stage.classList.remove('building');
    number();
    // An open notebook always shows two pages: finish an odd count with a blank ruled page.
    if (isSpread() && sheets.length % 2) {
      var blank = document.createElement('section');
      blank.className = 'page sheet blank';
      blank.setAttribute('aria-hidden', 'true');
      blank.setAttribute('data-token', sheets[sheets.length - 1].getAttribute('data-token'));
      blank.setAttribute('data-title', '');
      stage.appendChild(blank);
      sheets.push(blank);
    }
    views = [];
    var step = isSpread() ? 2 : 1;
    for (var i = 0; i < sheets.length; i += step) views.push(step === 2 && sheets[i + 1] ? [i, i + 1] : [i]);
    show(keep ? viewOf(keep) : viewFromHash(), null, false);
  }

  // Page numbers in the corner, and the index's Page No. column, follow the real layout.
  function number() {
    sheets.forEach(function (p, i) {
      var val = p.querySelector('.corner .val');
      if (val) val.textContent = i === 0 ? 'Index' : String(i);
    });
    arr(stage.querySelectorAll('a.idx-row')).forEach(function (a) {
      var token = a.getAttribute('href').slice(1);
      var first = pageOf(token), cell = a.querySelector('.pno');
      if (!cell || first < 0) return;
      var last = first;
      if (!a.getAttribute('data-anchor')) {
        while (sheets[last + 1] && sheets[last + 1].getAttribute('data-contd') &&
               sheets[last + 1].getAttribute('data-token') === token) last++;
      }
      cell.textContent = last > first ? first + '–' + last : String(first);
    });
  }

  function pageOf(token) {
    for (var i = 0; i < sheets.length; i++) {
      if (sheets[i].getAttribute('data-token') === token && !sheets[i].getAttribute('data-contd')) return i;
      if (sheets[i].querySelector('[id="' + token + '"]')) return i;
    }
    return -1;
  }
  function viewOf(token) {
    var p = pageOf(token);
    for (var v = 0; v < views.length; v++) if (views[v].indexOf(p) >= 0) return v;
    return 0;
  }
  function viewFromHash() { var h = (location.hash || '').slice(1); return h ? viewOf(h) : 0; }
  function currentToken() { return sheets[views[view][0]].getAttribute('data-token'); }
  function label(i) {
    return sheets[i].getAttribute('data-title') + (sheets[i].getAttribute('data-contd') ? ' (contd.)' : '');
  }

  function show(v, anchor, smooth) {
    view = Math.max(0, Math.min(views.length - 1, v));
    sheets.forEach(function (p, i) { p.hidden = views[view].indexOf(i) < 0; });
    var prevOk = view > 0, nextOk = view < views.length - 1;
    barPrev.hidden = !prevOk;
    barNext.hidden = !nextOk;
    if (prevOk) {
      var pi = views[view - 1][0];
      barPrev.textContent = '← ' + label(pi);
      barPrev.setAttribute('data-view', view - 1);
      barPrev.setAttribute('href', '#' + sheets[pi].getAttribute('data-token'));
    }
    if (nextOk) {
      var ni = views[view + 1][0];
      barNext.textContent = 'Next: ' + label(ni) + ' →';
      barNext.setAttribute('data-view', view + 1);
      barNext.setAttribute('href', '#' + sheets[ni].getAttribute('data-token'));
    }
    var top = book.getBoundingClientRect().top;
    if (top < 0 || top > window.innerHeight / 3) {
      window.scrollTo({ top: Math.max(0, top + window.pageYOffset - 16), behavior: smooth ? 'smooth' : 'auto' });
    }
    var token = anchor || currentToken();
    try { history.replaceState(null, '', view === 0 && !anchor ? location.pathname + location.search : '#' + token); } catch (e) {}
  }

  document.querySelector('.notebook').addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href^="#"]');
    if (!a) return;
    e.preventDefault();
    if (a.hasAttribute('data-view')) { show(parseInt(a.getAttribute('data-view'), 10)); return; }
    var token = a.getAttribute('href').slice(1);
    show(viewOf(token), a.getAttribute('data-anchor') ? token : null);
  });

  document.addEventListener('keydown', function (e) {
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    if (e.key === 'ArrowRight' || e.key === 'PageDown') { show(view + 1); e.preventDefault(); }
    else if (e.key === 'ArrowLeft' || e.key === 'PageUp') { show(view - 1); e.preventDefault(); }
  });

  // Swipe left / right on touch screens.
  var sx = null, sy = null;
  stage.addEventListener('touchstart', function (e) { sx = e.touches[0].clientX; sy = e.touches[0].clientY; }, { passive: true });
  stage.addEventListener('touchend', function (e) {
    if (sx === null) return;
    var dx = e.changedTouches[0].clientX - sx, dy = e.changedTouches[0].clientY - sy;
    sx = null;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.4) show(view + (dx < 0 ? 1 : -1));
  }, { passive: true });

  window.addEventListener('hashchange', function () { show(viewFromHash()); });
  var timer;
  window.addEventListener('resize', function () { clearTimeout(timer); timer = setTimeout(paginate, 150); });
  paginate();
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(paginate);
})();
