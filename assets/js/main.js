/* Almail Group — site behaviour: sticky header, mobile menu, back to top, scroll reveal, quote slider */
(function () {
  'use strict';

  var doc = document;
  var on = function (el, ev, fn, opts) { if (el) el.addEventListener(ev, fn, opts); };
  var all = function (sel, ctx) { return Array.prototype.slice.call((ctx || doc).querySelectorAll(sel)); };
  var reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Keyboard focus inside el. Focus a tap leaves behind (on the menu button
  // after closing the menu, say) doesn't count: it would pin the header.
  function keyboardIn(el) {
    var a = doc.activeElement;
    if (!a || !el.contains(a)) return false;
    try { return a.matches(':focus-visible'); } catch (e) { return true; }
  }

  /* ---------- sticky header ----------
     The header sits over the hero at the top of the page. Once it has
     scrolled out of sight it comes back as a compact bar fixed to the top
     (.is-stuck in style.css), and goes back to normal near the top.
     On a phone or tablet the bar also steps aside while the reader scrolls
     down and comes back as soon as they scroll up (.is-hidden): fixed, it
     takes a tenth of a phone's screen. It stays put while the menu is open
     or something in the header has keyboard focus. */
  function stickyHeader() {
    var header = doc.querySelector('.site-header');
    if (!header) return;
    var drawer = doc.querySelector('.mobile-nav');
    var small = window.matchMedia ? window.matchMedia('(max-width: 1080px), (max-height: 500px)') : null;
    var limit = header.offsetHeight + 120;
    var lastY = window.scrollY;
    var pending = false;
    function update() {
      pending = false;
      var y = window.scrollY;
      var stuck = y > limit;
      header.classList.toggle('is-stuck', stuck);
      var delta = y - lastY;
      if (!stuck || !small || !small.matches) {
        header.classList.remove('is-hidden');
      } else if (Math.abs(delta) > 6) {
        var keep = keyboardIn(header) || (drawer && drawer.classList.contains('is-open'));
        header.classList.toggle('is-hidden', delta > 0 && !keep);
      } else {
        return;   // too small a move to count; measure the next one from here
      }
      lastY = y;
    }
    on(window, 'scroll', function () {
      if (pending) return;
      pending = true;
      window.requestAnimationFrame(update);
    }, { passive: true });
    update();
  }

  /* ---------- mobile drawer ---------- */
  function mobileNav() {
    var burger = doc.querySelector('.burger');
    var drawer = doc.querySelector('.mobile-nav');
    var backdrop = doc.querySelector('.backdrop');
    var closeBtn = doc.querySelector('.mobile-nav .close');
    if (!burger || !drawer || !backdrop) return;
    // While the menu is open the page behind it is inert, so neither the
    // keyboard nor a screen reader's swipe can wander out of the menu.
    var behind = all('.skip-link, .site-header, main, .site-footer, .to-top');

    function setState(open) {
      drawer.classList.toggle('is-open', open);
      backdrop.classList.toggle('is-open', open);
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      doc.body.style.overflow = open ? 'hidden' : '';
      behind.forEach(function (el) { if (open) el.setAttribute('inert', ''); else el.removeAttribute('inert'); });
      if (open) { var f = drawer.querySelector('a, button'); if (f) f.focus(); }
    }

    on(burger, 'click', function () { setState(!drawer.classList.contains('is-open')); });
    on(backdrop, 'click', function () { setState(false); });
    on(closeBtn, 'click', function () { setState(false); burger.focus(); });
    all('.mobile-nav a').forEach(function (a) { on(a, 'click', function () { setState(false); }); });
    on(doc, 'keydown', function (e) {
      if (e.key === 'Escape' && drawer.classList.contains('is-open')) { setState(false); burger.focus(); }
    });
    // the drawer only exists below the desktop breakpoint in style.css
    on(window, 'resize', function () {
      if (window.innerWidth > 1080 && drawer.classList.contains('is-open')) setState(false);
    });
  }

  /* ---------- back to top ----------
     The pages are long on a phone. The button shows once the page has
     scrolled a screen and a half, and hands focus to the logo at the top so
     the keyboard lands where the eye does. Without JavaScript it stays hidden. */
  function toTop() {
    var btn = doc.querySelector('.to-top');
    if (!btn) return;
    btn.hidden = false;
    var pending = false;
    function update() {
      pending = false;
      btn.classList.toggle('is-visible', window.scrollY > window.innerHeight * 1.5);
    }
    on(window, 'scroll', function () {
      if (pending) return;
      pending = true;
      window.requestAnimationFrame(update);
    }, { passive: true });
    on(btn, 'click', function () {
      window.scrollTo({ top: 0, behavior: reducedMotion ? 'auto' : 'smooth' });
      var brand = doc.querySelector('.site-header .brand');
      if (brand) brand.focus({ preventScroll: true });
    });
    update();
  }

  /* ---------- reveal on scroll ---------- */
  function reveal() {
    var items = all('.reveal');
    if (!items.length) return;
    if (reducedMotion || !('IntersectionObserver' in window)) {
      items.forEach(function (el) { el.classList.add('is-in'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        var delay = parseInt(el.getAttribute('data-delay') || '0', 10);
        setTimeout(function () { el.classList.add('is-in'); }, delay);
        io.unobserve(el);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -60px 0px' });
    items.forEach(function (el) { io.observe(el); });
  }

  /* ---------- quote slider ----------
     Slides are stacked in one grid cell and cross-faded. With a single
     quote there is nothing to rotate, so the dot just marks it. */
  function quoteSlider() {
    var root = doc.querySelector('.quote');
    if (!root) return;
    var slides = all('.quote-slide', root);
    var dots = all('.quote-dot', root);
    if (slides.length < 2) return;

    var index = 0;
    var timer = null;
    var paused = false;

    function show(n) {
      index = (n + slides.length) % slides.length;
      slides.forEach(function (s, i) {
        var active = i === index;
        s.classList.toggle('is-active', active);
        if (active) s.removeAttribute('hidden'); else s.setAttribute('hidden', '');
      });
      dots.forEach(function (d, i) {
        if (i === index) d.setAttribute('aria-current', 'true'); else d.removeAttribute('aria-current');
      });
    }

    function start() {
      if (reducedMotion || timer) return;
      timer = setInterval(function () { if (!paused) show(index + 1); }, 7000);
    }

    dots.forEach(function (d, i) { on(d, 'click', function () { show(i); }); });
    on(root, 'mouseenter', function () { paused = true; });
    on(root, 'mouseleave', function () { paused = false; });
    on(root, 'focusin', function () { paused = true; });
    on(root, 'focusout', function () { paused = false; });
    start();
  }

  function init() {
    stickyHeader();
    mobileNav();
    toTop();
    reveal();
    quoteSlider();
  }

  if (doc.readyState === 'loading') on(doc, 'DOMContentLoaded', init);
  else init();
})();
