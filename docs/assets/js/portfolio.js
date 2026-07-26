(function (H) {
  function unskel(el) { if (el) el.classList.remove('skel'); }

  H.fetchData('portfolio')
    .then(function (d) {
      var liveText = document.getElementById('live-status-text');
      if (liveText) liveText.textContent = 'Live · updated ' + H.fmtRelativeTime(d.generated_at);

      var eqEl = document.getElementById('s-equity');
      unskel(eqEl);
      H.animateValue(eqEl, 0, H.toNum(d.account.equity) || 0, { format: function (n) { return H.fmtDollar(n); } });

      var deltaEl = document.getElementById('s-equity-delta');
      if (deltaEl && d.day_pnl_pct !== null && d.day_pnl_pct !== undefined) {
        deltaEl.className = 'equity-delta ' + H.pnlClass(d.day_pnl_pct);
        deltaEl.innerHTML = H.fmtPct(d.day_pnl_pct) + ' <span class="delta-suffix">today</span>';
        deltaEl.hidden = false;
      }

      H.sparkline(document.getElementById('equity-spark'), d.equity_series);

      var cashEl = document.getElementById('s-cash');
      unskel(cashEl);
      cashEl.textContent = d.account.cash_pct !== null ? d.account.cash_pct.toFixed(1) + '%' : '-';

      var dayEl = document.getElementById('s-day');
      unskel(dayEl);
      dayEl.textContent = H.fmtDollar(d.day_pnl, true) + ' (' + H.fmtPct(d.day_pnl_pct) + ')';
      dayEl.classList.add(H.pnlClass(d.day_pnl));

      var phaseEl = document.getElementById('s-phase');
      unskel(phaseEl);
      phaseEl.textContent = H.fmtDollar(d.phase_pnl, true) + ' (' + H.fmtPct(d.phase_pnl_pct) + ')';
      phaseEl.classList.add(H.pnlClass(d.phase_pnl));

      renderPositions(d.positions);
      renderDeployChart(d);
      renderTradeHistory(d.trade_history);
    })
    .catch(function (err) {
      console.error(err);
      var liveText = document.getElementById('live-status-text');
      if (liveText) liveText.textContent = 'Live data unavailable';
      document.getElementById('position-grid').innerHTML = '<div class="position-card"><p>Portfolio data unavailable.</p></div>';
    });

  function renderPositions(positions) {
    var grid = document.getElementById('position-grid');
    if (!positions || positions.length === 0) {
      grid.innerHTML = '<div class="position-card"><p>No open positions right now.</p></div>';
      return;
    }
    grid.innerHTML = positions.map(function (p) {
      var plClass = H.pnlClass(p.unrealized_pl);
      var plPct = H.toNum(p.unrealized_plpc);
      return (
        '<div class="position-card">' +
          '<div class="position-card-head">' +
            '<span class="position-ticker">' + H.escapeHtml(p.ticker) + '</span>' +
            '<span class="num ' + plClass + '">' + H.fmtDollar(p.unrealized_pl, true) + (plPct !== null ? ' (' + H.fmtPct(plPct * 100) + ')' : '') + '</span>' +
          '</div>' +
          '<div class="position-metrics">' +
            '<div><div class="m-label">Shares</div><div class="m-value num">' + H.escapeHtml(p.qty) + '</div></div>' +
            '<div><div class="m-label">Entry</div><div class="m-value num">' + H.fmtDollar(p.entry) + '</div></div>' +
            '<div><div class="m-label">Current</div><div class="m-value num">' + H.fmtDollar(p.current) + '</div></div>' +
          '</div>' +
          (p.thesis ? '<div class="position-thesis">' + H.escapeHtml(p.thesis) + '</div>' : '') +
          (p.stop_price ? '<div class="position-stop">Stop <span class="num">' + H.fmtDollar(p.stop_price) + '</span> &middot; ' + H.escapeHtml(p.trail_percent || '10') + '% trailing</div>' : '') +
        '</div>'
      );
    }).join('');
    H.reveal(grid.querySelectorAll('.position-card'), { stagger: 70 });
  }

  function renderDeployChart(d) {
    var equity = H.toNum(d.account.equity) || 0;
    var deployed = (d.positions || []).reduce(function (sum, p) {
      return sum + (H.toNum(p.market_value) || 0);
    }, 0);
    var cash = Math.max(0, equity - deployed);

    var theme = H.chartTheme();
    new Chart(document.getElementById('chart-deploy'), {
      type: 'doughnut',
      data: {
        labels: ['Deployed', 'Cash'],
        datasets: [{
          data: [Math.round(deployed * 100) / 100, Math.round(cash * 100) / 100],
          // Cash uses a visible neutral (not near-black bgSunken) so the arc and
          // its legend swatch read on the dark background.
          backgroundColor: [theme.accent, theme.inkFaint],
          borderColor: [theme.accent, theme.inkFaint],
          borderWidth: 1,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '68%',
        animation: H.reduceMotion ? false : { duration: 700, easing: 'easeOutQuint' },
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: '#ffffff',
              font: { size: 13, weight: '600' },
              padding: 16,
              generateLabels: function (chart) {
                var ds = chart.data.datasets[0];
                var total = ds.data.reduce(function (a, b) { return a + b; }, 0) || 1;
                return chart.data.labels.map(function (label, i) {
                  return {
                    text: label + ' ' + (ds.data[i] / total * 100).toFixed(0) + '%',
                    fillStyle: ds.backgroundColor[i],
                    strokeStyle: ds.borderColor[i],
                    lineWidth: 1,
                    index: i,
                  };
                });
              },
            },
          },
          tooltip: {
            backgroundColor: theme.bgRaised,
            titleColor: theme.ink,
            bodyColor: theme.inkSoft,
            callbacks: { label: function (ctx) { return ' ' + H.fmtDollar(ctx.parsed); } },
          },
        },
      },
    });
  }

  var activeTicker = 'all';

  function applyTickerFilter() {
    document.querySelectorAll('.trade-row[data-ticker]').forEach(function (row) {
      row.hidden = activeTicker !== 'all' && row.getAttribute('data-ticker') !== activeTicker;
    });
  }

  function renderTradeHistory(history) {
    var el = document.getElementById('trade-history');
    var filterBar = document.getElementById('ticker-filter-bar');

    if (!history || history.length === 0) {
      el.innerHTML = '<div class="trade-row"><p>No trades placed yet.</p></div>';
      return;
    }

    el.innerHTML = history.map(function (t) {
      return (
        '<div class="trade-row" data-ticker="' + H.escapeHtml(t.ticker) + '">' +
          '<span class="news-date">' + H.fmtDate(t.date) + '</span>' +
          '<span class="pill ' + (t.side === 'BUY' ? 'pill-buy' : 'pill-sell') + '">' + H.escapeHtml(t.side) + ' ' + H.escapeHtml(t.ticker) + '</span>' +
          '<p>' + H.escapeHtml(t.thesis || 'No thesis logged.') + '</p>' +
        '</div>'
      );
    }).join('');
    // Trade rows are left static - a long ledger animating row-by-row is busy.

    var tickers = Array.from(new Set(history.map(function (t) { return t.ticker; })));
    if (tickers.length > 1) {
      filterBar.hidden = false;
      tickers.forEach(function (ticker) {
        var btn = document.createElement('button');
        btn.className = 'filter-pill';
        btn.setAttribute('data-ticker', ticker);
        btn.setAttribute('aria-pressed', 'false');
        btn.textContent = ticker;
        filterBar.appendChild(btn);
      });
      filterBar.querySelectorAll('.filter-pill').forEach(function (pill) {
        pill.addEventListener('click', function () {
          filterBar.querySelectorAll('.filter-pill').forEach(function (p) { p.setAttribute('aria-pressed', 'false'); });
          pill.setAttribute('aria-pressed', 'true');
          activeTicker = pill.getAttribute('data-ticker');
          applyTickerFilter();
        });
      });
    }
  }
})(window.Hermes);
