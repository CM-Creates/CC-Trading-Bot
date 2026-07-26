(function () {
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.querySelector('.site-nav');

  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.getAttribute('data-open') === 'true';
      nav.setAttribute('data-open', String(!open));
      toggle.setAttribute('aria-expanded', String(!open));
    });
    nav.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        nav.setAttribute('data-open', 'false');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // Firm up the translucent header once the page scrolls past the top. Uses a
  // 1px sentinel + IntersectionObserver instead of a scroll listener (no
  // per-frame work). Header stays put; only its background/border cross-fade.
  var header = document.querySelector('.site-header');
  if (header && 'IntersectionObserver' in window) {
    var sentinel = document.createElement('div');
    sentinel.setAttribute('aria-hidden', 'true');
    sentinel.style.cssText = 'position:absolute;top:0;left:0;width:1px;height:1px;pointer-events:none;';
    document.body.appendChild(sentinel);
    new IntersectionObserver(function (entries) {
      header.classList.toggle('scrolled', !entries[0].isIntersecting);
    }, { rootMargin: '-1px 0px 0px 0px' }).observe(sentinel);
  }

  // Sliding active-indicator under the nav links (desktop only - hidden
  // under 720px via CSS). Positioned with transform/width, not layout
  // properties, so it stays smooth.
  if (!nav) return;
  var links = Array.prototype.slice.call(nav.querySelectorAll('a'));
  if (links.length === 0) return;

  var indicator = document.createElement('span');
  indicator.className = 'nav-indicator';
  indicator.setAttribute('aria-hidden', 'true');
  nav.appendChild(indicator);

  function moveIndicatorTo(link) {
    if (!link) { indicator.style.opacity = '0'; return; }
    var navRect = nav.getBoundingClientRect();
    var linkRect = link.getBoundingClientRect();
    indicator.style.width = linkRect.width + 'px';
    indicator.style.transform = 'translateX(' + (linkRect.left - navRect.left) + 'px)';
    indicator.style.opacity = '1';
  }

  var current = nav.querySelector('a[aria-current="page"]');

  links.forEach(function (link) {
    link.addEventListener('mouseenter', function () { moveIndicatorTo(link); });
  });
  nav.addEventListener('mouseleave', function () { moveIndicatorTo(current); });

  if (current) {
    // Position after layout/fonts settle so the rect is accurate.
    requestAnimationFrame(function () { moveIndicatorTo(current); });
    window.addEventListener('resize', function () { moveIndicatorTo(current); });
  }
})();
