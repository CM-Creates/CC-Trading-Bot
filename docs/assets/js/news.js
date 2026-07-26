(function (H) {
  function bulletList(lines) {
    return '<ul class="news-lines">' + lines.map(function (l) {
      return '<li>' + H.escapeAndBold(l) + '</li>';
    }).join('') + '</ul>';
  }

  function searchText(item) {
    var parts = [item.title, item.decision, item.ticker, item.side, item.thesis]
      .concat(item.market_lines || [])
      .concat(item.trade_ideas || [])
      .filter(Boolean);
    return parts.join(' ').toLowerCase();
  }

  function researchCard(item) {
    var isTrade = item.decision === 'TRADE';
    var teaser = item.market_lines.slice(0, 3);
    var rest = item.market_lines.slice(3);

    var extra = '';
    if (rest.length) extra += bulletList(rest);
    if (item.trade_ideas && item.trade_ideas.length) {
      extra += '<div style="margin-top:20px;"><div class="stat-label" style="margin-bottom:10px;">Trade ideas considered</div>' + bulletList(item.trade_ideas) + '</div>';
    }
    if (item.risk_factors && item.risk_factors.length) {
      extra += '<div style="margin-top:20px;"><div class="stat-label" style="margin-bottom:10px;">Risk factors</div>' + bulletList(item.risk_factors) + '</div>';
    }

    return (
      '<article class="news-card" data-decision="' + item.decision + '" data-search="' + H.escapeHtml(searchText(item)) + '">' +
        '<div class="news-card-head">' +
          '<span class="news-date">' + H.fmtDate(item.date) + '</span>' +
          '<span class="pill ' + (isTrade ? 'pill-trade' : 'pill-hold') + '">' + H.escapeHtml(item.decision) + '</span>' +
        '</div>' +
        '<h3 class="news-title">' + H.escapeHtml(item.title || 'Pre-market research') + '</h3>' +
        (teaser.length ? bulletList(teaser) : '') +
        (extra ? (
          '<details class="news-details">' +
            '<summary class="news-toggle" data-toggle-text>Full research and risk factors &rarr;</summary>' +
            '<div style="margin-top:14px;">' + extra + '</div>' +
          '</details>'
        ) : '') +
      '</article>'
    );
  }

  function tradeCard(item) {
    var pillClass = item.side === 'BUY' ? 'pill-buy' : 'pill-sell';
    return (
      '<article class="news-card" data-decision="TRADE" data-search="' + H.escapeHtml(searchText(item)) + '">' +
        '<div class="news-card-head">' +
          '<span class="news-date">' + H.fmtDate(item.date) + '</span>' +
          '<span class="pill ' + pillClass + '">' + H.escapeHtml(item.side) + ' ' + H.escapeHtml(item.ticker) + '</span>' +
        '</div>' +
        '<h3 class="news-title">' + H.escapeHtml(item.side) + ' ' + H.escapeHtml(item.ticker) + '</h3>' +
        '<div class="position-metrics">' +
          '<div><div class="m-label">Shares</div><div class="m-value num">' + H.escapeHtml(item.shares || '-') + '</div></div>' +
          '<div><div class="m-label">Entry</div><div class="m-value num">$' + H.escapeHtml(item.entry || '-') + '</div></div>' +
          '<div><div class="m-label">Stop</div><div class="m-value num">$' + H.escapeHtml(item.stop || '-') + '</div></div>' +
        '</div>' +
        (item.thesis ? '<p style="margin-top:14px;font-size:0.92rem;line-height:1.55;color:var(--ink-soft);">' + H.escapeHtml(item.thesis) + '</p>' : '') +
      '</article>'
    );
  }

  var activeFilter = 'all';
  var searchQuery = '';

  function applyFilters() {
    var feed = document.getElementById('news-feed');
    var cards = feed.querySelectorAll('.news-card');
    var visibleCount = 0;
    cards.forEach(function (card) {
      var matchesFilter = activeFilter === 'all' || card.getAttribute('data-decision') === activeFilter;
      var matchesSearch = !searchQuery || (card.getAttribute('data-search') || '').indexOf(searchQuery) !== -1;
      var visible = matchesFilter && matchesSearch;
      card.hidden = !visible;
      if (visible) visibleCount++;
    });
    document.getElementById('news-no-results').hidden = visibleCount !== 0;
  }

  function wireFilters() {
    document.querySelectorAll('.filter-pill').forEach(function (pill) {
      pill.addEventListener('click', function () {
        document.querySelectorAll('.filter-pill').forEach(function (p) { p.setAttribute('aria-pressed', 'false'); });
        pill.setAttribute('aria-pressed', 'true');
        activeFilter = pill.getAttribute('data-filter');
        applyFilters();
      });
    });
    var search = document.getElementById('news-search');
    search.addEventListener('input', function () {
      searchQuery = search.value.trim().toLowerCase();
      applyFilters();
    });
  }

  H.fetchData('news')
    .then(function (d) {
      var feed = document.getElementById('news-feed');
      if (!d.items || d.items.length === 0) {
        feed.innerHTML = '<div class="news-card"><p>No research entries yet.</p></div>';
        return;
      }
      feed.innerHTML = d.items.map(function (item) {
        return item.type === 'trade' ? tradeCard(item) : researchCard(item);
      }).join('');

      feed.querySelectorAll('details.news-details').forEach(function (el) {
        el.addEventListener('toggle', function () {
          var label = el.querySelector('[data-toggle-text]');
          if (label) label.innerHTML = el.open ? 'Show less' : 'Full research and risk factors &rarr;';
        });
      });

      wireFilters();
      H.reveal(feed.querySelectorAll('.news-card'), { stagger: 50 });
    })
    .catch(function (err) {
      console.error(err);
      document.getElementById('news-feed').innerHTML = '<div class="news-card"><p>News feed unavailable.</p></div>';
    });
})(window.Hermes);
