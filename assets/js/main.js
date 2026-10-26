/* Almail Group — site behaviour: sticky header, mobile menu, scroll reveal, quote slider */
(function () {
  'use strict';

  var doc = document;
  var on = function (el, ev, fn, opts) { if (el) el.addEventListener(ev, fn, opts); };
  var all = function (sel, ctx) { return Array.prototype.slice.call((ctx || doc).querySelectorAll(sel)); };
  var reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- sticky header ----------
     The header sits over the hero at the top of the page. Once it has
     scrolled out of sight it comes back as a compact bar fixed to the top
     (.is-stuck in style.css), and goes back to normal near the top. */
  function stickyHeader() {
    var header = doc.querySelector('.site-header');
    if (!header) return;
    var limit = header.offsetHeight + 120;
    var pending = false;
    function update() {
      pending = false;
      header.classList.toggle('is-stuck', window.scrollY > limit);
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
    var behind = all('.skip-link, .site-header, main, .site-footer');

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
    reveal();
    quoteSlider();
  }

  if (doc.readyState === 'loading') on(doc, 'DOMContentLoaded', init);
  else init();
})();
