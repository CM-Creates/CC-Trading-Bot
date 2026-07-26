window.Hermes = window.Hermes || {};

(function (H) {
  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  H.chartTheme = function () {
    return {
      ink: cssVar('--ink'),
      inkSoft: cssVar('--ink-soft'),
      inkFaint: cssVar('--ink-faint'),
      border: cssVar('--border'),
      accent: cssVar('--accent'),
      accentSoft: cssVar('--accent-soft'),
      gain: cssVar('--gain'),
      loss: cssVar('--loss'),
      bgRaised: cssVar('--bg-raised'),
      bgSunken: cssVar('--bg-sunken'),
    };
  };

  H.baseChartOptions = function (theme) {
    var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    return {
      responsive: true,
      maintainAspectRatio: false,
      animation: reduceMotion ? false : { duration: 700, easing: 'easeOutQuint' },
      plugins: {
        legend: { labels: { color: theme.inkSoft, font: { size: 11 } } },
        tooltip: {
          backgroundColor: theme.bgRaised,
          titleColor: theme.ink,
          bodyColor: theme.inkSoft,
          borderColor: theme.border,
          borderWidth: 1,
        },
      },
      scales: {
        x: { grid: { color: theme.border }, ticks: { color: theme.inkFaint, font: { size: 10 } } },
        y: { grid: { color: theme.border }, ticks: { color: theme.inkFaint, font: { size: 10 } } },
      },
    };
  };
})(window.Hermes);
