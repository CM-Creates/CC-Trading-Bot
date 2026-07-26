window.Hermes = window.Hermes || {};

(function (H) {
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  H.reduceMotion = reduceMotion;

  // ease-out-expo - visually matches the --ease-out cubic-bezier token
  function easeOutExpo(t) {
    return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
  }

  // Animate a number from `from` to `to` inside el.textContent.
  // `format(n)` renders the number at each frame (defaults to fixed(2)).
  H.animateValue = function (el, from, to, opts) {
    opts = opts || {};
    var duration = reduceMotion ? 0 : (opts.duration || 900);
    var format = opts.format || function (n) { return n.toFixed(2); };

    if (!el || duration === 0 || from === to || isNaN(from) || isNaN(to)) {
      if (el) el.textContent = format(to);
      return;
    }

    var start = null;
    function frame(ts) {
      if (start === null) start = ts;
      var progress = Math.min((ts - start) / duration, 1);
      var eased = easeOutExpo(progress);
      el.textContent = format(from + (to - from) * eased);
      if (progress < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  };

  // Stagger a one-time entrance for a list of elements. Elements are fully
  // visible by default (no CSS opacity:0 anywhere) - this only applies a
  // WAAPI animation on top of the natural visible state, so a JS failure
  // or slow script never leaves content invisible (learned from a v1 bug).
  H.staggerIn = function (elements, opts) {
    if (reduceMotion || !('animate' in Element.prototype)) return;
    opts = opts || {};
    var duration = opts.duration || 560;
    var stagger = opts.stagger || 90;
    var distance = opts.distance || 16;
    var easing = 'cubic-bezier(0.16, 1, 0.3, 1)';

    elements.forEach(function (el, i) {
      if (!el) return;
      el.animate(
        [
          { opacity: 0, transform: 'translateY(' + distance + 'px)' },
          { opacity: 1, transform: 'translateY(0)' },
        ],
        { duration: duration, delay: i * stagger, easing: easing, fill: 'backwards' }
      );
    });
  };

  // Scroll-reveal: play a one-time translateY+fade entrance as elements enter
  // the viewport, cascading items that arrive together. Progressive enhancement
  // just like staggerIn - content is fully visible in the DOM by default, this
  // only layers a WAAPI animation on top, so a JS/observer failure never hides
  // anything. No-ops under reduced motion (content stays static + visible).
  H.reveal = function (elements, opts) {
    elements = Array.prototype.slice.call(elements || []).filter(Boolean);
    if (elements.length === 0) return;
    if (reduceMotion || !('IntersectionObserver' in window) || !('animate' in Element.prototype)) return;

    opts = opts || {};
    // Cinematic restraint: fewer, slower, smaller-travel reveals read calmer
    // than a lot of items sliding a long way in quick succession.
    var distance = opts.distance || 14;
    var duration = opts.duration || 820;
    var stagger = opts.stagger || 110;
    var easing = 'cubic-bezier(0.22, 1, 0.36, 1)';

    var cohortCount = 0;
    var lastTs = 0;

    var io = new IntersectionObserver(function (entries) {
      var now = (window.performance && performance.now) ? performance.now() : Date.now();
      entries
        .filter(function (e) { return e.isIntersecting; })
        // top-to-bottom so a section cascades in reading order
        .sort(function (a, b) { return a.boundingClientRect.top - b.boundingClientRect.top; })
        .forEach(function (e) {
          if (now - lastTs > 140) cohortCount = 0; // new cohort after a scroll gap
          lastTs = now;
          e.target.animate(
            [
              { opacity: 0, transform: 'translateY(' + distance + 'px)' },
              { opacity: 1, transform: 'translateY(0)' },
            ],
            { duration: duration, delay: cohortCount * stagger, easing: easing, fill: 'backwards' }
          );
          cohortCount++;
          io.unobserve(e.target);
        });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });

    elements.forEach(function (el) { io.observe(el); });
  };

  // Inline SVG equity sparkline drawn from a real series of numbers. Colours by
  // overall trend (gain/loss), draws the line left-to-right once on first paint
  // (skipped under reduced motion). Returns early on too-few points so callers
  // can leave the value standing alone.
  H.sparkline = function (el, points, opts) {
    if (!el) return;
    points = (points || []).map(Number).filter(function (n) { return !isNaN(n); });
    if (points.length < 3) { el.innerHTML = ''; el.setAttribute('data-empty', 'true'); return; }

    opts = opts || {};
    var W = opts.width || 240;
    var Hgt = opts.height || 56;
    var pad = opts.pad || 4;             // vertical breathing room for the stroke
    var min = Math.min.apply(null, points);
    var max = Math.max.apply(null, points);
    var span = max - min || 1;
    var innerH = Hgt - pad * 2;

    function x(i) { return (i / (points.length - 1)) * W; }
    function y(v) { return pad + innerH - ((v - min) / span) * innerH; }

    var d = points.map(function (v, i) {
      return (i === 0 ? 'M' : 'L') + x(i).toFixed(2) + ' ' + y(v).toFixed(2);
    }).join(' ');
    var area = d + ' L' + W + ' ' + Hgt + ' L0 ' + Hgt + ' Z';

    var up = points[points.length - 1] >= points[0];
    var stroke = up ? 'var(--gain)' : 'var(--loss)';
    var gid = 'spark-fill-' + Math.random().toString(36).slice(2, 8);
    var lastX = x(points.length - 1).toFixed(2);
    var lastY = y(points[points.length - 1]).toFixed(2);

    el.style.color = stroke;
    el.innerHTML =
      '<svg viewBox="0 0 ' + W + ' ' + Hgt + '" width="100%" height="100%" preserveAspectRatio="none" aria-hidden="true" focusable="false">' +
        '<defs><linearGradient id="' + gid + '" x1="0" y1="0" x2="0" y2="1">' +
          '<stop offset="0" stop-color="currentColor" stop-opacity="0.20"/>' +
          '<stop offset="1" stop-color="currentColor" stop-opacity="0"/>' +
        '</linearGradient></defs>' +
        '<path d="' + area + '" fill="url(#' + gid + ')" stroke="none" class="spark-area"/>' +
        '<path d="' + d + '" fill="none" stroke="currentColor" stroke-width="1.75" ' +
          'stroke-linecap="round" stroke-linejoin="round" pathLength="1" class="spark-line"/>' +
        '<circle cx="' + lastX + '" cy="' + lastY + '" r="2.6" fill="currentColor" class="spark-dot"/>' +
      '</svg>';

    if (reduceMotion) return;
    var line = el.querySelector('.spark-line');
    var dot = el.querySelector('.spark-dot');
    var area2 = el.querySelector('.spark-area');
    if (line && line.animate) {
      // pathLength=1 lets us dash-draw without measuring the real length
      line.style.strokeDasharray = '1';
      line.animate(
        [{ strokeDashoffset: 1 }, { strokeDashoffset: 0 }],
        { duration: 900, easing: 'cubic-bezier(0.16, 1, 0.3, 1)', fill: 'backwards' }
      );
    }
    if (area2 && area2.animate) {
      area2.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 900, delay: 200, easing: 'ease-out', fill: 'backwards' });
    }
    if (dot && dot.animate) {
      dot.animate([{ opacity: 0 }, { opacity: 0 }, { opacity: 1 }], { duration: 950, easing: 'ease-out', fill: 'backwards' });
    }
  };
})(window.Hermes);
