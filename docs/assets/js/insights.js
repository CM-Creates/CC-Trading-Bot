(function (H) {
  H.fetchData('insights')
    .then(function (d) {
      var weekly = d.weekly || [];
      var latest = weekly[0];

      if (latest) {
        var vsSp = document.getElementById('s-vs-sp');
        var vsSpVal = H.toNum(latest.stats.bot_vs_sandp);
        vsSp.classList.remove('skel');
        vsSp.textContent = vsSpVal === null ? '-' : H.fmtPct(vsSpVal);
        vsSp.classList.add(H.pnlClass(vsSpVal));

        var shortStat = function (s) { return s ? s.split(' (')[0] : '-'; };
        var winEl = document.getElementById('s-winrate');
        var pfEl = document.getElementById('s-pf');
        var tradesEl = document.getElementById('s-trades');
        winEl.classList.remove('skel');
        pfEl.classList.remove('skel');
        tradesEl.classList.remove('skel');
        winEl.textContent = shortStat(latest.stats.win_rate);
        pfEl.textContent = shortStat(latest.stats.profit_factor);
        tradesEl.textContent = latest.stats.trades || '-';
      }

      renderChart(weekly);
      renderMacro(d.macro_snapshot);
      renderFieldNotes(weekly);
    })
    .catch(function (err) {
      console.error(err);
      document.getElementById('field-notes').innerHTML = '<p style="color:var(--ink-faint);">Insights data unavailable.</p>';
    });

  function renderChart(weeklyLatestFirst) {
    var weeksAsc = weeklyLatestFirst.slice().reverse();
    if (weeksAsc.length === 0) return;

    var labels = ['Start'];
    var equity = [H.toNum(weeksAsc[0].stats.starting_portfolio)];
    var sp = [H.toNum(weeksAsc[0].stats.starting_portfolio)];

    weeksAsc.forEach(function (w) {
      labels.push(H.fmtDate(w.week_end));
      equity.push(H.toNum(w.stats.ending_portfolio));
      var spReturn = H.toNum(w.stats.sandp_500_week) || 0;
      var prevSp = sp[sp.length - 1];
      sp.push(prevSp === null ? null : Math.round(prevSp * (1 + spReturn / 100) * 100) / 100);
    });

    var theme = H.chartTheme();
    var opts = H.baseChartOptions(theme);
    opts.scales.y.ticks.callback = function (v) { return '$' + (v / 1000).toFixed(0) + 'k'; };

    new Chart(document.getElementById('chart-equity'), {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          { label: 'Hermes', data: equity, borderColor: theme.accent, backgroundColor: theme.accentSoft, tension: 0.3, fill: true, pointRadius: 4 },
          { label: 'S&P 500 (equivalent)', data: sp, borderColor: theme.inkFaint, borderDash: [4, 4], tension: 0, fill: false, pointRadius: 2 },
        ],
      },
      options: opts,
    });
  }

  function renderMacro(macro) {
    var grid = document.getElementById('macro-grid');
    if (!macro || !macro.market_lines || macro.market_lines.length === 0) {
      grid.innerHTML = '<div class="macro-line">No macro snapshot logged yet.</div>';
      return;
    }
    grid.innerHTML = macro.market_lines.map(function (line) {
      return '<div class="macro-line">' + H.escapeHtml(line) + '</div>';
    }).join('');
  }

  function renderFieldNotes(weeklyLatestFirst) {
    var el = document.getElementById('field-notes');
    if (weeklyLatestFirst.length === 0) {
      el.innerHTML = '<p style="color:var(--ink-faint);">First weekly review lands Friday.</p>';
      return;
    }

    function bullets(items) {
      return '<ul>' + items.map(function (i) { return '<li>' + H.escapeAndBold(i) + '</li>'; }).join('') + '</ul>';
    }

    el.innerHTML = weeklyLatestFirst.map(function (w, i) {
      var sections = '';
      if (w.what_worked.length) sections += '<div style="margin-top:18px;"><div class="stat-label">What worked</div>' + bullets(w.what_worked) + '</div>';
      if (w.what_didnt.length) sections += '<div style="margin-top:18px;"><div class="stat-label">What didn\'t</div>' + bullets(w.what_didnt) + '</div>';
      if (w.key_lessons.length) sections += '<div style="margin-top:18px;"><div class="stat-label">Key lessons</div>' + bullets(w.key_lessons) + '</div>';
      if (w.adjustments.length) sections += '<div style="margin-top:18px;"><div class="stat-label">Adjustments</div>' + bullets(w.adjustments) + '</div>';

      var isOpen = i === 0;
      return (
        '<div class="field-note" data-open="' + isOpen + '">' +
          '<button class="field-note-toggle" aria-expanded="' + isOpen + '">' +
            '<h3>Week ending ' + H.escapeHtml(H.fmtDate(w.week_end)) + '</h3>' +
            '<span class="field-note-meta">' +
              '<span class="num">Bot vs S&amp;P <span class="grade">' + H.escapeHtml(w.stats.bot_vs_sandp || '-') + '</span></span>' +
              '<span class="grade">Grade ' + H.escapeHtml(w.grade) + '</span>' +
              '<svg class="field-note-chevron" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 9l6 6 6-6"/></svg>' +
            '</span>' +
          '</button>' +
          '<div class="field-note-body-wrap"><div class="field-note-body"><div class="field-note-body-inner">' + sections + '</div></div></div>' +
        '</div>'
      );
    }).join('');

    el.querySelectorAll('.field-note-toggle').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var note = btn.closest('.field-note');
        var open = note.getAttribute('data-open') === 'true';
        note.setAttribute('data-open', String(!open));
        btn.setAttribute('aria-expanded', String(!open));
      });
    });

    H.reveal(el.querySelectorAll('.field-note'), { stagger: 60 });
  }
})(window.Hermes);
