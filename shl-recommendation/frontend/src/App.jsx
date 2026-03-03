import { useState, useEffect, useRef, useCallback } from 'react';

// ─── CONSTANTS ────────────────────────────────────────────────────────────────
const TYPE_CFG = {
  'Ability & Aptitude':              { letter: 'A', cls: 'badge-A', bar: 'bar-blue'   },
  'Biodata & Situational Judgement': { letter: 'B', cls: 'badge-B', bar: 'bar-purple' },
  'Competencies':                    { letter: 'C', cls: 'badge-C', bar: 'bar-green'  },
  'Development & 360':               { letter: 'D', cls: 'badge-D', bar: 'bar-gold'   },
  'Assessment Exercises':            { letter: 'E', cls: 'badge-E', bar: 'bar-orange' },
  'Knowledge & Skills':              { letter: 'K', cls: 'badge-K', bar: 'bar-blue'   },
  'Personality & Behavior':          { letter: 'P', cls: 'badge-P', bar: 'bar-green'  },
  'Simulations':                     { letter: 'S', cls: 'badge-S', bar: 'bar-orange' },
};
const BAR_FALLBACKS = ['bar-blue', 'bar-green', 'bar-orange', 'bar-gold', 'bar-purple'];

const SAMPLE_QUERIES = [
  { emoji: '☕', label: 'Java dev + business collaboration',  text: 'I am hiring for Java developers who can also collaborate effectively with my business teams. Need assessments covering both technical Java skills and behavioral/interpersonal skills.' },
  { emoji: '🐍', label: 'Python, SQL, JavaScript — 60 min',  text: 'Looking to hire mid-level professionals who are proficient in Python, SQL and JavaScript. Need an assessment package that can test all skills with max duration of 60 minutes.' },
  { emoji: '📊', label: 'Analyst — cognitive + personality', text: 'I am hiring for an analyst and want to screen applicants using Cognitive and personality tests. What options are available within 45 mins?' },
  { emoji: '🎯', label: 'Sales graduate — 30 min',           text: 'I am looking for new graduates for my sales team. Suggest a 30 min long assessment covering sales aptitude and personality.' },
  { emoji: '✍️', label: 'Content Writer — SEO + English',    text: 'For Marketing Content Writer position — need assessments for English writing, SEO knowledge, and creative thinking skills.' },
  { emoji: '📞', label: 'Customer support — English comms',  text: 'I want to hire Customer Support executives who are expert in English communication for an India-based international BPO team.' },
];

const LOADING_STEPS = [
  'Understanding query intent',
  'Searching assessment catalog',
  'Ranking by relevance',
  'Balancing skill types',
];

// ─── CUSTOM CURSOR ────────────────────────────────────────────────────────────
function useCursor() {
  const cursorRef = useRef(null);
  const ringRef   = useRef(null);

  useEffect(() => {
    const move = (e) => {
      if (cursorRef.current) { cursorRef.current.style.left = e.clientX + 'px'; cursorRef.current.style.top = e.clientY + 'px'; }
      setTimeout(() => {
        if (ringRef.current) { ringRef.current.style.left = e.clientX + 'px'; ringRef.current.style.top = e.clientY + 'px'; }
      }, 60);
    };
    const down = () => { if (cursorRef.current) { cursorRef.current.style.width = '6px'; cursorRef.current.style.height = '6px'; } };
    const up   = () => { if (cursorRef.current) { cursorRef.current.style.width = '10px'; cursorRef.current.style.height = '10px'; } };
    document.addEventListener('mousemove', move);
    document.addEventListener('mousedown', down);
    document.addEventListener('mouseup', up);
    return () => { document.removeEventListener('mousemove', move); document.removeEventListener('mousedown', down); document.removeEventListener('mouseup', up); };
  }, []);

  const grow   = () => { if (cursorRef.current) { cursorRef.current.style.width='14px'; cursorRef.current.style.height='14px'; } if (ringRef.current) { ringRef.current.style.width='50px'; ringRef.current.style.height='50px'; } };
  const shrink = () => { if (cursorRef.current) { cursorRef.current.style.width='10px'; cursorRef.current.style.height='10px'; } if (ringRef.current) { ringRef.current.style.width='36px'; ringRef.current.style.height='36px'; } };

  return { cursorRef, ringRef, grow, shrink };
}

// ─── TOAST ────────────────────────────────────────────────────────────────────
function useToast() {
  const [toasts, setToasts] = useState([]);
  const show = useCallback((msg, type = '') => {
    const id = Date.now();
    setToasts(t => [...t, { id, msg, type }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3200);
  }, []);
  return { toasts, show };
}

// ─── LOADING OVERLAY ──────────────────────────────────────────────────────────
function LoadingOverlay({ visible }) {
  const [step, setStep] = useState(-1);
  useEffect(() => {
    if (!visible) { setStep(-1); return; }
    const timers = LOADING_STEPS.map((_, i) => setTimeout(() => setStep(i), i * 700));
    return () => timers.forEach(clearTimeout);
  }, [visible]);
  if (!visible) return null;
  return (
    <div className="loading-overlay">
      <div className="loading-orb" />
      <div className="loading-text">Finding best matches</div>
      <div className="loading-subtext">AI is analysing your requirements</div>
      <div className="loading-steps">
        {LOADING_STEPS.map((s, i) => (
          <div key={i} className={`loading-step${i === step ? ' active' : i < step ? ' done' : ''}`}>
            <div className="step-dot" />{s}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── HEADER ───────────────────────────────────────────────────────────────────
function Header({ savedCount, onSavedClick, onSearchClick, grow, shrink }) {
  return (
    <header className="header">
      <a className="logo" href="/" onMouseEnter={grow} onMouseLeave={shrink}>
        <div className="logo-mark">
          <div className="logo-letter s">S</div>
          <div className="logo-letter h">H</div>
          <div className="logo-letter l">L</div>
        </div>
        <div>
          <div className="logo-text">AssessMatch</div>
          <div className="logo-sub">AI Assessment Finder</div>
        </div>
      </a>
      <nav className="header-nav">
        <button className="nav-link" onClick={onSearchClick} onMouseEnter={grow} onMouseLeave={shrink}>Search</button>
        <a className="nav-link" href="https://www.shl.com/solutions/products/product-catalog/" target="_blank" rel="noopener noreferrer" onMouseEnter={grow} onMouseLeave={shrink}>Catalog ↗</a>
        <button className="nav-link" onClick={onSavedClick} onMouseEnter={grow} onMouseLeave={shrink}>Saved ({savedCount})</button>
        <button className="nav-btn" onClick={onSearchClick} onMouseEnter={grow} onMouseLeave={shrink}>Try It Free</button>
      </nav>
    </header>
  );
}

// ─── SEARCH SECTION ───────────────────────────────────────────────────────────
function SearchSection({ onSubmit, queryCount, prefillQuery, grow, shrink }) {
  const [tab,       setTab]   = useState('text');
  const [textQ,     setTextQ] = useState('');
  const [urlQ,      setUrlQ]  = useState('');
  const [maxN,      setMaxN]  = useState(10);
  const [filterType,setFT]    = useState('');
  const [loading,   setLoading] = useState(false);
  const [error,     setError]   = useState('');

  useEffect(() => { if (prefillQuery) { setTab('text'); setTextQ(prefillQuery); } }, [prefillQuery]);

  const query = tab === 'text' ? textQ : urlQ;

  const handleSubmit = async () => {
    if (!query.trim()) { setError('Please enter a job description, query, or URL.'); return; }
    setError(''); setLoading(true);
    try { await onSubmit(query.trim(), maxN, filterType); }
    catch (e) { setError(e.message + ' — make sure the backend is running on port 8000.'); }
    finally { setLoading(false); }
  };

  return (
    <section className="hero" id="search-section">
      <div className="hero-eyebrow"><div className="eyebrow-dot" />Powered by Gemini AI · 377+ Assessments</div>

      <h1 className="hero-title">Find the <em>right tests</em><br />for any role, instantly</h1>

      <p className="hero-desc">
        Describe your hiring need in plain English — or paste a full job description.
        Get intelligently ranked SHL assessments in seconds.
      </p>

      <div className="stats-bar">
        {[{ num: '377+', label: 'Assessments' }, { num: '8', label: 'Test Types' }, { num: 'RAG', label: 'AI Pipeline' }, { num: queryCount, label: 'Queries Run' }]
          .map((s, i) => (
            <div className="stat-item" key={i}>
              <span className="stat-num">{s.num}</span>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
      </div>

      <div className="search-card">
        <div className="search-tabs">
          {[{ id: 'text', icon: '📝', label: 'Job Description / Query' }, { id: 'url', icon: '🔗', label: 'URL' }].map(t => (
            <button key={t.id} className={`search-tab${tab === t.id ? ' active' : ''}`} onClick={() => setTab(t.id)} onMouseEnter={grow} onMouseLeave={shrink}>
              <span className="tab-icon">{t.icon}</span>{t.label}
            </button>
          ))}
        </div>

        <div className="search-body">
          {tab === 'text'
            ? <textarea className="search-textarea" value={textQ} onChange={e => setTextQ(e.target.value)} onKeyDown={e => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') handleSubmit(); }} placeholder={"Describe what you need — e.g. 'I need a Java developer who can also collaborate with business teams. Time limit: 60 min.'"} />
            : <><input type="url" className="search-input-url" value={urlQ} onChange={e => setUrlQ(e.target.value)} onKeyDown={e => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') handleSubmit(); }} placeholder="https://company.com/jobs/software-engineer ..." /><p className="url-hint">We'll fetch and analyse the job description from this URL automatically.</p></>
          }

          <div className="search-footer">
            <div className="search-options">
              <div className="option-group">
                <span className="option-label">Max Results</span>
                <select className="select-pill" value={maxN} onChange={e => setMaxN(+e.target.value)} onMouseEnter={grow} onMouseLeave={shrink}>
                  <option value={5}>5</option><option value={7}>7</option><option value={10}>10</option>
                </select>
              </div>
              <div className="option-group">
                <span className="option-label">Filter Type</span>
                <select className="select-pill" value={filterType} onChange={e => setFT(e.target.value)} onMouseEnter={grow} onMouseLeave={shrink}>
                  <option value="">All Types</option>
                  <option value="K">Knowledge & Skills</option>
                  <option value="P">Personality & Behavior</option>
                  <option value="A">Ability & Aptitude</option>
                  <option value="C">Competencies</option>
                  <option value="B">Biodata & SJT</option>
                </select>
              </div>
            </div>
            <button className="submit-btn" onClick={handleSubmit} disabled={loading || !query.trim()} onMouseEnter={grow} onMouseLeave={shrink}>
              {loading && <div className="btn-spinner" />}
              {loading ? 'Analysing...' : 'Get Recommendations'}
              {!loading && <span className="btn-arrow">→</span>}
            </button>
          </div>

          {error && <div className="error-box"><span className="error-icon">⚠</span><span>{error}</span></div>}
        </div>
      </div>

      <div className="samples-section">
        <div className="samples-header">
          <div className="samples-title">Quick Try</div>
          <div className="samples-line" />
        </div>
        <div className="samples-grid">
          {SAMPLE_QUERIES.map((s, i) => (
            <button key={i} className="sample-chip" onClick={() => { setTab('text'); setTextQ(s.text); }} onMouseEnter={grow} onMouseLeave={shrink}>
              {s.emoji} {s.label}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── TYPE BADGE ───────────────────────────────────────────────────────────────
function TypeBadge({ type }) {
  const cfg = TYPE_CFG[type] || { letter: (type || '?')[0], cls: 'badge-A' };
  return (
    <span className={`type-badge ${cfg.cls}`}>
      <span className="type-letter">{cfg.letter}</span>{type}
    </span>
  );
}

// ─── CARD ─────────────────────────────────────────────────────────────────────
function AssessmentCard({ assessment, rank, isSaved, onSave, onCopy, grow, shrink }) {
  const [expanded, setExpanded] = useState(false);
  const types   = assessment.test_type || [];
  const barCls  = TYPE_CFG[types[0]]?.bar || BAR_FALLBACKS[rank % BAR_FALLBACKS.length];
  const rankCls = rank === 1 ? 'rank-1' : rank === 2 ? 'rank-2' : rank === 3 ? 'rank-3' : 'rank-other';
  const desc    = assessment.description || '';

  return (
    <div className="assessment-card">
      <div className={`card-accent-bar ${barCls}`} />
      <div className="card-top-row">
        <div className="card-name">
          <a href={assessment.url} target="_blank" rel="noopener noreferrer" onMouseEnter={grow} onMouseLeave={shrink}>
            {assessment.name || 'Assessment'}
          </a>
        </div>
        <div className={`card-rank ${rankCls}`}>#{rank}</div>
      </div>

      {types.length > 0 && <div className="type-badges">{types.map((t, i) => <TypeBadge key={i} type={t} />)}</div>}

      <div className="card-meta">
        {assessment.duration > 0 && <span className="meta-chip"><span>⏱</span>{assessment.duration} min</span>}
        <span className={`meta-chip${assessment.remote_support === 'Yes' ? ' good' : ''}`}>
          <span>{assessment.remote_support === 'Yes' ? '💻' : '🏢'}</span>
          {assessment.remote_support === 'Yes' ? 'Remote' : 'In-person'}
        </span>
        {assessment.adaptive_support === 'Yes' && <span className="meta-chip good"><span>🎯</span>Adaptive</span>}
      </div>

      {desc && (
        <>
          <p className={`card-desc${expanded ? ' expanded' : ''}`}>{desc}</p>
          {desc.length > 120 && <button className="read-more-btn" onClick={() => setExpanded(e => !e)} onMouseEnter={grow} onMouseLeave={shrink}>{expanded ? 'Show less ↑' : 'Read more ↓'}</button>}
        </>
      )}

      <div className="card-footer">
        <a className="card-link" href={assessment.url} target="_blank" rel="noopener noreferrer" onMouseEnter={grow} onMouseLeave={shrink}>View Assessment →</a>
        <div className="card-actions">
          <button className={`icon-btn${isSaved ? ' saved' : ''}`} onClick={() => onSave(assessment)} title="Save" onMouseEnter={grow} onMouseLeave={shrink}>📌</button>
          <button className="icon-btn" onClick={() => onCopy(assessment.url)} title="Copy link" onMouseEnter={grow} onMouseLeave={shrink}>🔗</button>
        </div>
      </div>
    </div>
  );
}

// ─── SUMMARY PANEL ────────────────────────────────────────────────────────────
function SummaryPanel({ query, results }) {
  const durations = results.map(r => r.duration).filter(Boolean);
  const avgDur    = durations.length ? Math.round(durations.reduce((a, b) => a + b, 0) / durations.length) : null;
  const typeCounts = {};
  results.forEach(r => (r.test_type || []).forEach(t => { typeCounts[t] = (typeCounts[t] || 0) + 1; }));
  return (
    <div className="summary-panel">
      <div className="summary-query-section">
        <div className="summary-label">Your Query</div>
        <div className="summary-query-text">{query.length > 160 ? query.slice(0, 160) + '...' : query}</div>
      </div>
      <div className="type-dist-section">
        <div className="summary-label">Type Distribution</div>
        <div className="type-distribution">
          {Object.entries(typeCounts).sort((a, b) => b[1] - a[1]).map(([t, c]) => (
            <div key={t} className="dist-badge">{TYPE_CFG[t]?.letter || t[0]} × {c}</div>
          ))}
        </div>
      </div>
      <div className="summary-stats">
        <div className="summary-stat"><span className="summary-stat-num">{results.length}</span><span className="summary-stat-label">Results</span></div>
        <div className="summary-stat"><span className="summary-stat-num">{avgDur ?? '—'}</span><span className="summary-stat-label">Avg Min</span></div>
      </div>
    </div>
  );
}

// ─── RESULTS SECTION ──────────────────────────────────────────────────────────
function ResultsSection({ results, query, savedItems, onSave, onReset, showToast, grow, shrink }) {
  const [view, setView] = useState('grid');
  const [sort, setSort] = useState('rank');

  const sorted = [...results].sort((a, b) => {
    if (sort === 'duration_asc')  return (a.duration || 999) - (b.duration || 999);
    if (sort === 'duration_desc') return (b.duration || 0)   - (a.duration || 0);
    if (sort === 'name')          return (a.name || '').localeCompare(b.name || '');
    return 0;
  });

  const dlFile = (name, content) => { const a = document.createElement('a'); a.href = 'data:text/plain;charset=utf-8,' + encodeURIComponent(content); a.download = name; a.click(); };
  const exportCSV  = () => { dlFile('shl_predictions.csv',      ['Query,Assessment_url', ...results.map(r => `"${query.replace(/"/g,'""')}","${r.url}"`)].join('\n')); showToast('CSV exported!', 'success'); };
  const exportJSON = () => { dlFile('shl_recommendations.json', JSON.stringify({ query, recommended_assessments: results }, null, 2)); showToast('JSON exported!', 'success'); };
  const copyURLs   = () => { navigator.clipboard.writeText(results.map(r => r.url).join('\n')).then(() => showToast('URLs copied!', 'success')); };
  const copyLink   = (url) => { navigator.clipboard.writeText(url).then(() => showToast('Link copied!')); };

  return (
    <section className="results-section">
      <SummaryPanel query={query} results={results} />

      <div className="toolbar">
        <div className="export-btns">
          <button className="export-btn" onClick={exportCSV}  onMouseEnter={grow} onMouseLeave={shrink}><span className="e-icon">📄</span>Export CSV</button>
          <button className="export-btn" onClick={exportJSON} onMouseEnter={grow} onMouseLeave={shrink}><span className="e-icon">&#123;&#125;</span>Export JSON</button>
          <button className="export-btn" onClick={copyURLs}   onMouseEnter={grow} onMouseLeave={shrink}><span className="e-icon">🔗</span>Copy URLs</button>
        </div>
        <div className="right-controls">
          <select className="sort-select" value={sort} onChange={e => setSort(e.target.value)} onMouseEnter={grow} onMouseLeave={shrink}>
            <option value="rank">Sort: Relevance</option>
            <option value="duration_asc">Duration: Short → Long</option>
            <option value="duration_desc">Duration: Long → Short</option>
            <option value="name">Name A–Z</option>
          </select>
          <div className="view-toggle">
            <button className={`view-btn${view === 'grid' ? ' active' : ''}`} onClick={() => setView('grid')} onMouseEnter={grow} onMouseLeave={shrink}>⊞</button>
            <button className={`view-btn${view === 'list' ? ' active' : ''}`} onClick={() => setView('list')} onMouseEnter={grow} onMouseLeave={shrink}>≡</button>
          </div>
          <button className="reset-btn" onClick={onReset} onMouseEnter={grow} onMouseLeave={shrink}>New Search</button>
        </div>
      </div>

      <div className={`results-grid${view === 'list' ? ' list-view' : ''}`}>
        {sorted.map((a, i) => (
          <AssessmentCard key={a.url + i} assessment={a} rank={i + 1}
            isSaved={savedItems.some(s => s.url === a.url)}
            onSave={onSave} onCopy={copyLink} grow={grow} shrink={shrink} />
        ))}
      </div>
    </section>
  );
}

// ─── HISTORY ──────────────────────────────────────────────────────────────────
function HistorySection({ history, onRerun, grow, shrink }) {
  if (!history.length) return null;
  return (
    <section className="history-section">
      <div className="history-title">Recent Searches</div>
      <div className="history-list">
        {history.map((h, i) => (
          <div key={i} className="history-item" onClick={() => onRerun(h.query)} onMouseEnter={grow} onMouseLeave={shrink}>
            <span className="history-query">{h.query.length > 90 ? h.query.slice(0, 90) + '...' : h.query}</span>
            <span className="history-time">{h.time}</span>
            <button className="history-rerun-btn" onMouseEnter={grow} onMouseLeave={shrink}>Run again →</button>
          </div>
        ))}
      </div>
    </section>
  );
}

// ─── SAVED SIDEBAR ────────────────────────────────────────────────────────────
function SavedSidebar({ open, onClose, savedItems, onClear, onExport, grow, shrink }) {
  return (
    <div className={`sidebar-overlay${open ? ' open' : ''}`} onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="saved-sidebar">
        <div className="sidebar-header">
          <div className="sidebar-title">Saved</div>
          <button className="close-btn" onClick={onClose} onMouseEnter={grow} onMouseLeave={shrink}>×</button>
        </div>
        {!savedItems.length
          ? <div className="saved-empty">📌 Nothing saved yet.<br />Click the bookmark icon on any card.</div>
          : savedItems.map((s, i) => (
              <div key={i} className="saved-item">
                <div className="saved-item-name">{s.name}</div>
                <div className="saved-item-url">{s.url}</div>
              </div>
            ))
        }
        {savedItems.length > 0 && (
          <div className="saved-footer-btns">
            <button className="saved-action-btn" onClick={onExport} onMouseEnter={grow} onMouseLeave={shrink}>Export CSV</button>
            <button className="saved-action-btn" onClick={onClear}  onMouseEnter={grow} onMouseLeave={shrink}>Clear All</button>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── APP ──────────────────────────────────────────────────────────────────────
export default function App() {
  const { cursorRef, ringRef, grow, shrink } = useCursor();
  const { toasts, show: showToast }          = useToast();

  const [results,     setResults]     = useState([]);
  const [currentQ,    setCurrentQ]    = useState('');
  const [loading,     setLoading]     = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [prefillQ,    setPrefillQ]    = useState('');
  const [savedItems,  setSavedItems]  = useState(() => JSON.parse(localStorage.getItem('shl_saved')    || '[]'));
  const [history,     setHistory]     = useState(() => JSON.parse(localStorage.getItem('shl_history')  || '[]'));
  const [queryCount,  setQueryCount]  = useState(() => parseInt(localStorage.getItem('shl_queryCount') || '0'));

  useEffect(() => { localStorage.setItem('shl_saved',      JSON.stringify(savedItems));  }, [savedItems]);
  useEffect(() => { localStorage.setItem('shl_history',    JSON.stringify(history));     }, [history]);
  useEffect(() => { localStorage.setItem('shl_queryCount', String(queryCount));          }, [queryCount]);

  // API health check
  useEffect(() => {
    fetch('/health').then(r => r.json())
      .then(d => { if (d.status === 'healthy') showToast('API connected ✓', 'success'); })
      .catch(() => showToast('API offline — start the backend on port 8000', 'error'));
  // eslint-disable-next-line
  }, []);

  const handleSubmit = async (query, maxN, filterType) => {
    setLoading(true);
    try {
      const res = await fetch('/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || `HTTP ${res.status}`); }
      const data = await res.json();
      let recs = data.recommended_assessments || [];
      if (filterType) {
        const lbl = { K: 'Knowledge', P: 'Personality', A: 'Ability', C: 'Competencies', B: 'Biodata' };
        recs = recs.filter(r => (r.test_type || []).some(t => t.includes(lbl[filterType] || filterType)));
      }
      recs = recs.slice(0, maxN);
      setResults(recs); setCurrentQ(query); setShowResults(true);
      setQueryCount(c => c + 1);
      setHistory(h => [{ query, time: new Date().toLocaleTimeString() }, ...h].slice(0, 5));
      showToast(`${recs.length} assessments found!`, 'success');
      setTimeout(() => document.getElementById('results-top')?.scrollIntoView({ behavior: 'smooth' }), 200);
    } finally { setLoading(false); }
  };

  const handleSave = (item) => {
    setSavedItems(prev => {
      const exists = prev.findIndex(s => s.url === item.url);
      if (exists >= 0) { showToast('Removed from saved'); return prev.filter((_, i) => i !== exists); }
      showToast('Saved! 📌');
      return [...prev, { name: item.name, url: item.url, test_type: item.test_type }];
    });
  };

  const exportSaved = () => {
    if (!savedItems.length) { showToast('Nothing saved', 'error'); return; }
    const a = document.createElement('a');
    a.href = 'data:text/plain;charset=utf-8,' + encodeURIComponent(['name,url', ...savedItems.map(s => `"${s.name}","${s.url}"`)].join('\n'));
    a.download = 'shl_saved.csv'; a.click();
    showToast('Exported!', 'success');
  };

  const handleReset = () => { setShowResults(false); setResults([]); setCurrentQ(''); document.getElementById('search-section')?.scrollIntoView({ behavior: 'smooth' }); showToast('Ready for a new search!'); };
  const scrollToSearch = () => document.getElementById('search-section')?.scrollIntoView({ behavior: 'smooth' });

  return (
    <>
      <div className="cursor"      ref={cursorRef} />
      <div className="cursor-ring" ref={ringRef}   />
      <div className="noise-overlay" />
      <div className="bg-blobs">
        <div className="blob blob-1" /><div className="blob blob-2" /><div className="blob blob-3" />
      </div>

      <LoadingOverlay visible={loading} />

      <SavedSidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)}
        savedItems={savedItems} onClear={() => { setSavedItems([]); showToast('Cleared'); }}
        onExport={exportSaved} grow={grow} shrink={shrink} />

      <div className="toast-container">
        {toasts.map(t => <div key={t.id} className={`toast ${t.type}`}>{t.msg}</div>)}
      </div>

      <div className="page-wrapper">
        <Header savedCount={savedItems.length} onSavedClick={() => setSidebarOpen(true)} onSearchClick={scrollToSearch} grow={grow} shrink={shrink} />

        <SearchSection onSubmit={handleSubmit} queryCount={queryCount} prefillQuery={prefillQ} grow={grow} shrink={shrink} />

        {history.length > 0 && !showResults && (
          <HistorySection history={history} onRerun={q => { setPrefillQ(q); scrollToSearch(); showToast('Query loaded!'); }} grow={grow} shrink={shrink} />
        )}

        {showResults && (
          <div id="results-top">
            <ResultsSection results={results} query={currentQ} savedItems={savedItems}
              onSave={handleSave} onReset={handleReset} showToast={showToast} grow={grow} shrink={shrink} />
          </div>
        )}

        <footer className="footer">
          <span>© 2025 SHL AssessMatch · Powered by Gemini AI</span>
          <span><a href="https://www.shl.com/solutions/products/product-catalog/" target="_blank" rel="noopener noreferrer">View Full Catalog ↗</a></span>
        </footer>
      </div>
    </>
  );
}
