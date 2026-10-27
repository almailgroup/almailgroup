/* Almail Group — site behaviour: sticky header, mobile menu, back to top, scroll reveal, photo hints, quote slider */
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
    // The header's height and the scroll position are read inside a frame,
    // never while the script starts: reading either then makes the browser
    // lay out the whole page early, in one long task that holds up the first
    // taps. The height is read again after a resize.
    var limit = null;
    var lastY = null;
    var pending = false;
    function update() {
      pending = false;
      if (limit === null) limit = header.offsetHeight + 120;
      var y = window.scrollY;
      if (lastY === null) lastY = y;
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
    function schedule() {
      if (pending) return;
      pending = true;
      window.requestAnimationFrame(update);
    }
    on(window, 'scroll', schedule, { passive: true });
    on(window, 'resize', function () {
      if (header.classList.contains('is-stuck')) return;   // the compact bar is not the height to measure
      limit = null;
      schedule();
    });
    schedule();
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

    function setInert(open) {
      behind.forEach(function (el) { if (open) el.setAttribute('inert', ''); else el.removeAttribute('inert'); });
    }

    // The menu starts to slide first, and the bookkeeping (the page behind
    // made inert or not, focus moved) follows once that first frame is on
    // screen, so a tap is answered at once. `refocus` sends focus back to
    // the menu button after closing.
    function afterPaint(fn) {
      window.requestAnimationFrame(function () { setTimeout(fn, 0); });
    }
    function setState(open, refocus) {
      drawer.classList.toggle('is-open', open);
      backdrop.classList.toggle('is-open', open);
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      doc.body.style.overflow = open ? 'hidden' : '';
      afterPaint(function () {
        if (drawer.classList.contains('is-open') !== open) return;   // changed again meanwhile
        setInert(open);
        var f = open ? drawer.querySelector('a, button') : refocus ? burger : null;
        if (f) f.focus({ preventScroll: true });
      });
    }

    on(burger, 'click', function () { setState(!drawer.classList.contains('is-open')); });
    on(backdrop, 'click', function () { setState(false); });
    on(closeBtn, 'click', function () { setState(false, true); });
    all('.mobile-nav a').forEach(function (a) { on(a, 'click', function () { setState(false); }); });
    on(doc, 'keydown', function (e) {
      if (e.key === 'Escape' && drawer.classList.contains('is-open')) setState(false, true);
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
    function schedule() {
      if (pending) return;
      pending = true;
      window.requestAnimationFrame(update);   // in a frame, as the header's (above)
    }
    on(window, 'scroll', schedule, { passive: true });
    on(btn, 'click', function () {
      window.scrollTo({ top: 0, behavior: reducedMotion ? 'auto' : 'smooth' });
      var brand = doc.querySelector('.site-header .brand');
      if (brand) brand.focus({ preventScroll: true });
    });
    schedule();
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
    }, { threshold: 0, rootMargin: '0px 0px -40px 0px' });
    items.forEach(function (el) { io.observe(el); });
  }

  /* ---------- photo hints ----------
     A photo's blurred stand-in (style.css, "photos that load") is drawn
     once its box is within a screen of view, which is after the first
     paint: the page's first frame never waits on the stand-ins of photos
     further down. The photo itself marks its box loaded (build.py). */
  function photoHints() {
    var boxes = all('.has-hint');
    if (!boxes.length) return;
    if (!('IntersectionObserver' in window)) {
      boxes.forEach(function (el) { el.classList.add('is-near'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-near');
        io.unobserve(entry.target);
      });
    }, { rootMargin: '100% 0px' });
    boxes.forEach(function (el) { io.observe(el); });
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
    // iOS Safari shows :active (the tap feedback in style.css) only on a page
    // that listens for touches.
    on(doc, 'touchstart', function () {}, { passive: true });
    stickyHeader();
    mobileNav();
    toTop();
    reveal();
    photoHints();
    quoteSlider();
  }

  if (doc.readyState === 'loading') on(doc, 'DOMContentLoaded', init);
  else init();
})();
