window.Hermes = window.Hermes || {};

(function (H) {
  H.fetchData = function (name) {
    return fetch('data/' + name + '.json', { cache: 'no-store' }).then(function (r) {
      if (!r.ok) throw new Error('failed to load ' + name + '.json');
      return r.json();
    });
  };

  function toNum(v) {
    if (v === null || v === undefined) return null;
    var n = typeof v === 'string' ? parseFloat(v.replace(/[^0-9.+-]/g, '')) : v;
    return isNaN(n) ? null : n;
  }
  H.toNum = toNum;

  H.fmtDollar = function (v, signed) {
    var n = toNum(v);
    if (n === null) return '-';
    var prefix = n < 0 ? '-' : (signed && n > 0 ? '+' : '');
    return prefix + '$' + Math.abs(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  H.fmtPct = function (v, signed) {
    var n = toNum(v);
    if (n === null) return '-';
    if (signed === undefined) signed = true;
    var prefix = n < 0 ? '-' : (signed && n > 0 ? '+' : '');
    return prefix + Math.abs(n).toFixed(2) + '%';
  };

  H.pnlClass = function (v) {
    var n = toNum(v);
    if (n === null || n === 0) return 'neutral';
    return n > 0 ? 'gain' : 'loss';
  };

  H.fmtDate = function (iso) {
    if (!iso) return '-';
    var d = new Date(iso + 'T00:00:00Z');
    if (isNaN(d.getTime())) return iso;
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
  };

  H.escapeHtml = function (s) {
    if (s === null || s === undefined) return '';
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  };

  // Escapes HTML, then renders **bold** markdown as <strong> - the source
  // memory logs use ** for emphasis in bullet points.
  H.escapeAndBold = function (s) {
    return H.escapeHtml(s).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  };

  // Parses site_build.py's "YYYY-MM-DD HH:MM UTC" generated_at stamp.
  H.parseGeneratedAt = function (s) {
    if (!s) return null;
    var m = /^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}) UTC$/.exec(s);
    if (!m) return null;
    return new Date(Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]));
  };

  H.fmtRelativeTime = function (generatedAtStr) {
    var d = H.parseGeneratedAt(generatedAtStr);
    if (!d) return 'unknown';
    var diffMs = Date.now() - d.getTime();
    var mins = Math.round(diffMs / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return mins + (mins === 1 ? ' minute ago' : ' minutes ago');
    var hours = Math.round(mins / 60);
    if (hours < 24) return hours + (hours === 1 ? ' hour ago' : ' hours ago');
    var days = Math.round(hours / 24);
    return days + (days === 1 ? ' day ago' : ' days ago');
  };
})(window.Hermes);
