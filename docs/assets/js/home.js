(function (H) {
  // Hero entrance plays immediately on load, regardless of data fetch state -
  // content is already fully visible in the DOM either way (progressive
  // enhancement), this is just a one-time cascade on top of that.
  H.staggerIn(
    [
      document.querySelector('.hero h1'),
      document.querySelector('.hero-lede'),
      document.querySelector('.hero-ctas'),
    ],
    { stagger: 150, duration: 900, distance: 22 }
  );

  // Scroll-reveal only the deliberate below-the-fold moments. The rulebook
  // list is left static on purpose - a long column of rows sliding up reads as
  // busy, not cinematic.
  H.reveal(document.querySelectorAll('.wat-item'), { stagger: 130 });

  function unskel(el) {
    if (el) el.classList.remove('skel');
  }

  H.fetchData('home')
    .then(function (d) {
      var liveText = document.getElementById('live-status-text');
      if (liveText) liveText.textContent = 'Live · updated ' + H.fmtRelativeTime(d.generated_at);

      var eqEl = document.getElementById('s-equity');
      unskel(eqEl);
      H.animateValue(eqEl, 0, H.toNum(d.equity) || 0, { format: function (n) { return H.fmtDollar(n); } });

      var deltaEl = document.getElementById('s-equity-delta');
      if (deltaEl && d.day_pnl_pct !== null && d.day_pnl_pct !== undefined) {
        deltaEl.className = 'equity-delta ' + H.pnlClass(d.day_pnl_pct);
        deltaEl.innerHTML = H.fmtPct(d.day_pnl_pct) + ' <span class="delta-suffix">today</span>';
        deltaEl.hidden = false;
      }

      H.sparkline(document.getElementById('equity-spark'), d.equity_series);

      var phaseEl = document.getElementById('s-phase');
      unskel(phaseEl);
      var phaseVal = H.toNum(d.phase_pnl_pct) || 0;
      H.animateValue(phaseEl, 0, phaseVal, { format: function (n) { return H.fmtPct(n); } });
      phaseEl.classList.add(H.pnlClass(d.phase_pnl_pct));

      var daysEl = document.getElementById('s-days');
      unskel(daysEl);
      daysEl.textContent = d.days_live !== null ? d.days_live : '-';

      var posEl = document.getElementById('s-positions');
      unskel(posEl);
      posEl.textContent = d.open_position_count;

      var grid = document.getElementById('activity-grid');
      if (!d.recent_activity || d.recent_activity.length === 0) {
        grid.innerHTML = '<div class="activity-card"><p>No activity logged yet.</p></div>';
        return;
      }
      grid.innerHTML = d.recent_activity.map(function (item) {
        var href = item.type === 'trade' ? 'portfolio.html' : 'news.html';
        return (
          '<a class="activity-card" href="' + href + '">' +
            '<span class="news-date">' + H.fmtDate(item.date) + '</span>' +
            '<p>' + H.escapeHtml(item.summary) + '</p>' +
          '</a>'
        );
      }).join('');
      H.reveal(grid.querySelectorAll('.activity-card'), { stagger: 70 });
    })
    .catch(function (err) {
      console.error(err);
      var liveText = document.getElementById('live-status-text');
      if (liveText) liveText.textContent = 'Live data unavailable';
      var grid = document.getElementById('activity-grid');
      if (grid) grid.innerHTML = '<div class="activity-card"><p>Activity feed unavailable.</p></div>';
    });
})(window.Hermes);
