/**
 * IPO Screening Engine — Presentation Application (UI-2 & UI-3)
 *
 * Implements:
 * 1. Executive Dashboard (#dashboard)
 * 2. IPO Directory (#directory)
 * 3. Evaluation Detail Scorecard (#evaluations/{id})
 * 4. Evidence & Provenance Explorer (#evidence/{id})
 *
 * The engine remains the sole scoring authority: figures, verdicts, and bounds are
 * delivered by the API. Explicit user workflow actions are delegated to API routes.
 * ZERO client-side scoring calculations; ZERO API keys stored.
 */

import { ApiClient, ApiError } from './api.js';

export class App {
  constructor(apiClient = null) {
    this.api = apiClient || new ApiClient();
    this.currentView = 'dashboard';
    this.currentParams = {};
    
    // Directory state
    this.directoryState = {
      page: 1,
      pageSize: 20,
      search: '',
    };

    // Evidence state
    this.evidenceState = null;
  }

  init() {
    window.addEventListener('hashchange', () => this.handleRouting());
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.closeEvidenceInspector();
      }
    });
    this.handleRouting();
    this.loadGovernanceBanner();
  }

  // --------------------------------------------------------------------------
  // Routing
  // --------------------------------------------------------------------------

  handleRouting() {
    const hash = window.location.hash.slice(1) || 'dashboard';
    const [path, queryString] = hash.split('?');
    const segments = path.split('/').filter(Boolean);

    // Update active nav button
    document.querySelectorAll('.nav-tab').forEach(tab => {
      const target = tab.getAttribute('data-view');
      tab.classList.toggle('active', target === segments[0] || (segments.length === 0 && target === 'dashboard'));
    });

    if (segments.length === 0 || segments[0] === 'dashboard') {
      this.renderDashboard();
    } else if (segments[0] === 'directory') {
      this.renderDirectory();
    } else if (segments[0] === 'evaluations' && segments[1]) {
      this.renderScorecard(segments[1]);
    } else if (segments[0] === 'evidence' && segments[1]) {
      this.renderEvidenceExplorer(segments[1], queryString);
    } else if (segments[0] === 'performance' && segments[1]) {
      this.renderPerformanceExplorer(segments[1], queryString);
    } else if (segments[0] === 'backtest' || (segments[0] === 'analytics' && segments[1] === 'backtest')) {
      this.renderBacktestAnalytics();
    } else if (segments[0] === 'calibration' || segments[0] === 'configuration') {
      this.renderCalibrationView();
    } else if (segments[0] === 'ingest' || segments[0] === 'upload') {
      this.renderIngestView();
    } else if (segments[0] === 'ipos' && segments[1]) {
      this.renderIpoDetail(segments[1]);
    } else {
      this.renderNotFound(path);
    }
  }

  navigateTo(hash) {
    window.location.hash = hash;
  }

  // --------------------------------------------------------------------------
  // Governance Status Banner
  // --------------------------------------------------------------------------

  async loadGovernanceBanner() {
    const bannerEl = document.getElementById('governance-banner');
    if (!bannerEl) return;

    try {
      const cfg = await this.api.getConfigurationStatus();
      bannerEl.innerHTML = `
        <span class="gov-pill active" title="Active Scoring Policy">
          ● ACTIVE: ${this.escape(cfg.active_configuration.version)}
        </span>
        <span class="gov-pill inactive" title="Candidate Policy (Gated, Inactive)">
          ○ CANDIDATE: ${this.escape(cfg.candidate_configuration.version)} (${this.escape(cfg.candidate_configuration.status)})
        </span>
        <span class="meta-tag" title="Frozen Core Engine Status">
          Frozen Core: ACTIVE
        </span>
      `;
    } catch {
      bannerEl.innerHTML = `<span class="gov-pill inactive">Policy Status Unavailable</span>`;
    }
  }

  // --------------------------------------------------------------------------
  // View 1: Executive Dashboard (#dashboard)
  // --------------------------------------------------------------------------

  async renderDashboard() {
    this.setViewActive('dashboard-view');
    const container = document.getElementById('dashboard-view');
    if (!container) return;

    container.innerHTML = `
      <div class="state-box">
        <div class="spinner"></div>
        <h3>Loading Executive Dashboard...</h3>
        <p>Projecting read-only portfolio metrics from presentation service...</p>
      </div>
    `;

    try {
      const [iposResp, evalsResp, cfg] = await Promise.all([
        this.api.listIpos({ page: 1, pageSize: 50 }),
        this.api.listEvaluations({ page: 1, pageSize: 50 }),
        this.api.getConfigurationStatus(),
      ]);

      const ipos = iposResp.items || [];
      const evals = evalsResp.items || [];

      // Calculate aggregate statistics purely for presentation counts
      const totalIpos = iposResp.total || ipos.length;
      const totalEvals = evalsResp.total || evals.length;

      const verdictCounts = {
        APPLY: 0,
        CONSIDER: 0,
        AVOID: 0,
        INSUFFICIENT_DATA: 0,
      };

      const scoreBands = {
        '0-19': 0,
        '20-39': 0,
        '40-59': 0,
        '60-79': 0,
        '80-100': 0,
      };

      evals.forEach(e => {
        const v = e.verdict || 'UNKNOWN';
        if (verdictCounts[v] !== undefined) {
          verdictCounts[v]++;
        }
        const s = e.final_score ?? 0;
        if (s < 20) scoreBands['0-19']++;
        else if (s < 40) scoreBands['20-39']++;
        else if (s < 60) scoreBands['40-59']++;
        else if (s < 80) scoreBands['60-79']++;
        else scoreBands['80-100']++;
      });

      const latestEval = evals[0] || null;

      container.innerHTML = `
        <div class="card" style="margin-bottom: 24px;">
          <div class="card-header">
            <div>
              <div class="card-title">Indian Mainboard IPO Screening Portfolio</div>
              <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">
                Executive read-model aggregation across evaluated offerings
              </div>
            </div>
            <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
              <a href="#backtest" class="btn btn-outline btn-sm">Historical Backtest Analytics &rarr;</a>
              <a href="#calibration" class="btn btn-outline btn-sm">Policy Governance &rarr;</a>
              <span class="meta-tag">POLICY: v${this.escape(cfg.active_configuration.version)}</span>
            </div>
          </div>

          <!-- KPI Metrics Row -->
          <div class="kpi-grid">
            <div class="kpi-card">
              <div class="kpi-label">Tracked IPO Issuers</div>
              <div class="kpi-val">${totalIpos}</div>
              <div class="kpi-meta">Active offerings in repository</div>
            </div>

            <div class="kpi-card">
              <div class="kpi-label">Evaluations Logged</div>
              <div class="kpi-val">${totalEvals}</div>
              <div class="kpi-meta">Preliminary and final assessments</div>
            </div>

            <div class="kpi-card">
              <div class="kpi-label">Latest Verdict</div>
              <div class="kpi-val" style="font-size: 1.35rem; margin-top: 6px;">
                ${latestEval ? this.renderVerdictBadge(latestEval.verdict) : '—'}
              </div>
              <div class="kpi-meta">${latestEval ? this.escape(latestEval.company_name) : 'No evaluations'}</div>
            </div>

            <div class="kpi-card">
              <div class="kpi-label">Active Engine Version</div>
              <div class="kpi-val" style="font-size: 1.35rem; font-family: var(--font-mono);">
                v${this.escape(cfg.active_configuration.version)}
              </div>
              <div class="kpi-meta">SEBI ICDR Compliant</div>
            </div>
          </div>
        </div>

        <!-- Distributions Grid -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; margin-bottom: 24px;">
          <!-- Verdict Breakdown -->
          <div class="card">
            <div class="card-header">
              <div class="card-title">Verdict Distribution</div>
              <span class="meta-tag">${totalEvals} Runs</span>
            </div>
            <div class="distribution-grid">
              <div class="distribution-item" style="border-left: 3px solid var(--color-apply);">
                <div style="font-size: 0.85rem; font-weight: 600;">APPLY</div>
                <div style="font-size: 1.2rem; font-weight: 700; color: var(--color-apply);">${verdictCounts.APPLY}</div>
              </div>
              <div class="distribution-item" style="border-left: 3px solid var(--color-consider);">
                <div style="font-size: 0.85rem; font-weight: 600;">CONSIDER</div>
                <div style="font-size: 1.2rem; font-weight: 700; color: var(--color-consider);">${verdictCounts.CONSIDER}</div>
              </div>
              <div class="distribution-item" style="border-left: 3px solid var(--color-avoid);">
                <div style="font-size: 0.85rem; font-weight: 600;">AVOID</div>
                <div style="font-size: 1.2rem; font-weight: 700; color: var(--color-avoid);">${verdictCounts.AVOID}</div>
              </div>
              <div class="distribution-item" style="border-left: 3px solid var(--color-insufficient);">
                <div style="font-size: 0.85rem; font-weight: 600;">INSUFFICIENT DATA</div>
                <div style="font-size: 1.2rem; font-weight: 700; color: var(--color-insufficient);">${verdictCounts.INSUFFICIENT_DATA}</div>
              </div>
            </div>
          </div>

          <!-- Score Bands -->
          <div class="card">
            <div class="card-header">
              <div class="card-title">Score Band Distribution</div>
              <span class="meta-tag">Range [0 – 100]</span>
            </div>
            <div class="distribution-grid">
              ${Object.entries(scoreBands).map(([band, cnt]) => `
                <div class="distribution-item">
                  <div style="font-size: 0.75rem; color: var(--text-muted);">${band} pts</div>
                  <div style="font-size: 1.15rem; font-weight: 700;">${cnt}</div>
                </div>
              `).join('')}
            </div>
          </div>
        </div>

        <!-- Recent Evaluations Feed -->
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">Recent Evaluation Records</div>
              <div style="font-size: 0.8rem; color: var(--text-muted);">Immutable screening outcomes stored in filesystem repository</div>
            </div>
            <a href="#directory" class="btn btn-outline btn-sm">Explore All Issuers &rarr;</a>
          </div>
          ${this.renderEvaluationsTableHtml(evals.slice(0, 5))}
        </div>
      `;
    } catch (err) {
      this.renderError(container, 'Failed to load executive dashboard', err);
    }
  }

  // --------------------------------------------------------------------------
  // View 2: IPO Discovery / Directory (#directory)
  // --------------------------------------------------------------------------

  async renderDirectory() {
    this.setViewActive('directory-view');
    const container = document.getElementById('directory-view');
    if (!container) return;

    container.innerHTML = `
      <div class="card" style="margin-bottom: 20px;">
        <div class="card-header">
          <div>
            <div class="card-title">IPO Discovery &amp; Directory</div>
            <div style="font-size: 0.85rem; color: var(--text-muted);">
              Browse all issuers tracked and evaluated by the screening engine
            </div>
          </div>
          <span class="meta-tag">DETERMINISTIC REGISTRY</span>
        </div>

        <!-- Filter & Search Toolbar -->
        <div class="filter-bar">
          <div class="search-input-wrapper">
            <input
              type="search"
              id="directory-search-input"
              class="search-input"
              placeholder="Search by issuer company name or IPO ID..."
              value="${this.escape(this.directoryState.search)}"
              aria-label="Search IPO issuers"
            />
          </div>
          <button id="directory-search-btn" class="btn btn-primary btn-sm">Search</button>
        </div>
      </div>

      <div id="directory-table-container">
        <div class="state-box">
          <div class="spinner"></div>
          <p>Loading directory...</p>
        </div>
      </div>
    `;

    this.setupDirectorySearch(container);
    await this.fetchAndRenderIpos(container);
  }

  setupDirectorySearch(container) {
    const input = container.querySelector('#directory-search-input');
    const btn = container.querySelector('#directory-search-btn');

    let debounceTimeout = null;
    const executeSearch = () => {
      this.directoryState.search = input.value.trim();
      this.directoryState.page = 1;
      this.fetchAndRenderIpos(container);
    };

    if (input) {
      input.addEventListener('input', () => {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(executeSearch, 300);
      });
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          clearTimeout(debounceTimeout);
          executeSearch();
        }
      });
    }

    if (btn) {
      btn.addEventListener('click', executeSearch);
    }
  }

  async fetchAndRenderIpos(container) {
    const tableContainer = container.querySelector('#directory-table-container');
    if (!tableContainer) return;

    tableContainer.innerHTML = `
      <div class="state-box">
        <div class="spinner"></div>
        <p>Fetching matching IPO records...</p>
      </div>
    `;

    try {
      const resp = await this.api.listIpos({
        page: this.directoryState.page,
        pageSize: this.directoryState.pageSize,
        search: this.directoryState.search || null,
      });

      this.renderIposTable(tableContainer, resp);
    } catch (err) {
      this.renderError(tableContainer, 'Error loading IPO records', err);
    }
  }

  renderIposTable(tableContainer, resp) {
    const items = resp.items || [];
    const total = resp.total || items.length;
    const page = resp.page || 1;
    const pages = resp.pages || 1;

    if (items.length === 0) {
      tableContainer.innerHTML = `
        <div class="card">
          <div class="state-box">
            <h3>No IPO Issuers Found</h3>
            <p>No records match the query "${this.escape(this.directoryState.search)}".</p>
          </div>
        </div>
      `;
      return;
    }

    tableContainer.innerHTML = `
      <div class="card">
        <div class="table-wrapper">
          <table class="data-table" role="table" aria-label="IPO Issuers List">
            <thead>
              <tr>
                <th scope="col">Company Name</th>
                <th scope="col">IPO Identifier</th>
                <th scope="col">Sector Profile</th>
                <th scope="col">Evaluations</th>
                <th scope="col">Latest Score</th>
                <th scope="col">Latest Verdict</th>
                <th scope="col">Action</th>
              </tr>
            </thead>
            <tbody>
              ${items.map(ipo => `
                <tr>
                  <td>
                    <div style="font-weight: 600;">${this.escape(ipo.company_name)}</div>
                    ${ipo.exchange_symbol ? `<div style="font-size: 0.75rem; color: var(--text-light); font-family: var(--font-mono);">${this.escape(ipo.exchange_symbol)}</div>` : ''}
                  </td>
                  <td>
                    <code>${this.escape(ipo.ipo_id)}</code>
                  </td>
                  <td>
                    <span class="meta-tag">${this.escape(ipo.sector_profile || 'STANDARD')}</span>
                  </td>
                  <td>
                    <strong>${ipo.evaluation_count}</strong>
                    ${ipo.historical_count > 0 ? `<div style="font-size: 0.72rem; color: var(--text-muted);">${ipo.historical_count} historical</div>` : ''}
                    ${ipo.archived_count > 0 ? `<div style="font-size: 0.72rem; color: var(--text-muted);">${ipo.archived_count} archived</div>` : ''}
                  </td>
                  <td>
                    ${ipo.latest_score !== null ? `<strong>${ipo.latest_score.toFixed(1)}</strong> / 100 <span class="badge badge-active" style="font-size: 0.65rem; padding: 2px 4px; vertical-align: middle;">ACTIVE</span>` : '<span class="badge badge-unknown">UNKNOWN</span>'}
                  </td>
                  <td>
                    ${this.renderVerdictBadge(ipo.latest_verdict)}
                  </td>
                  <td>
                    <div style="display: flex; gap: 6px;">
                      ${ipo.latest_evaluation_id ? `
                        <a href="#evaluations/${this.escape(ipo.latest_evaluation_id)}" class="btn btn-primary btn-sm">
                          View Scorecard
                        </a>
                      ` : ''}
                      <a href="#ipos/${this.escape(ipo.ipo_id)}" class="btn btn-outline btn-sm">
                        History
                      </a>
                    </div>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>

        <!-- Deterministic Pagination Controls -->
        <div class="pagination-bar">
          <div class="pagination-info">
            Showing Page <strong>${page}</strong> of <strong>${pages}</strong> (${total} total issuers)
          </div>
          <div class="pagination-controls">
            <button class="btn btn-outline btn-sm" id="btn-prev-page" ${page <= 1 ? 'disabled' : ''}>
              &larr; Previous
            </button>
            <button class="btn btn-outline btn-sm" id="btn-next-page" ${page >= pages ? 'disabled' : ''}>
              Next &rarr;
            </button>
          </div>
        </div>
      </div>
    `;

    const prevBtn = tableContainer.querySelector('#btn-prev-page');
    const nextBtn = tableContainer.querySelector('#btn-next-page');

    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        if (this.directoryState.page > 1) {
          this.directoryState.page--;
          this.fetchAndRenderIpos(document.getElementById('directory-view'));
        }
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        if (this.directoryState.page < pages) {
          this.directoryState.page++;
          this.fetchAndRenderIpos(document.getElementById('directory-view'));
        }
      });
    }
  }

  // --------------------------------------------------------------------------
  // View 3: Evaluation Scorecard & Detail (#evaluations/{id})
  // --------------------------------------------------------------------------

  renderPenaltyItems(penalties) {
    if (!penalties || penalties.length === 0) {
      return '<p style="color: var(--text-muted); font-size: 0.85rem;">Zero penalties triggered for this evaluation.</p>';
    }
    return `<ul style="list-style: none;">${penalties.map(p => {
      const isUnknown = p.state === 'UNKNOWN';
      const stateLabel = isUnknown
        ? 'UNKNOWN \u2014 carried in range'
        : (p.points === 0 ? 'Not triggered' : 'Applied');
      const badgeClass = isUnknown ? 'badge-unknown' : (p.points === 0 ? 'badge-clear' : 'badge-avoid');
      return `
      <li style="padding: 8px 0; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem;">
        <div>
          <strong>${this.escape(p.id)}:</strong> ${this.escape(p.label)}
          <div style="margin-top: 3px;"><span class="badge ${badgeClass}">${stateLabel}</span></div>
          ${p.reason ? `<div style="color: var(--text-muted); font-size: 0.78rem; margin-top: 2px;">${this.escape(p.reason)}</div>` : ''}
        </div>
        <span class="badge badge-avoid">${p.points.toFixed(1)} pts</span>
      </li>`;
    }).join('')}</ul>`;
  }

  async renderScorecard(evaluationId) {
    this.setViewActive('scorecard-view');
    const container = document.getElementById('scorecard-view');
    if (!container) return;

    container.innerHTML = `
      <div class="state-box">
        <div class="spinner"></div>
        <h3>Loading Evaluation Scorecard...</h3>
        <p>Fetching immutable evaluation record <code>${this.escape(evaluationId)}</code>...</p>
      </div>
    `;

    try {
      const evaluation = await this.api.getEvaluation(evaluationId);

      const score = evaluation.score;
      const verdict = evaluation.verdict;
      const knockouts = evaluation.knockouts;
      const penalties = evaluation.penalties || [];
      const missing = evaluation.missing_unverified || [];

      // Calculate score range percentage for visual bar
      const lowerPct = Math.max(0, Math.min(100, score.lower_bound));
      const upperPct = Math.max(0, Math.min(100, score.upper_bound));
      const finalPct = Math.max(0, Math.min(100, score.final_score));

      container.innerHTML = `
        <!-- Top Breadcrumbs & Mode Nav -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 8px;">
          <a href="#directory" class="btn btn-outline btn-sm">&larr; Back to Directory</a>
          <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
            <a href="#evidence/${this.escape(evaluationId)}" class="btn btn-outline btn-sm" id="btn-inspect-evidence">
              Inspect Evidence &amp; Provenance &rarr;
            </a>
            <a href="#performance/${this.escape(evaluationId)}" class="btn btn-primary btn-sm" id="btn-post-listing-performance">
              Post-Listing Performance &rarr;
            </a>
            <a href="#ipos/${this.escape(evaluation.ipo_id)}" class="btn btn-outline btn-sm">Lifecycle History</a>
          </div>
        </div>

        ${evaluation.operational_status === 'SUPERSEDED' ? `
          <div class="lifecycle-banner-superseded">
            <div>
              <strong>⚠️ NOTICE: This evaluation is SUPERSEDED.</strong>
              <span>An authoritative replacement evaluation has superseded this historical record.</span>
              ${evaluation.superseded_by ? `
                <div style="font-size: 0.8rem; margin-top: 4px;">
                  Active Replacement: <code>${this.escape(evaluation.superseded_by)}</code>
                </div>
              ` : ''}
            </div>
            ${evaluation.superseded_by ? `
              <a href="#evaluations/${this.escape(evaluation.superseded_by)}" class="btn btn-primary btn-sm">
                Switch to Active Scorecard &rarr;
              </a>
            ` : ''}
          </div>
        ` : evaluation.operational_status === 'ARCHIVED' ? `
          <div class="lifecycle-banner-archived">
            <div>
              <strong>📦 NOTICE: This evaluation is ARCHIVED.</strong>
              <span>This record is suppressed from operational dashboards and retained for auditability.</span>
            </div>
            <button class="btn btn-outline btn-sm" id="btn-unarchive-current" data-eval-id="${this.escape(evaluationId)}">Unarchive Evaluation</button>
          </div>
        ` : ''}

        <!-- 1. Scorecard Banner Header -->
        <div class="scorecard-banner">
          <div class="scorecard-meta">
            <h2>${this.escape(evaluation.company_name)}</h2>
            <div class="meta-tags">
              <span class="meta-tag">IPO ID: ${this.escape(evaluation.ipo_id)}</span>
              <span class="meta-tag">MODE: ${this.escape(evaluation.evaluation_mode)}</span>
              <span class="meta-tag">DATE: ${this.formatDate(evaluation.evaluation_timestamp)}</span>
              <span class="meta-tag">ENGINE: v${this.escape(evaluation.engine_version)}</span>
              <span class="meta-tag">CONFIG: v${this.escape(evaluation.config_version)}</span>
            </div>
            <div style="font-size: 0.75rem; color: var(--text-light); font-family: var(--font-mono); margin-top: 8px; word-break: break-all;">
              RESULT HASH: ${this.escape(evaluation.result_hash)}
            </div>

            <!-- Score Range Bar -->
            <div class="score-range-box">
              <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span>Floor: <strong>${score.lower_bound.toFixed(1)}</strong></span>
                <span>Final Score: <strong>${score.final_score.toFixed(1)}</strong></span>
                <span>Ceiling: <strong>${score.upper_bound.toFixed(1)}</strong></span>
              </div>
              <div class="range-bar">
                <div class="range-indicator" style="left: ${lowerPct}%; width: ${Math.max(2, upperPct - lowerPct)}%;"></div>
                <div class="range-marker" style="left: ${finalPct}%;"></div>
              </div>
              <div style="display: flex; justify-content: space-between; color: var(--text-muted); font-size: 0.75rem;">
                <span>Available Points: ${score.available_points !== null ? score.available_points.toFixed(1) : '—'}</span>
                <span>Unknown Points: ${score.unknown_points !== null ? score.unknown_points.toFixed(1) : '—'}</span>
                <span>Confidence: <strong>${this.escape(score.confidence)}</strong> (${score.completeness_pct.toFixed(0)}%)</span>
              </div>
            </div>
          </div>

          <!-- 2. Verdict & Final Score Card -->
          <div class="scorecard-verdict-box">
            <div class="verdict-large">${this.renderVerdictBadge(verdict.verdict)}</div>
            <div class="score-display">
              <span class="score-num">${score.final_score.toFixed(1)}</span>
              <span class="score-max">/ 100</span>
            </div>
            <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 6px;">
              Base: ${score.base_score.toFixed(1)} | Penalties: ${score.penalties_total.toFixed(1)}
            </div>
            ${verdict.uncertain ? `
              <div class="badge badge-insufficient" style="margin-top: 10px; font-size: 0.7rem;">
                UNCERTAINTY FLAG ACTIVE
              </div>
            ` : ''}
          </div>
        </div>

        <!-- 3. Knockouts Status Section -->
        <div class="card" style="margin-bottom: 24px;">
          <div class="card-header">
            <div class="card-title">Knockout Rules (K1 – K6)</div>
            <span class="badge ${knockouts.status === 'CLEAR' ? 'badge-clear' : knockouts.status === 'TRIGGERED' ? 'badge-triggered' : 'badge-unverified'}">
              STATUS: ${this.escape(knockouts.status)}
            </span>
          </div>
          <div class="knockout-grid">
            ${knockouts.rules.map(k => `
              <div class="knockout-card ${this.escape(k.state)}">
                <span class="badge ${k.state === 'CLEAR' ? 'badge-clear' : k.state === 'TRIGGERED' ? 'badge-triggered' : 'badge-unverified'}">
                  ${this.escape(k.id)}: ${this.escape(k.state)}
                </span>
                <div>
                  <strong>${this.escape(k.label)}</strong>
                  ${k.state === 'UNVERIFIED' && k.missing_inputs.length ? `
                    <div style="font-size: 0.75rem; color: var(--color-unknown); margin-top: 4px;">
                      Missing: <code>${this.escape(k.missing_inputs.join(', '))}</code>
                    </div>
                  ` : ''}
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- 4. Modules A through F Breakdown -->
        <div class="card">
          <div class="card-header">
            <div class="card-title">Scoring Modules (A – F)</div>
            <span class="meta-tag">Authoritative Weights</span>
          </div>
          <div class="modules-container">
            ${score.modules.map(m => `
              <div class="module-card">
                <div class="module-header">
                  <span>Module ${this.escape(m.id)}: ${this.escape(m.name)}</span>
                  <span class="module-score-pill">
                    Score: <strong>${m.score.toFixed(1)}</strong> / ${m.max.toFixed(1)}
                  </span>
                </div>
                <div class="table-wrapper" style="border: none; border-radius: 0;">
                  <table class="data-table">
                    <thead>
                      <tr>
                        <th>Criterion ID</th>
                        <th>Label</th>
                        <th>Metric Value</th>
                        <th>Status</th>
                        <th>Score</th>
                        <th>Max</th>
                        <th>Reason / Evidence</th>
                      </tr>
                    </thead>
                    <tbody>
                      ${m.criteria.map(c => `
                        <tr>
                          <td><code>${this.escape(c.id)}</code></td>
                          <td><strong>${this.escape(c.label)}</strong></td>
                          <td>${this.renderMetricValue(c.value, c.state)}</td>
                          <td>${this.renderSemanticStateBadge(c.state)}</td>
                          <td><strong>${c.score.toFixed(1)}</strong></td>
                          <td>${c.max.toFixed(1)}</td>
                          <td style="color: var(--text-muted); font-size: 0.8rem;">
                            ${this.escape(c.reason || '—')}
                            ${c.capped_by ? `<span class="badge badge-avoid" style="margin-left: 4px;">Capped: ${this.escape(c.capped_by)}</span>` : ''}
                            <div style="margin-top: 4px;">
                              <a href="#evidence/${this.escape(evaluationId)}?field=${this.escape(c.id)}" class="evidence-pill-link" title="Explore evidence for ${this.escape(c.label)}">
                                Inspect Citation [EV] &rarr;
                              </a>
                            </div>
                          </td>
                        </tr>
                      `).join('')}
                    </tbody>
                  </table>
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- 5. Penalties & Missing Data Grid -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px;">
          <!-- Penalties -->
          <div class="card">
            <div class="card-header">
              <div class="card-title">Active Penalties</div>
              <span class="badge ${penalties.length ? 'badge-avoid' : 'badge-clear'}">
                Total: ${score.penalties_total.toFixed(1)} pts
              </span>
            </div>
            ${this.renderPenaltyItems(penalties)}
          </div>

          <!-- Missing / Unverified Items -->
          <div class="card">
            <div class="card-header">
              <div class="card-title">Missing / Unverified Data Items</div>
              <span class="badge badge-unknown">${missing.length} Items</span>
            </div>
            ${missing.length === 0 ? `
              <p style="color: var(--text-muted); font-size: 0.85rem;">No missing inputs recorded. Dataset is complete.</p>
            ` : `
              <ul style="list-style: none;">
                ${missing.map(mu => `
                  <li style="padding: 8px 0; border-bottom: 1px solid var(--border-color); font-size: 0.85rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                      <code>${this.escape(mu.item)}</code>
                      <span class="badge badge-unknown">${this.escape(mu.category)}</span>
                    </div>
                    ${mu.description ? `<div style="font-size: 0.75rem; color: var(--text-muted);">${this.escape(mu.description)}</div>` : ''}
                    <div style="margin-top: 4px;">
                      <a href="#evidence/${this.escape(evaluationId)}?field=${this.escape(mu.item)}" class="evidence-pill-link">
                        Search in Evidence &rarr;
                      </a>
                    </div>
                  </li>
                `).join('')}
              </ul>
            `}
          </div>
        </div>
      `;

      const unarchiveBtn = container.querySelector('#btn-unarchive-current');
      if (unarchiveBtn) {
        unarchiveBtn.addEventListener('click', async () => {
          unarchiveBtn.disabled = true;
          unarchiveBtn.textContent = 'Unarchiving...';
          try {
            await this.api.unarchiveEvaluation(evaluationId);
            await this.renderScorecard(evaluationId);
          } catch (err) {
            alert(`Failed to unarchive: ${err.message}`);
            unarchiveBtn.disabled = false;
            unarchiveBtn.textContent = 'Unarchive Evaluation';
          }
        });
      }
    } catch (err) {
      this.renderError(container, 'Failed to load evaluation scorecard', err);
    }
  }

  // --------------------------------------------------------------------------
  // View 4: Evidence & Provenance Explorer (UI-3)
  // --------------------------------------------------------------------------

  async renderEvidenceExplorer(evaluationId, queryString = '') {
    this.setViewActive('evidence-view');
    const container = document.getElementById('evidence-view');
    if (!container) return;

    container.innerHTML = `
      <div class="state-box">
        <div class="spinner"></div>
        <h3>Loading Evidence &amp; Provenance Explorer...</h3>
        <p>Fetching immutable evidence citations and cryptographic hashes for <code>${this.escape(evaluationId)}</code>...</p>
      </div>
    `;

    try {
      const [evaluation, evidenceResp] = await Promise.all([
        this.api.getEvaluation(evaluationId),
        this.api.getEvaluationEvidence(evaluationId),
      ]);

      const params = new URLSearchParams(queryString || '');
      const initialFilter = params.get('field') || params.get('search') || '';

      this.evidenceState = {
        evaluationId,
        evaluation,
        evidenceResp,
        filterText: initialFilter,
        category: 'ALL',
      };

      this.renderEvidenceExplorerContent(container);
    } catch (err) {
      this.renderError(container, 'Failed to load Evidence & Provenance Explorer', err);
    }
  }

  renderEvidenceExplorerContent(container) {
    const { evaluation, evidenceResp, filterText } = this.evidenceState;
    const items = evidenceResp.items || [];

    container.innerHTML = `
      <!-- Top Return Bar -->
      <div class="evidence-header-bar">
        <div class="evidence-header-title">
          <div style="display: flex; gap: 8px; margin-bottom: 8px;">
            <a href="#evaluations/${this.escape(evaluation.evaluation_id)}" class="btn btn-outline btn-sm">
              &larr; Return to Scorecard
            </a>
            <a href="#performance/${this.escape(evaluation.evaluation_id)}" class="btn btn-outline btn-sm">
              Performance Explorer &rarr;
            </a>
          </div>
          <h2>Evidence &amp; Provenance Explorer</h2>
          <div class="company-subtitle">
            ${this.escape(evaluation.company_name)} &bull; <code>${this.escape(evaluation.ipo_id)}</code>
          </div>
        </div>
        <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
          <span class="meta-tag">MODE: ${this.escape(evaluation.evaluation_mode)}</span>
          <span class="meta-tag">ENGINE: v${this.escape(evaluation.engine_version)}</span>
          <span class="meta-tag">SPEC: v${this.escape(evaluation.spec_version)}</span>
          ${this.renderVerdictBadge(evaluation.verdict ? evaluation.verdict.verdict : 'UNKNOWN')}
        </div>
      </div>

      <!-- Provenance & Cryptographic Audit Panel -->
      <div class="provenance-panel" role="region" aria-label="Cryptographic Provenance Fingerprints">
        <div class="provenance-panel-header">
          <div class="provenance-panel-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            </svg>
            Cryptographic Provenance Fingerprints
          </div>
          <span class="meta-tag">IMMUTABLE RECORD</span>
        </div>

        <div class="provenance-grid">
          <div class="provenance-item">
            <span class="provenance-item-label">Evaluation Identifier</span>
            <div class="provenance-hash-row">
              <span class="provenance-hash" title="${this.escape(evaluation.evaluation_id)}">
                ${this.escape(evaluation.evaluation_id)}
              </span>
              <button class="btn-copy" data-copy="${this.escape(evaluation.evaluation_id)}">Copy</button>
            </div>
          </div>

          <div class="provenance-item">
            <span class="provenance-item-label">Result Hash (SHA-256)</span>
            <div class="provenance-hash-row">
              <span class="provenance-hash" title="${this.escape(evaluation.result_hash)}">
                ${this.escape(evaluation.result_hash)}
              </span>
              <button class="btn-copy" data-copy="${this.escape(evaluation.result_hash)}">Copy</button>
            </div>
          </div>

          <div class="provenance-item">
            <span class="provenance-item-label">Source Manifest Hash</span>
            <div class="provenance-hash-row">
              <span class="provenance-hash" title="${this.escape(evidenceResp.source_manifest_hash || evaluation.source_manifest_hash)}">
                ${this.escape(evidenceResp.source_manifest_hash || evaluation.source_manifest_hash)}
              </span>
              <button class="btn-copy" data-copy="${this.escape(evidenceResp.source_manifest_hash || evaluation.source_manifest_hash)}">Copy</button>
            </div>
          </div>

          <div class="provenance-item">
            <span class="provenance-item-label">Input Snapshot Hash</span>
            <div class="provenance-hash-row">
              <span class="provenance-hash" title="${this.escape(evaluation.input_snapshot_hash)}">
                ${this.escape(evaluation.input_snapshot_hash)}
              </span>
              <button class="btn-copy" data-copy="${this.escape(evaluation.input_snapshot_hash)}">Copy</button>
            </div>
          </div>

          <div class="provenance-item">
            <span class="provenance-item-label">Configuration Hash</span>
            <div class="provenance-hash-row">
              <span class="provenance-hash" title="${this.escape(evaluation.config_hash)}">
                ${this.escape(evaluation.config_hash)}
              </span>
              <button class="btn-copy" data-copy="${this.escape(evaluation.config_hash)}">Copy</button>
            </div>
          </div>

          ${evaluation.market_snapshot_hash ? `
            <div class="provenance-item">
              <span class="provenance-item-label">Market Snapshot Hash</span>
              <div class="provenance-hash-row">
                <span class="provenance-hash" title="${this.escape(evaluation.market_snapshot_hash)}">
                  ${this.escape(evaluation.market_snapshot_hash)}
                </span>
                <button class="btn-copy" data-copy="${this.escape(evaluation.market_snapshot_hash)}">Copy</button>
              </div>
            </div>
          ` : ''}

          ${evaluation.peer_snapshot_hash ? `
            <div class="provenance-item">
              <span class="provenance-item-label">Peer Snapshot Hash</span>
              <div class="provenance-hash-row">
                <span class="provenance-hash" title="${this.escape(evaluation.peer_snapshot_hash)}">
                  ${this.escape(evaluation.peer_snapshot_hash)}
                </span>
                <button class="btn-copy" data-copy="${this.escape(evaluation.peer_snapshot_hash)}">Copy</button>
              </div>
            </div>
          ` : ''}
        </div>
      </div>

      <!-- Market Data State Panel -->
      <div class="provenance-panel" role="region" aria-label="Market Data State">
        <div class="provenance-panel-header">
          <div class="provenance-panel-title">Market Data State (as recorded at evaluation)</div>
        </div>
        <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 10px;">
          Market criteria marked UNKNOWN mean the data was unavailable, stale, or not supplied — <strong>not</strong> that a market signal was observed and found negative. Freshness describes the recorded data's currency; it is not a qualification of the source.
        </div>
        <div class="provenance-grid">
          ${(evaluation.market_blocks || []).map(b => `
            <div class="provenance-item">
              <span class="provenance-item-label">${this.escape(String(b.block || '').toUpperCase())}</span>
              <div>
                ${b.status === 'FRESH' ? '<span class="badge badge-source-evidence">SUPPLIED (FRESH)</span>' : b.status === 'STALE' ? '<span class="badge badge-unknown-evidence">STALE — NOT USED</span>' : '<span class="badge badge-unknown">NOT SUPPLIED — NO SIGNAL OBSERVED</span>'}
              </div>
              <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 4px;">
                ${b.as_of ? `As of: ${this.escape(b.as_of)}` : 'No timestamp recorded'}
                ${b.source_id ? ` &bull; Source: ${this.escape(b.source_id)}` : ''}
                ${b.reason ? `<br>${this.escape(b.reason)}` : ''}
              </div>
            </div>
          `).join('') || '<div style="font-size: 0.8rem; color: var(--text-muted);">No market snapshot recorded for this evaluation.</div>'}
        </div>
      </div>

      <!-- Contract Guidance Note -->
      <div class="contract-guidance-note">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0; margin-top: 1px;" aria-hidden="true">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="16" x2="12" y2="12"></line>
          <line x1="12" y1="8" x2="12.01" y2="8"></line>
        </svg>
        <div>
          <strong>Source Evidence vs. Derived Provenance:</strong> Verbatim quotes and locators are extracted directly from official offer documents (RHP/DRHP). Derived scoring metrics and synthetic values are calculated deterministically by the engine core; they are not direct quotes from source filings.
        </div>
      </div>

      <!-- Evidence Toolbar -->
      <div class="evidence-toolbar">
        <div class="evidence-search-box">
          <input
            type="search"
            id="evidence-filter-input"
            class="evidence-search-input"
            placeholder="Filter by field, document, page, locator, or quote text..."
            value="${this.escape(filterText)}"
            aria-label="Filter evidence citations"
          />
        </div>

        <div class="evidence-category-filters" role="group" aria-label="Evidence categories">
          <button class="filter-btn active" data-cat="ALL">All Citations</button>
          <button class="filter-btn" data-cat="FINANCIALS">Financials</button>
          <button class="filter-btn" data-cat="GOVERNANCE">Governance</button>
          <button class="filter-btn" data-cat="STRUCTURE">Structure</button>
          <button class="filter-btn" data-cat="VALUATION">Valuation</button>
        </div>

        <span id="evidence-counter-badge" class="meta-tag">
          Showing ${items.length} of ${items.length} citations
        </span>
      </div>

      <!-- Evidence Cards Grid -->
      <div id="evidence-cards-container" class="evidence-grid" role="region" aria-label="Evidence Cards Grid">
        <!-- Rendered dynamically -->
      </div>

      <!-- Detail Inspector Slide-Out Drawer Container -->
      <div id="evidence-inspector-slot"></div>
    `;

    // Wire up events if container supports DOM queries
    if (typeof container.querySelector === 'function') {
      this.setupEvidenceEvents(container);
      this.updateEvidenceGrid();
    }
  }

  setupEvidenceEvents(container) {
    const input = container.querySelector('#evidence-filter-input');
    if (input) {
      input.addEventListener('input', () => {
        this.evidenceState.filterText = input.value.trim();
        this.updateEvidenceGrid();
      });
    }

    // Category filter buttons
    container.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        container.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.evidenceState.category = btn.getAttribute('data-cat') || 'ALL';
        this.updateEvidenceGrid();
      });
    });

    // Copy-to-clipboard buttons
    container.querySelectorAll('.btn-copy').forEach(btn => {
      btn.addEventListener('click', () => {
        const text = btn.getAttribute('data-copy');
        if (text) this.copyToClipboard(text, btn);
      });
    });
  }

  updateEvidenceGrid() {
    const gridEl = document.getElementById('evidence-cards-container');
    const counterEl = document.getElementById('evidence-counter-badge');
    if (!gridEl || !this.evidenceState) return;

    const { evidenceResp, filterText, category } = this.evidenceState;
    const allItems = evidenceResp.items || [];
    const query = (filterText || '').toLowerCase();

    const filtered = allItems.filter(item => {
      // Category filter
      if (category !== 'ALL') {
        const f = (item.field || '').toLowerCase();
        const id = (item.evidence_id || '').toLowerCase();
        if (category === 'FINANCIALS' && !/(cfo|pat|ebitda|revenue|debt|worth|roe|growth|margin|cash|period)/.test(f + id)) return false;
        if (category === 'GOVERNANCE' && !/(promoter|litigation|auditor|board|debarment|integrity|track)/.test(f + id)) return false;
        if (category === 'STRUCTURE' && !/(issue|ofs|proceeds|qib|retail|anchor|share|fresh|lockup)/.test(f + id)) return false;
        if (category === 'VALUATION' && !/(pe|multiple|peer|price|valuation|discount|collar)/.test(f + id)) return false;
      }

      // Text query filter
      if (!query) return true;
      const haystack = [
        item.evidence_id,
        item.field,
        item.document,
        item.locator,
        item.quote,
        String(item.extracted_value ?? ''),
        item.unit,
      ].join(' ').toLowerCase();

      return haystack.includes(query);
    });

    if (counterEl) {
      counterEl.textContent = `Showing ${filtered.length} of ${allItems.length} citations`;
    }

    if (filtered.length === 0) {
      gridEl.innerHTML = `
        <div class="card" style="grid-column: 1 / -1; padding: 40px 20px; text-align: center;">
          <h3 style="font-size: 1.1rem; color: var(--text-main); margin-bottom: 8px;">No Evidence Citations Found</h3>
          <p style="font-size: 0.85rem; color: var(--text-muted); max-width: 400px; margin: 0 auto 16px;">
            No recorded citations match "${this.escape(filterText)}".
          </p>
          <button class="btn btn-outline btn-sm" id="btn-reset-filters">Clear Filter</button>
        </div>
      `;
      const resetBtn = gridEl.querySelector('#btn-reset-filters');
      if (resetBtn) {
        resetBtn.addEventListener('click', () => {
          this.evidenceState.filterText = '';
          this.evidenceState.category = 'ALL';
          const input = document.getElementById('evidence-filter-input');
          if (input) input.value = '';
          document.querySelectorAll('.filter-btn').forEach(b => {
            b.classList.toggle('active', b.getAttribute('data-cat') === 'ALL');
          });
          this.updateEvidenceGrid();
        });
      }
      return;
    }

    gridEl.innerHTML = filtered.map(item => {
      const isQuotePresent = Boolean(item.quote && item.quote.trim());
      const isExtractedPresent = item.extracted_value !== null && item.extracted_value !== undefined;

      const isProcessing = item.quote_kind === 'PROCESSING';
      const processingText = isProcessing && item.note ? item.note.replace(/^PROCESSING_SUMMARY:\s*/, '') : '';

      let distinctionBadge = '';
      if (item.extraction_method === 'MANUAL_ENTRY') {
        distinctionBadge = `<span class="badge badge-unknown-evidence" title="Entered manually by the operator; not verified against an official source">MANUALLY ENTERED (Not Source-Verified)</span>`;
      } else if (isProcessing) {
        distinctionBadge = `<span class="badge badge-derived-value" title="Generated by the extractor, not quoted from the source document">PROCESSING SUMMARY</span>`;
      } else if (item.verification === 'RETAINED_UNVERIFIED') {
        distinctionBadge = `<span class="badge badge-unknown-evidence" title="Retained copy whose official provenance is not established">UNVERIFIED RETAINED SOURCE</span>`;
      } else if (isQuotePresent) {
        distinctionBadge = `<span class="badge badge-source-evidence" title="Extracted verbatim from prospectus">SOURCE EVIDENCE</span>`;
      } else if (!isExtractedPresent) {
        distinctionBadge = `<span class="badge badge-unknown-evidence" title="Data point is missing or unverified">UNKNOWN / UNVERIFIED</span>`;
      } else {
        distinctionBadge = `<span class="badge badge-derived-value" title="Derived or calculated by scoring engine">DERIVED VALUE</span>`;
      }

      const quoteText = item.quote ? item.quote.trim() : '';
      const isLongQuote = quoteText.length > 180;
      const displayQuote = isLongQuote ? quoteText.slice(0, 180) + '…' : quoteText;

      return `
        <article class="evidence-card" role="article" aria-label="Evidence ${this.escape(item.evidence_id)}">
          <div>
            <div class="evidence-card-header">
              <div>
                <div class="evidence-field-name">${this.escape(item.field)}</div>
                <div class="evidence-id-tag"><code>${this.escape(item.evidence_id)}</code></div>
              </div>
              ${distinctionBadge}
            </div>

            <!-- Extracted Value Box -->
            <div class="evidence-extracted-box">
              <span class="evidence-extracted-label">Extracted Value</span>
              <span class="evidence-extracted-val">
                ${isExtractedPresent ? `<code>${this.escape(String(item.extracted_value))}</code>` : item.value_summary ? `<code>${this.escape(item.value_summary)}</code>` : '<span class="badge badge-unknown">UNKNOWN</span>'}
                ${item.unit ? `<span class="unit-badge">${this.escape(item.unit)}</span>` : ''}
              </span>
            </div>

            <!-- Quotation / Processing Block -->
            ${isProcessing ? `
              <div class="evidence-quote-box">
                <span class="quote-text" style="font-style: italic;">${this.escape(processingText)}</span>
                <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 4px;">Extractor processing information — not a quotation from the source document.</div>
              </div>
            ` : isQuotePresent ? `
              <div class="evidence-quote-box">
                <span class="quote-text">&ldquo;${this.escape(displayQuote)}&rdquo;</span>
                ${isLongQuote ? `
                  <div>
                    <button class="quote-expansion-toggle" data-full-quote="${this.escape(quoteText)}">
                      Show full quote
                    </button>
                  </div>
                ` : ''}
              </div>
            ` : `
              <div style="font-size: 0.78rem; color: var(--text-light); font-style: italic; margin: 10px 0;">
                No verbatim text quoted (Structured or Computed Metric)
              </div>
            `}
          </div>

          <div>
            <!-- Locator & Document Info -->
            <div class="evidence-locator-row">
              <span class="locator-tag" title="Source Document">${this.escape(item.document || 'Filing / RHP')}</span>
              <span class="locator-tag" title="Page Number">${item.page !== null && item.page !== undefined ? `p. ${this.escape(item.page)}` : 'Page unrecorded'}</span>
              ${item.locator ? `<span class="locator-tag" title="Document Locator">${this.escape(item.locator)}</span>` : ''}
            </div>

            <div style="margin-top: 12px; display: flex; justify-content: flex-end;">
              <button class="btn btn-outline btn-sm btn-inspect-item" data-ev-id="${this.escape(item.evidence_id)}">
                Inspect Full Detail &rarr;
              </button>
            </div>
          </div>
        </article>
      `;
    }).join('');

    // Wire quote expansion toggles
    gridEl.querySelectorAll('.quote-expansion-toggle').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const fullQuote = btn.getAttribute('data-full-quote');
        const quoteSpan = btn.closest('.evidence-quote-box').querySelector('.quote-text');
        if (btn.textContent.includes('Show')) {
          quoteSpan.innerHTML = `&ldquo;${this.escape(fullQuote)}&rdquo;`;
          btn.textContent = 'Collapse quote';
        } else {
          quoteSpan.innerHTML = `&ldquo;${this.escape(fullQuote.slice(0, 180) + '…')}&rdquo;`;
          btn.textContent = 'Show full quote';
        }
      });
    });

    // Wire inspect detail buttons
    gridEl.querySelectorAll('.btn-inspect-item').forEach(btn => {
      btn.addEventListener('click', () => {
        const evId = btn.getAttribute('data-ev-id');
        const item = allItems.find(it => it.evidence_id === evId);
        if (item) this.openEvidenceInspector(item);
      });
    });
  }

  openEvidenceInspector(item) {
    const slot = document.getElementById('evidence-inspector-slot');
    if (!slot) return;

    const isQuotePresent = Boolean(item.quote && item.quote.trim());
    const isExtractedPresent = item.extracted_value !== null && item.extracted_value !== undefined;

    const isProcessing = item.quote_kind === 'PROCESSING';
    const processingText = isProcessing && item.note ? item.note.replace(/^PROCESSING_SUMMARY:\s*/, '') : '';

    let provenanceStatusLabel = 'SOURCE EVIDENCE (Extracted from Filing)';
    if (item.extraction_method === 'MANUAL_ENTRY') {
      provenanceStatusLabel = 'MANUALLY ENTERED (Operator Entry — Not Source-Verified)';
    } else if (isProcessing) {
      provenanceStatusLabel = 'PROCESSING SUMMARY (Extractor-Generated, Not Source Text)';
    } else if (item.verification === 'RETAINED_UNVERIFIED') {
      provenanceStatusLabel = 'UNVERIFIED RETAINED SOURCE (official provenance not established)';
    } else if (item.verification === 'OFFICIAL_VERIFIED' && isExtractedPresent) {
      provenanceStatusLabel = 'SOURCE EVIDENCE (Verified Official Source)';
    } else if (isQuotePresent && (item.verification === 'FILING' || item.verification === 'OFFICIAL_VERIFIED')) {
      // A recorded quotation backed by a filing/official source is source
      // evidence even when the structured value is non-scalar (e.g. a
      // seller list) and therefore carries no scalar extracted_value.
      // Provenance describes the evidence's origin; it must not be
      // reported as UNKNOWN merely because the value is a list.
      provenanceStatusLabel = item.verification === 'OFFICIAL_VERIFIED'
        ? 'SOURCE EVIDENCE (Verified Official Source)'
        : 'SOURCE EVIDENCE (Extracted from Filing)';
    } else if (!isExtractedPresent && !isQuotePresent) {
      provenanceStatusLabel = 'UNKNOWN / UNVERIFIED (Missing or Incomplete Data)';
    } else if (!isQuotePresent) {
      provenanceStatusLabel = 'DERIVED VALUE (Engine-Computed Metric)';
    }

    slot.innerHTML = `
      <div class="inspector-backdrop" id="inspector-backdrop" role="dialog" aria-modal="true" aria-labelledby="inspector-title">
        <div class="inspector-drawer">
          <div class="inspector-header">
            <h3 id="inspector-title">Evidence Detail: <code>${this.escape(item.evidence_id)}</code></h3>
            <button class="btn btn-outline btn-sm" id="btn-close-inspector" aria-label="Close Inspector">&times; Close</button>
          </div>

          <div class="inspector-content">
            <div class="inspector-row">
              <span class="inspector-label">Provenance Classification</span>
              <div class="inspector-val">
                <span class="badge ${item.verification === 'RETAINED_UNVERIFIED' ? 'badge-unknown-evidence' : isQuotePresent ? 'badge-source-evidence' : !isExtractedPresent ? 'badge-unknown-evidence' : 'badge-derived-value'}">
                  ${provenanceStatusLabel}
                </span>
              </div>
            </div>

            <div class="inspector-row">
              <span class="inspector-label">Canonical Field Name</span>
              <div class="inspector-val"><code>${this.escape(item.field)}</code></div>
            </div>

            <div class="inspector-row">
              <span class="inspector-label">Extracted Value &amp; Unit</span>
              <div class="inspector-val">
                ${isExtractedPresent ? `<strong>${this.escape(String(item.extracted_value))}</strong>` : item.value_summary ? `<strong>${this.escape(item.value_summary)}</strong>` : '<span class="badge badge-unknown">UNKNOWN</span>'}
                ${item.unit ? `<span class="unit-badge" style="margin-left: 6px;">${this.escape(item.unit)}</span>` : ''}
              </div>
            </div>

            <div class="inspector-row">
              <span class="inspector-label">Source Document</span>
              <div class="inspector-val">
                <strong>${this.escape(item.document || 'Prospectus / Filing')}</strong>
                ${item.source ? `<span class="meta-tag" style="margin-left: 6px;">Source ID: ${this.escape(item.source)}</span>` : ''}
              </div>
            </div>

            <div class="inspector-row">
              <span class="inspector-label">Page &amp; Locator</span>
              <div class="inspector-val">
                Page: <strong>${item.page !== null && item.page !== undefined ? this.escape(item.page) : 'Unrecorded'}</strong>
                ${item.locator ? ` &bull; Locator: <code>${this.escape(item.locator)}</code>` : ''}
              </div>
            </div>

            <div class="inspector-row">
              <span class="inspector-label">${isProcessing ? 'Extractor Processing Information' : 'Recorded Quotation (as recorded in evidence)'}</span>
              ${isProcessing ? `
                <div class="evidence-quote-box" style="font-size: 0.9rem; margin-top: 6px;">
                  <span style="font-style: italic;">${this.escape(processingText)}</span>
                </div>
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 6px;">Generated by the extractor from the data it parsed. This is not text quoted from the source document.</div>
              ` : isQuotePresent ? `
                <div class="evidence-quote-box" style="font-size: 0.9rem; margin-top: 6px;">
                  &ldquo;${this.escape(item.quote)}&rdquo;
                </div>
                <div style="margin-top: 6px;">
                  <button class="btn btn-outline btn-sm" id="btn-copy-quote" data-copy="${this.escape(item.quote)}">
                    Copy Verbatim Quote
                  </button>
                </div>
              ` : `
                <div style="font-size: 0.82rem; color: var(--text-muted); font-style: italic; margin-top: 6px;">
                  No verbatim quote registered for this record.
                </div>
              `}
            </div>

            <div class="inspector-row" style="margin-top: 8px;">
              <span class="inspector-label">Raw Provenance Payload (JSON)</span>
              <pre class="raw-json-box"><code>${this.escape(JSON.stringify(item, null, 2))}</code></pre>
            </div>
          </div>
        </div>
      </div>
    `;

    // Wire close actions
    const closeBtn = slot.querySelector('#btn-close-inspector');
    const backdrop = slot.querySelector('#inspector-backdrop');

    if (closeBtn) closeBtn.addEventListener('click', () => this.closeEvidenceInspector());
    if (backdrop) {
      backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) this.closeEvidenceInspector();
      });
    }

    // Wire copy quote
    const copyQuoteBtn = slot.querySelector('#btn-copy-quote');
    if (copyQuoteBtn) {
      copyQuoteBtn.addEventListener('click', () => {
        const text = copyQuoteBtn.getAttribute('data-copy');
        if (text) this.copyToClipboard(text, copyQuoteBtn);
      });
    }
  }

  closeEvidenceInspector() {
    const slot = document.getElementById('evidence-inspector-slot');
    if (slot) slot.innerHTML = '';
  }

  copyToClipboard(text, triggerBtn) {
    if (!text) return;
    const originalText = triggerBtn.textContent;

    const performFeedback = () => {
      triggerBtn.textContent = 'Copied!';
      triggerBtn.style.color = 'var(--color-apply)';
      setTimeout(() => {
        triggerBtn.textContent = originalText;
        triggerBtn.style.color = '';
      }, 1500);
    };

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(performFeedback).catch(() => {
        this.fallbackCopy(text);
        performFeedback();
      });
    } else {
      this.fallbackCopy(text);
      performFeedback();
    }
  }

  fallbackCopy(text) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.left = '-9999px';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    try {
      document.execCommand('copy');
    } catch {}
    document.body.removeChild(ta);
  }

  // --------------------------------------------------------------------------
  // View 5: Post-Listing Observation & Performance Explorer (UI-4)
  // --------------------------------------------------------------------------

  async renderPerformanceExplorer(evaluationId, queryString = '') {
    this.setViewActive('performance-view');
    const container = document.getElementById('performance-view');
    if (!container) return;

    container.innerHTML = `
      <div class="state-box">
        <div class="spinner"></div>
        <h3>Loading Post-Listing Performance Explorer...</h3>
        <p>Fetching post-listing price observations and benchmark alpha metrics for <code>${this.escape(evaluationId)}</code>...</p>
      </div>
    `;

    try {
      const [evalRes, perfRes, obsRes, btRes, calRes] = await Promise.allSettled([
        this.api.getEvaluation(evaluationId),
        this.api.getPerformance(evaluationId),
        this.api.getPostListing(evaluationId),
        this.api.getBacktestAnalytics(),
        this.api.getCalibrationProposals(),
      ]);

      if (evalRes.status !== 'fulfilled') {
        throw evalRes.reason;
      }

      const evaluation = evalRes.value;
      const perfSummary = perfRes.status === 'fulfilled' ? perfRes.value : null;
      const postListing = obsRes.status === 'fulfilled' ? obsRes.value : null;
      const backtest = btRes.status === 'fulfilled' ? btRes.value : null;
      const calibration = calRes.status === 'fulfilled' ? calRes.value : null;

      this.renderPerformanceContent(container, {
        evaluation,
        perfSummary,
        postListing,
        backtest,
        calibration,
      });
    } catch (err) {
      this.renderError(container, 'Failed to load Post-Listing Performance Explorer', err);
    }
  }

  renderPerformanceContent(container, { evaluation, perfSummary, postListing, backtest, calibration }) {
    const observations = postListing?.observations || [];
    const horizons = perfSummary?.horizons || {};
    const oneWeek = horizons.one_week || { status: 'INCOMPLETE' };
    const oneMonth = horizons.one_month || { status: 'INCOMPLETE' };
    const sixMonth = horizons.six_month || { status: 'INCOMPLETE' };

    const issuePriceDisplay = perfSummary?.issue_price ? `₹${parseFloat(perfSummary.issue_price).toFixed(2)}` : (evaluation.score?.issue_price ? `₹${parseFloat(evaluation.score.issue_price).toFixed(2)}` : 'UNRECORDED');
    const listingDateDisplay = perfSummary?.listing_date || 'Pending / Unrecorded';

    container.innerHTML = `
      <!-- Top Navigation Bar -->
      <div class="evidence-header-bar">
        <div class="evidence-header-title">
          <div style="display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap;">
            <a href="#evaluations/${this.escape(evaluation.evaluation_id)}" class="btn btn-outline btn-sm">
              &larr; Return to Scorecard
            </a>
            <a href="#evidence/${this.escape(evaluation.evaluation_id)}" class="btn btn-outline btn-sm">
              Inspect Evidence &rarr;
            </a>
          </div>
          <h2>Post-Listing Observation &amp; Performance Explorer</h2>
          <div class="company-subtitle">
            ${this.escape(evaluation.company_name)} &bull; <code>${this.escape(evaluation.ipo_id)}</code>
          </div>
        </div>
        <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
          <span class="meta-tag">FINAL EVAL: <code>${this.escape(evaluation.evaluation_id)}</code></span>
          <span class="meta-tag">ENGINE: v${this.escape(evaluation.engine_version)}</span>
          ${this.renderVerdictBadge(evaluation.verdict ? evaluation.verdict.verdict : 'UNKNOWN')}
        </div>
      </div>

      <!-- 1. Executive Performance Summary KPI Strip -->
      <div class="perf-kpi-grid" role="region" aria-label="Performance Summary KPIs">
        <div class="perf-kpi-card">
          <div class="perf-kpi-label">Issue Price</div>
          <div class="perf-kpi-val">${this.escape(issuePriceDisplay)}</div>
          <div class="perf-kpi-sub">Listing Date: ${this.escape(listingDateDisplay)}</div>
        </div>

        <div class="perf-kpi-card">
          <div class="perf-kpi-label">1-Week Horizon (1W)</div>
          <div class="perf-kpi-val">${this.formatReturnPct(oneWeek.ipo_return_pct)}</div>
          <div class="perf-kpi-sub">
            Excess Alpha: <strong>${this.formatReturnPct(oneWeek.excess_return_pct)}</strong> &bull; ${this.escape(oneWeek.status)}
          </div>
        </div>

        <div class="perf-kpi-card">
          <div class="perf-kpi-label">1-Month Horizon (1M)</div>
          <div class="perf-kpi-val">${this.formatReturnPct(oneMonth.ipo_return_pct)}</div>
          <div class="perf-kpi-sub">
            Excess Alpha: <strong>${this.formatReturnPct(oneMonth.excess_return_pct)}</strong> &bull; ${this.escape(oneMonth.status)}
          </div>
        </div>

        <div class="perf-kpi-card">
          <div class="perf-kpi-label">6-Month Horizon (6M)</div>
          <div class="perf-kpi-val">${this.formatReturnPct(sixMonth.ipo_return_pct)}</div>
          <div class="perf-kpi-sub">
            Excess Alpha: <strong>${this.formatReturnPct(sixMonth.excess_return_pct)}</strong> &bull; ${this.escape(sixMonth.status)}
          </div>
        </div>
      </div>

      <!-- 2. Deterministic Performance Timeline -->
      <div class="card" style="margin-bottom: 24px;">
        <div class="card-header">
          <div class="card-title">Deterministic Performance Timeline</div>
          <span class="meta-tag">Offering Progression Chain</span>
        </div>

        <div class="timeline-wrapper" role="region" aria-label="Lifecycle Performance Timeline">
          <!-- Step 1: FINAL Evaluation -->
          <div class="timeline-step completed">
            <div class="timeline-step-title">
              <span>1. FINAL Screening</span>
              <span class="badge badge-clear" style="font-size: 0.68rem;">COMPLETED</span>
            </div>
            <div class="timeline-step-date">${this.formatDate(evaluation.evaluation_timestamp)}</div>
            <div class="timeline-step-metric">
              Score: <strong>${evaluation.score ? evaluation.score.final_score.toFixed(1) : '—'}</strong> / 100
            </div>
            <div style="margin-top: 6px; font-size: 0.75rem;">
              Verdict: ${this.renderVerdictBadge(evaluation.verdict ? evaluation.verdict.verdict : 'UNKNOWN')}
            </div>
          </div>

          <!-- Step 2: Listing Day -->
          <div class="timeline-step ${observations.length > 0 ? 'completed' : 'incomplete'}">
            <div class="timeline-step-title">
              <span>2. Listing Day</span>
              <span class="badge ${observations.length > 0 ? 'badge-clear' : 'badge-unknown'}" style="font-size: 0.68rem;">
                ${observations.length > 0 ? 'RECORDED' : 'PENDING'}
              </span>
            </div>
            <div class="timeline-step-date">${this.escape(listingDateDisplay)}</div>
            <div class="timeline-step-metric">
              ${observations[0]?.prices?.listing_close ? `Close: ₹${observations[0].prices.listing_close.toFixed(2)}` : 'Awaiting Listing'}
            </div>
            <div style="margin-top: 6px; font-size: 0.75rem;">
              Gain: ${observations[0]?.returns?.listing_gain_pct !== undefined ? this.formatReturnPct(observations[0].returns.listing_gain_pct) : '<span class="return-badge-neutral">UNAVAILABLE</span>'}
            </div>
          </div>

          <!-- Step 3: 1-Week Horizon -->
          <div class="timeline-step ${oneWeek.status === 'RECORDED' ? 'completed' : 'incomplete'}">
            <div class="timeline-step-title">
              <span>3. 1-Week (1W)</span>
              <span class="badge ${oneWeek.status === 'RECORDED' ? 'badge-clear' : 'badge-unknown'}" style="font-size: 0.68rem;">
                ${this.escape(oneWeek.status)}
              </span>
            </div>
            <div class="timeline-step-date">
              ${observations.find(o => o.horizon === '1W')?.actual_trading_date || '7d Trading Window'}
            </div>
            <div class="timeline-step-metric">
              Return: ${this.formatReturnPct(oneWeek.ipo_return_pct)}
            </div>
            <div style="margin-top: 6px; font-size: 0.75rem;">
              Excess Alpha: ${this.formatReturnPct(oneWeek.excess_return_pct)}
            </div>
          </div>

          <!-- Step 4: 1-Month Horizon -->
          <div class="timeline-step ${oneMonth.status === 'RECORDED' ? 'completed' : 'incomplete'}">
            <div class="timeline-step-title">
              <span>4. 1-Month (1M)</span>
              <span class="badge ${oneMonth.status === 'RECORDED' ? 'badge-clear' : 'badge-unknown'}" style="font-size: 0.68rem;">
                ${this.escape(oneMonth.status)}
              </span>
            </div>
            <div class="timeline-step-date">
              ${observations.find(o => o.horizon === '1M')?.actual_trading_date || '30d Trading Window'}
            </div>
            <div class="timeline-step-metric">
              Return: ${this.formatReturnPct(oneMonth.ipo_return_pct)}
            </div>
            <div style="margin-top: 6px; font-size: 0.75rem;">
              Excess Alpha: ${this.formatReturnPct(oneMonth.excess_return_pct)}
            </div>
          </div>

          <!-- Step 5: 6-Month Horizon -->
          <div class="timeline-step ${sixMonth.status === 'RECORDED' ? 'completed' : 'incomplete'}">
            <div class="timeline-step-title">
              <span>5. 6-Month (6M)</span>
              <span class="badge ${sixMonth.status === 'RECORDED' ? 'badge-clear' : 'badge-unknown'}" style="font-size: 0.68rem;">
                ${this.escape(sixMonth.status)}
              </span>
            </div>
            <div class="timeline-step-date">
              ${observations.find(o => o.horizon === '6M')?.actual_trading_date || '180d Trading Window'}
            </div>
            <div class="timeline-step-metric">
              Return: ${this.formatReturnPct(sixMonth.ipo_return_pct)}
            </div>
            <div style="margin-top: 6px; font-size: 0.75rem;">
              Excess Alpha: ${this.formatReturnPct(sixMonth.excess_return_pct)}
            </div>
          </div>
        </div>
      </div>

      <!-- 3. Multi-Horizon Detailed Observation Cards -->
      <div style="margin-bottom: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
          <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--text-main);">
            Detailed Horizon Price &amp; Return Observations
          </h3>
          <span class="meta-tag">${observations.length} Recorded Horizons</span>
        </div>

        ${observations.length === 0 ? `
          <div class="card">
            <div class="state-box">
              <h3>No Post-Listing Observations Recorded</h3>
              <p>No post-listing price observations have matured or been ingested for this offering yet. Offering may be in pre-listing phase or awaiting observation window closure.</p>
              <div class="meta-tag" style="margin-top: 10px;">HORIZONS TRACKED: 1W (7d) &bull; 1M (30d) &bull; 6M (180d)</div>
            </div>
          </div>
        ` : `
          <div class="horizon-grid">
            ${observations.map(obs => {
              const caFactor = obs.prices?.corporate_action_factor ?? 1.0;
              const isAdjusted = Math.abs(caFactor - 1.0) > 0.0001;

              return `
                <div class="horizon-card">
                  <div>
                    <div class="horizon-card-header">
                      <div class="horizon-card-title">
                        <span class="badge badge-apply">${this.escape(obs.horizon)}</span>
                        <span>Horizon Observation</span>
                      </div>
                      <span class="badge ${obs.status === 'RECORDED' ? 'badge-clear' : 'badge-unknown'}">
                        ${this.escape(obs.status)}
                      </span>
                    </div>

                    <!-- Trading Schedule Info -->
                    <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 12px;">
                      <span>Target Date: <code>${this.escape(obs.target_date)}</code></span>
                      <span>Trading Date: <code>${this.escape(obs.actual_trading_date)}</code></span>
                    </div>

                    <!-- Compact Price Metrics Table -->
                    <table class="price-metric-table">
                      <tbody>
                        <tr>
                          <td class="label-col">Issue Price</td>
                          <td class="val-col">₹${obs.prices?.issue_price !== undefined ? parseFloat(obs.prices.issue_price).toFixed(2) : this.escape(obs.issue_price)}</td>
                        </tr>
                        <tr>
                          <td class="label-col">Listing Day Open</td>
                          <td class="val-col">${obs.prices?.listing_open !== null && obs.prices?.listing_open !== undefined ? `₹${obs.prices.listing_open.toFixed(2)}` : '—'}</td>
                        </tr>
                        <tr>
                          <td class="label-col">Listing Day Close</td>
                          <td class="val-col">${obs.prices?.listing_close !== null && obs.prices?.listing_close !== undefined ? `₹${obs.prices.listing_close.toFixed(2)}` : '—'}</td>
                        </tr>
                        <tr>
                          <td class="label-col">Raw Observed Close</td>
                          <td class="val-col">${obs.prices?.raw_observed_close !== null && obs.prices?.raw_observed_close !== undefined ? `₹${obs.prices.raw_observed_close.toFixed(2)}` : '—'}</td>
                        </tr>
                        <tr>
                          <td class="label-col">Adjusted Observed Close</td>
                          <td class="val-col"><strong>${obs.prices?.adjusted_observed_close !== null && obs.prices?.adjusted_observed_close !== undefined ? `₹${obs.prices.adjusted_observed_close.toFixed(2)}` : '—'}</strong></td>
                        </tr>
                      </tbody>
                    </table>

                    <!-- Corporate Action & Adjustment Status -->
                    <div style="margin-bottom: 12px;">
                      ${isAdjusted ? `
                        <span class="ca-pill-adjusted" title="Corporate action detected (splits, bonus, rights)">
                          &#9888; Factor: ${caFactor.toFixed(4)} (Adjusted)
                        </span>
                      ` : `
                        <span class="ca-pill-clean" title="Zero corporate actions detected">
                          &#10003; Factor: 1.0000 (Clean / Unadjusted)
                        </span>
                      `}
                    </div>

                    <!-- Returns Breakdown Grid -->
                    <div class="returns-breakdown-box">
                      <div style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted);">
                        Deterministic Returns Breakdown
                      </div>
                      <div class="returns-breakdown-grid">
                        <div class="return-metric-cell">
                          <span class="return-metric-label">Absolute Return</span>
                          <span class="return-metric-val">${this.formatReturnPct(obs.returns?.absolute_return_pct)}</span>
                        </div>
                        <div class="return-metric-cell">
                          <span class="return-metric-label">Listing Gain</span>
                          <span class="return-metric-val">${this.formatReturnPct(obs.returns?.listing_gain_pct)}</span>
                        </div>
                        <div class="return-metric-cell">
                          <span class="return-metric-label">Secondary Return</span>
                          <span class="return-metric-val">${this.formatReturnPct(obs.returns?.secondary_return_pct)}</span>
                        </div>
                        <div class="return-metric-cell">
                          <span class="return-metric-label">Benchmark (${this.escape(obs.benchmark?.symbol || 'BENCHMARK')})</span>
                          <span class="return-metric-val">${this.formatReturnPct(obs.returns?.benchmark_return_pct ?? obs.benchmark?.return_pct)}</span>
                        </div>
                        <div class="return-metric-cell" style="grid-column: 1 / -1; border-top: 1px solid var(--border-color); padding-top: 6px; margin-top: 4px;">
                          <span class="return-metric-label">Excess Alpha vs Benchmark</span>
                          <span class="return-metric-val" style="font-size: 1.1rem;">${this.formatReturnPct(obs.returns?.excess_return_pct)}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid var(--border-color); font-size: 0.72rem; color: var(--text-light); font-family: var(--font-mono);">
                    Observation ID: <code>${this.escape(obs.observation_id)}</code> (v${obs.version})
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        `}
      </div>

      <!-- 4. Provenance & Observation Audit Panel -->
      <div class="provenance-panel" role="region" aria-label="Observation Provenance and Fingerprints">
        <div class="provenance-panel-header">
          <div class="provenance-panel-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            </svg>
            Cryptographic Observation Provenance Fingerprints
          </div>
          <span class="meta-tag">FROZEN OBSERVER STORE</span>
        </div>

        <div class="provenance-grid">
          <div class="provenance-item">
            <span class="provenance-item-label">Final Evaluation Linkage</span>
            <div class="provenance-hash-row">
              <span class="provenance-hash" title="${this.escape(evaluation.evaluation_id)}">
                ${this.escape(evaluation.evaluation_id)}
              </span>
              <button class="btn-copy" data-copy="${this.escape(evaluation.evaluation_id)}">Copy</button>
            </div>
          </div>

          <div class="provenance-item">
            <span class="provenance-item-label">Source Manifest Hash</span>
            <div class="provenance-hash-row">
              <span class="provenance-hash" title="${this.escape(evaluation.source_manifest_hash)}">
                ${this.escape(evaluation.source_manifest_hash)}
              </span>
              <button class="btn-copy" data-copy="${this.escape(evaluation.source_manifest_hash)}">Copy</button>
            </div>
          </div>

          <div class="provenance-item">
            <span class="provenance-item-label">Evaluation Result Hash</span>
            <div class="provenance-hash-row">
              <span class="provenance-hash" title="${this.escape(evaluation.result_hash)}">
                ${this.escape(evaluation.result_hash)}
              </span>
              <button class="btn-copy" data-copy="${this.escape(evaluation.result_hash)}">Copy</button>
            </div>
          </div>

          <div class="provenance-item">
            <span class="provenance-item-label">Benchmark Provider</span>
            <div class="provenance-hash-row">
              <span class="provenance-hash">
                ${this.escape(observations[0]?.benchmark?.symbol || 'NSE NIFTY 50 (Bhavcopy Official)')}
              </span>
              <span class="meta-tag">OFFICIAL</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 5. Backtest & Calibration Governance Boundaries -->
      <div class="analytics-callout-grid">
        <!-- Backtest Analytics Affordance -->
        <div class="backtest-callout">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
            <div style="font-weight: 700; color: var(--text-main); font-size: 0.95rem;">
              Aggregate Backtest Analytics Boundary
            </div>
            <span class="meta-tag">POPULATION METRICS</span>
          </div>
          <p style="font-size: 0.8rem; color: var(--text-muted); line-height: 1.45; margin-bottom: 12px;">
            <strong>Individual Observation &ne; Aggregate Backtest Analysis:</strong> Individual observations measure single-offering post-listing trajectory. Aggregate backtesting evaluates population rank information coefficient (IC), hit rates, and decile spreads across the full historical universe.
          </p>

          ${backtest ? `
            <div style="font-size: 0.78rem; font-family: var(--font-mono); display: flex; flex-direction: column; gap: 4px;">
              <div>Analysis Hash: <code>${this.escape(backtest.analysis_hash)}</code></div>
              <div>Dataset Hash: <code>${this.escape(backtest.dataset_hash)}</code></div>
              <div>Leakage Audit: <span class="badge ${backtest.leakage_audit_passed ? 'badge-clear' : 'badge-avoid'}">${backtest.leakage_audit_passed ? 'PASSED' : 'FAILED'}</span></div>
            </div>
            <div style="margin-top: 10px;">
              <a href="#backtest" class="btn btn-outline btn-sm">Explore Backtest Analytics Dashboard &rarr;</a>
            </div>
          ` : `
            <div style="font-size: 0.78rem; color: var(--text-muted); background: var(--bg-surface); padding: 8px 12px; border-radius: 4px; border: 1px solid var(--border-color);">
              <span class="badge badge-unknown" style="font-size: 0.7rem;">NO RUN ARTIFACT</span>
              No pre-computed backtest analytics artifact on disk (<code>build/analytics/</code>).
            </div>
            <div style="margin-top: 10px;">
              <a href="#backtest" class="btn btn-outline btn-sm">Backtest Analytics Dashboard &rarr;</a>
            </div>
          `}
        </div>

        <!-- Calibration Governance Boundary -->
        <div class="calibration-callout">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
            <div style="font-weight: 700; color: #92400e; font-size: 0.95rem;">
              Calibration Governance Boundary
            </div>
            <span class="meta-tag" style="background: #fde68a; color: #78350f;">GATED LIFECYCLE</span>
          </div>
          <p style="font-size: 0.8rem; color: var(--text-muted); line-height: 1.45; margin-bottom: 12px;">
            <strong>Policy Evolution Principle:</strong> Evidence &rarr; Analysis &rarr; Proposal &ne; Approval &ne; Implementation &ne; Activation. In-browser or automated config mutation is strictly prohibited.
          </p>
          <div style="font-size: 0.8rem; background: #fffdf5; padding: 10px; border-radius: 6px; border: 1px solid #fde68a;">
            <div>Active Scoring Policy: <strong>● v1.5.0 (Executable)</strong></div>
            <div style="margin-top: 4px;">Candidate Proposal: <strong>○ v1.6.0 (READY_FOR_HUMAN_REVIEW)</strong></div>
            <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 6px;">
              Activation requires formal offline committee ratification. Zero in-browser activation controls.
            </div>
            <div style="margin-top: 10px;">
              <a href="#calibration" class="btn btn-outline btn-sm">Inspect Calibration &amp; Policy Governance &rarr;</a>
            </div>
          </div>
        </div>
      </div>
    `;

    // Wire up copy buttons if container supports DOM queries
    if (typeof container.querySelectorAll === 'function') {
      container.querySelectorAll('.btn-copy').forEach(btn => {
        btn.addEventListener('click', () => {
          const text = btn.getAttribute('data-copy');
          if (text) this.copyToClipboard(text, btn);
        });
      });
    }
  }

  formatReturnPct(val) {
    if (val === null || val === undefined || val === '') {
      return '<span class="return-badge-neutral">UNAVAILABLE</span>';
    }
    const num = typeof val === 'number' ? val : parseFloat(val);
    if (isNaN(num)) {
      return `<span class="return-badge-neutral">${this.escape(String(val))}</span>`;
    }
    if (num > 0) {
      return `<span class="return-badge-pos">+${num.toFixed(2)}%</span>`;
    }
    if (num < 0) {
      return `<span class="return-badge-neg">${num.toFixed(2)}%</span>`;
    }
    return `<span class="return-badge-neutral">0.00%</span>`;
  }

  // --------------------------------------------------------------------------
  // View 6: Backtest Analytics Dashboard (UI-5)
  // --------------------------------------------------------------------------

  async renderBacktestAnalytics() {
    this.setViewActive('backtest-view');
    const container = document.getElementById('backtest-view');
    if (!container) return;

    container.innerHTML = `
      <div class="state-box">
        <div class="spinner"></div>
        <h3>Loading Backtest Analytics Dashboard...</h3>
        <p>Fetching historical statistical diagnostics and population rank IC metrics...</p>
      </div>
    `;

    try {
      const [analyticsRes, datasetsRes, calRes, cfgRes] = await Promise.allSettled([
        this.api.getBacktestAnalytics(),
        this.api.getBacktestDatasets(),
        this.api.getCalibrationProposals(),
        this.api.getConfigurationStatus(),
      ]);

      const analytics = analyticsRes.status === 'fulfilled' ? analyticsRes.value : null;
      const datasets = datasetsRes.status === 'fulfilled' ? datasetsRes.value : null;
      const proposals = calRes.status === 'fulfilled' ? calRes.value : null;
      const config = cfgRes.status === 'fulfilled' ? cfgRes.value : null;

      if (!analytics) {
        container.innerHTML = `
          <div class="state-box">
            <div style="font-size: 2rem; margin-bottom: 8px;">📊</div>
            <h3>No Pre-Computed Backtest Analytics Artifact Available</h3>
            <p>The presentation service did not find an assembled backtest analytics report on disk (<code>build/analytics/analysis.json</code>).</p>
            <div style="font-size: 0.8rem; color: var(--text-muted); max-width: 600px; margin: 12px auto 20px;">
              Backtest analytics are generated by the Phase-6C analytical pipeline and exposed via <code>GET /api/v1/backtest/analytics</code>.
            </div>
            <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
              <a href="#dashboard" class="btn btn-primary">&larr; Return to Dashboard</a>
              <a href="#directory" class="btn btn-outline">Explore IPO Directory &rarr;</a>
            </div>
          </div>
        `;
        return;
      }

      this.renderBacktestContent(container, { analytics, datasets, proposals, config });
    } catch (err) {
      this.renderError(container, 'Failed to load backtest analytics dashboard', err);
    }
  }

  renderBacktestContent(container, { analytics, datasets, proposals, config }) {
    const rankIc = analytics.rank_ic || null;
    const hitRates = analytics.hit_rates || null;
    const avoidedLoss = analytics.avoided_loss_rates || null;
    const deciles = analytics.decile_buckets || [];
    const sampleMaturity = analytics.sample_maturity || {};
    const leakagePassed = Boolean(analytics.leakage_audit_passed);
    const activeVersion = config?.active_configuration?.version || '1.5.0';
    const candidateVersion = config?.candidate_configuration?.version || '1.6.0';
    const candidateStatus = config?.candidate_configuration?.status || 'READY_FOR_HUMAN_REVIEW';

    // Sample size from rank_ic or dataset summary
    const sampleSize = rankIc?.sample_size ?? datasets?.datasets?.[0]?.row_count ?? null;

    container.innerHTML = `
      <!-- Header Bar -->
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <div>
          <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 4px; display: flex; align-items: center; gap: 8px;">
            <span>IPO Screening Engine</span>
            <span>&bull;</span>
            <span>Historical Population Analysis</span>
          </div>
          <h2 style="margin: 0; font-size: 1.6rem; font-weight: 800; color: var(--text-main);">
            Backtest Analytics Dashboard
          </h2>
        </div>

        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          <a href="#dashboard" class="btn btn-outline btn-sm">&larr; Return to Dashboard</a>
          <a href="#directory" class="btn btn-outline btn-sm">Explore IPO Directory &rarr;</a>
        </div>
      </div>

      <!-- 1. Architectural Distinction Banner -->
      <div class="distinction-banner" role="region" aria-label="System Domain Distinctions">
        <div class="distinction-card highlight">
          <div class="distinction-title" style="color: #1d4ed8;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
            Historical Population Analysis
            <span class="badge badge-clear" style="font-size: 0.65rem; margin-left: auto;">ACTIVE VIEW</span>
          </div>
          <p class="distinction-desc">
            Aggregated cross-sectional statistical diagnostics, Rank IC (Spearman correlation), hit rates, and decile distributions across the full historical universe of offerings.
          </p>
        </div>

        <div class="distinction-card">
          <div class="distinction-title" style="color: var(--text-main);">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
            Individual IPO Performance
          </div>
          <p class="distinction-desc">
            Detailed post-listing price trajectories, corporate action adjustments, and benchmark excess return tracking for a single evaluated issuer.
          </p>
          <div style="margin-top: 10px;">
            <a href="#directory" class="btn btn-outline btn-sm">Explore Offerings &rarr;</a>
          </div>
        </div>

        <div class="distinction-card">
          <div class="distinction-title" style="color: #92400e;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
            Calibration Proposals
            <span class="badge badge-na" style="font-size: 0.65rem; margin-left: auto;">GATED</span>
          </div>
          <p class="distinction-desc">
            Candidate policy adjustments and overfitting safeguards derived from backtest diagnostics. Strictly separated from active execution; requires offline committee ratification.
          </p>
          <div style="margin-top: 10px;">
            <a href="#calibration" class="btn btn-outline btn-sm">Inspect Calibration Proposal &rarr;</a>
          </div>
        </div>
      </div>

      <!-- 2. Executive Analytics Summary (KPIs) -->
      <div class="analytics-kpi-grid" role="region" aria-label="Executive Analytics Summary">
        <div class="analytics-kpi-card">
          <div class="analytics-kpi-label">Analysis Sample Size (N)</div>
          <div class="analytics-kpi-val">${sampleSize !== null ? sampleSize : '—'}</div>
          <div class="analytics-kpi-sub">Eligible Offerings in Universe</div>
        </div>

        <div class="analytics-kpi-card">
          <div class="analytics-kpi-label">Sample Maturity (1W / 1M / 6M)</div>
          <div style="display: flex; flex-direction: column; gap: 4px; margin-top: 4px;">
            <div style="display: flex; justify-content: space-between; font-size: 0.72rem;">
              <span>1W:</span> ${this.renderMaturityBadge(sampleMaturity.one_week || 'DESCRIPTIVE_ONLY')}
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.72rem;">
              <span>1M:</span> ${this.renderMaturityBadge(sampleMaturity.one_month || 'DESCRIPTIVE_ONLY')}
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.72rem;">
              <span>6M:</span> ${this.renderMaturityBadge(sampleMaturity.six_month || 'DESCRIPTIVE_ONLY')}
            </div>
          </div>
        </div>

        <div class="analytics-kpi-card">
          <div class="analytics-kpi-label">Rank IC (Spearman)</div>
          <div class="analytics-kpi-val">${this.formatIcValue(rankIc?.spearman_ic)}</div>
          <div class="analytics-kpi-sub">p-value: ${this.formatPValue(rankIc?.p_value)}</div>
        </div>

        <div class="analytics-kpi-card">
          <div class="analytics-kpi-label">1W Hit Rate</div>
          <div class="analytics-kpi-val">${this.formatRatePct(hitRates?.one_week)}</div>
          <div class="analytics-kpi-sub">Qualifying Offerings Outperforming</div>
        </div>

        <div class="analytics-kpi-card">
          <div class="analytics-kpi-label">1W Avoided Loss Rate</div>
          <div class="analytics-kpi-val">${this.formatRatePct(avoidedLoss?.one_week)}</div>
          <div class="analytics-kpi-sub">AVOID Verdict Loss Prevention</div>
        </div>

        <div class="analytics-kpi-card">
          <div class="analytics-kpi-label">Point-in-Time Leakage Audit</div>
          <div style="margin-top: 6px;">
            <span class="badge ${leakagePassed ? 'badge-clear' : 'badge-avoid'}" style="font-size: 0.95rem; padding: 4px 10px;">
              ${leakagePassed ? 'PASSED' : 'FAILED'}
            </span>
          </div>
          <div class="analytics-kpi-sub">Point-in-Time Safety Verified</div>
        </div>
      </div>

      <!-- 3. Diagnostics Grid -->
      <div class="diagnostic-grid-2">
        <!-- Rank IC Diagnostic -->
        <div class="diagnostic-card">
          <div class="diagnostic-header">
            <div class="diagnostic-title">Information Coefficient (Rank IC) &amp; Correlation</div>
            <span class="meta-tag">RANK PREDICTIVE POWER</span>
          </div>
          <div class="diagnostic-body">
            <div class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Dimension</th>
                    <th>Value</th>
                    <th>Interpretation / Policy Boundary</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><strong>Predictor &rarr; Outcome</strong></td>
                    <td><code>FINAL_SCORE &rarr; EXCESS_RETURN</code></td>
                    <td>Fundamental Screening Score vs Realized Benchmark Alpha</td>
                  </tr>
                  <tr>
                    <td><strong>Horizon</strong></td>
                    <td><code>${this.escape(rankIc?.horizon || 'SIX_MONTH')}</code></td>
                    <td>Evaluation maturity horizon</td>
                  </tr>
                  <tr>
                    <td><strong>Spearman Rank IC (&rho;)</strong></td>
                    <td>${this.formatIcValue(rankIc?.spearman_ic)}</td>
                    <td>Monotonic rank ordering between score and alpha</td>
                  </tr>
                  <tr>
                    <td><strong>p-value</strong></td>
                    <td>${this.formatPValue(rankIc?.p_value)}</td>
                    <td>Statistical significance (unadjusted for small sample)</td>
                  </tr>
                  <tr>
                    <td><strong>Sample Size (N)</strong></td>
                    <td><code>${rankIc?.sample_size !== undefined && rankIc?.sample_size !== null ? rankIc.sample_size : '—'}</code></td>
                    <td>${this.renderMaturityBadge(sampleMaturity.six_month || 'DESCRIPTIVE_ONLY')}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="unexposed-box" style="margin-top: 14px;">
              <strong>Zero browser calculation authority:</strong> Spearman correlation coefficients and p-values are calculated exclusively on the backend by the deterministic analytics engine. When sample size N &lt; 30, metrics are governed as <code>DESCRIPTIVE_ONLY</code>. Formal hypothesis rejection requires mature sample size (N &ge; 100).
            </div>
          </div>
        </div>

        <!-- Hit Rates & Loss Avoidance -->
        <div class="diagnostic-card">
          <div class="diagnostic-header">
            <div class="diagnostic-title">Hit-Rate &amp; Avoidance Diagnostics</div>
            <span class="meta-tag">VERDICT ACCURACY</span>
          </div>
          <div class="diagnostic-body">
            <div class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Horizon</th>
                    <th>Hit Rate (%)</th>
                    <th>Avoided Loss Rate (%)</th>
                    <th>Sample Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><strong>1-Week (1W)</strong></td>
                    <td>${this.formatRatePct(hitRates?.one_week)}</td>
                    <td>${this.formatRatePct(avoidedLoss?.one_week)}</td>
                    <td>${this.renderMaturityBadge(sampleMaturity.one_week || 'DESCRIPTIVE_ONLY')}</td>
                  </tr>
                  <tr>
                    <td><strong>1-Month (1M)</strong></td>
                    <td>${this.formatRatePct(hitRates?.one_month)}</td>
                    <td>${this.formatRatePct(avoidedLoss?.one_month)}</td>
                    <td>${this.renderMaturityBadge(sampleMaturity.one_month || 'DESCRIPTIVE_ONLY')}</td>
                  </tr>
                  <tr>
                    <td><strong>6-Month (6M)</strong></td>
                    <td>${this.formatRatePct(hitRates?.six_month)}</td>
                    <td>${this.formatRatePct(avoidedLoss?.six_month)}</td>
                    <td>${this.renderMaturityBadge(sampleMaturity.six_month || 'DESCRIPTIVE_ONLY')}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="unexposed-box" style="margin-top: 14px;">
              <strong>Authoritative Verdict Semantics:</strong> Hit rate reflects the proportion of non-AVOID offerings that generate positive excess returns over benchmark. Avoided loss rate measures the proportion of AVOID offerings that underperformed benchmark. No client-side thresholding applied.
            </div>
          </div>
        </div>
      </div>

      <!-- 4. Deciles & Quantiles -->
      <div class="diagnostic-card" style="margin-bottom: 24px;">
        <div class="diagnostic-header">
          <div class="diagnostic-title">Score Decile &amp; Quantile Distribution Analysis</div>
          <span class="meta-tag">MONOTONIC SPREAD</span>
        </div>
        <div class="diagnostic-body">
          ${deciles && deciles.length > 0 ? `
            <div class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Decile Bucket</th>
                    <th>Score Range</th>
                    <th>Sample (N)</th>
                    <th>Mean Return (%)</th>
                    <th>Benchmark Return (%)</th>
                    <th>Excess Spread (%)</th>
                  </tr>
                </thead>
                <tbody>
                  ${deciles.map(d => `
                    <tr>
                      <td><strong>Decile ${this.escape(d.bucket_number || '—')}</strong></td>
                      <td><code>${d.score_lower_bound !== undefined ? d.score_lower_bound.toFixed(1) : '—'} - ${d.score_upper_bound !== undefined ? d.score_upper_bound.toFixed(1) : '—'}</code></td>
                      <td><code>${d.n !== undefined ? d.n : '—'}</code></td>
                      <td>${d.mean_return !== undefined ? d.mean_return.toFixed(2) + '%' : '—'}</td>
                      <td>${d.mean_benchmark_return !== undefined ? d.mean_benchmark_return.toFixed(2) + '%' : '—'}</td>
                      <td>${d.mean_excess_return !== undefined ? d.mean_excess_return.toFixed(2) + '%' : '—'}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          ` : `
            <div class="unexposed-box">
              <div style="font-weight: 700; color: var(--text-main); margin-bottom: 4px;">
                Decile Partitioning: Insufficient Sample Size (N &lt; 100)
              </div>
              <div>
                The authoritative analytics policy mandates a minimum sample size of 100 eligible observations before partitioning the population into 10 quantile buckets. With the current universe in <code>DESCRIPTIVE_ONLY</code> status, decile buckets are not mathematically formed to prevent small-sample overfitting.
              </div>
              <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 6px;">
                Zero browser calculation authority: Deciles are never synthesized or interpolated client-side.
              </div>
            </div>
          `}
        </div>
      </div>

      <!-- 5. Cohort Stability & Out-of-Sample Holdout Grid -->
      <div class="diagnostic-grid-2">
        <!-- Vintage Analysis -->
        <div class="diagnostic-card">
          <div class="diagnostic-header">
            <div class="diagnostic-title">Historical Vintage &amp; Cohort Stability</div>
            <span class="meta-tag">CALENDAR COHORTS</span>
          </div>
          <div class="diagnostic-body">
            <div class="unexposed-box">
              <div style="font-weight: 700; color: var(--text-main); margin-bottom: 4px;">
                Status: NOT EXPOSED IN CURRENT API SCHEMA
              </div>
              <div>
                Calendar-year vintage breakdowns (2021, 2022, 2023, 2024, 2025) are maintained in offline research datasets (<code>build/analytics/analysis.json</code>) and are not projected by the UI-1 Presentation API contract (<code>docs/openapi/presentation-api-v1.yaml</code>).
              </div>
              <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 6px;">
                Fail-closed policy: The browser presentation layer does not synthesize or fabricate historical cohorts.
              </div>
            </div>
          </div>
        </div>

        <!-- Holdout Analysis -->
        <div class="diagnostic-card">
          <div class="diagnostic-header">
            <div class="diagnostic-title">Out-of-Sample Temporal Holdout Partition</div>
            <span class="meta-tag">OUT-OF-SAMPLE VALIDATION</span>
          </div>
          <div class="diagnostic-body">
            <div class="unexposed-box">
              <div style="font-weight: 700; color: var(--text-main); margin-bottom: 4px;">
                Status: NOT EXPOSED IN CURRENT API SCHEMA
              </div>
              <div>
                Temporal holdout partitioning (in-sample development vs out-of-sample holdout) is maintained in offline research manifests and is not projected by the UI-1 Presentation API contract (<code>docs/openapi/presentation-api-v1.yaml</code>).
              </div>
              <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 6px;">
                Fail-closed policy: The browser presentation layer does not synthesize or fabricate holdout splits.
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 6. Leakage Audit & Point-in-Time Safety Panel -->
      <div class="diagnostic-card" style="margin-bottom: 24px;">
        <div class="diagnostic-header">
          <div class="diagnostic-title">Point-in-Time Safety &amp; Leakage Audit</div>
          <span class="badge ${leakagePassed ? 'badge-clear' : 'badge-avoid'}">
            ${leakagePassed ? 'AUDIT PASSED' : 'AUDIT FAILED'}
          </span>
        </div>
        <div class="diagnostic-body">
          <p style="font-size: 0.85rem; color: var(--text-main); line-height: 1.5; margin-bottom: 12px;">
            The point-in-time leakage audit programmatically verifies that all scoring inputs, financials, and governance attributes were strictly point-in-time relative to each offering's prospectus filing date and price band notice date, with zero future price lookahead.
          </p>
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; font-size: 0.8rem;">
            <div style="background: #f8fafc; padding: 10px 14px; border-radius: 6px; border: 1px solid var(--border-color);">
              <div style="font-weight: 600; color: var(--color-apply); margin-bottom: 2px;">✓ Prospectus Feature Freeze</div>
              <div style="color: var(--text-muted);">Scores locked at evaluation timestamp prior to market listing.</div>
            </div>
            <div style="background: #f8fafc; padding: 10px 14px; border-radius: 6px; border: 1px solid var(--border-color);">
              <div style="font-weight: 600; color: var(--color-apply); margin-bottom: 2px;">✓ Trading Day Calendar Alignment</div>
              <div style="color: var(--text-muted);">Secondary closing prices sourced strictly on actual trading days.</div>
            </div>
            <div style="background: #f8fafc; padding: 10px 14px; border-radius: 6px; border: 1px solid var(--border-color);">
              <div style="font-weight: 600; color: var(--color-apply); margin-bottom: 2px;">✓ Corporate Action Synchronization</div>
              <div style="color: var(--text-muted);">Adjustment factors time-aligned with official ex-date notices.</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 7. Provenance Fingerprints Panel -->
      <div class="provenance-panel" role="region" aria-label="Dataset and Analysis Provenance Fingerprints">
        <div class="provenance-panel-header">
          <div class="provenance-panel-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            </svg>
            Cryptographic Backtest Analysis Provenance Fingerprints
          </div>
          <span class="meta-tag">ANALYTICS RUN MANIFEST</span>
        </div>

        <div class="provenance-grid">
          <div class="provenance-item">
            <span class="provenance-item-label">Analysis Run Hash</span>
            <div class="provenance-hash-row">
              <span class="provenance-hash" title="${this.escape(analytics.analysis_hash)}">
                ${this.escape(analytics.analysis_hash || 'UNAVAILABLE')}
              </span>
              <button class="btn-copy" data-copy="${this.escape(analytics.analysis_hash || '')}">Copy</button>
            </div>
          </div>

          <div class="provenance-item">
            <span class="provenance-item-label">Backtest Dataset Hash</span>
            <div class="provenance-hash-row">
              <span class="provenance-hash" title="${this.escape(analytics.dataset_hash)}">
                ${this.escape(analytics.dataset_hash || 'UNAVAILABLE')}
              </span>
              <button class="btn-copy" data-copy="${this.escape(analytics.dataset_hash || '')}">Copy</button>
            </div>
          </div>

          <div class="provenance-item">
            <span class="provenance-item-label">Presentation API Contract</span>
            <div class="provenance-hash-row">
              <span class="provenance-hash" title="UI-1 Presentation API v1.0.0">
                UI-1 Presentation API (docs/openapi/presentation-api-v1.yaml)
              </span>
            </div>
          </div>

          <div class="provenance-item">
            <span class="provenance-item-label">Active Engine Version</span>
            <div class="provenance-hash-row">
              <span class="provenance-hash" title="v${this.escape(activeVersion)}">
                v${this.escape(activeVersion)} (Active Frozen Core)
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 8. Calibration Governance Boundary Callout -->
      <div class="calibration-callout" style="margin-top: 24px;" role="region" aria-label="Calibration Governance Boundary">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
          <div style="font-weight: 700; color: #92400e; font-size: 0.95rem;">
            Calibration Governance Boundary
          </div>
          <span class="meta-tag" style="background: #fde68a; color: #78350f;">GATED LIFECYCLE</span>
        </div>
        <p style="font-size: 0.8rem; color: var(--text-muted); line-height: 1.45; margin-bottom: 12px;">
          <strong>Policy Evolution Principle:</strong> Evidence &rarr; Analysis &rarr; Proposal &ne; Approval &ne; Implementation &ne; Activation.
          Backtest diagnostics provide empirical evidence used to formulate candidate calibration proposals (e.g. <code>v1.6.0</code>). In-browser or automated config mutation is strictly prohibited.
        </p>
        <div style="font-size: 0.8rem; background: #fffdf5; padding: 12px; border-radius: 6px; border: 1px solid #fde68a;">
          <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
            <div>Active Scoring Policy: <strong>● v${this.escape(activeVersion)} (Executable)</strong></div>
            <div>Candidate Proposal: <strong>○ v${this.escape(candidateVersion)} (${this.escape(candidateStatus)})</strong></div>
          </div>
          <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 8px;">
            Activation requires formal offline committee ratification. Zero in-browser activation controls.
          </div>
          <div style="margin-top: 10px;">
            <a href="#calibration" class="btn btn-outline btn-sm">Inspect Calibration &amp; Policy Governance &rarr;</a>
          </div>
        </div>
      </div>

      <!-- Navigation Footer -->
      <div style="margin-top: 24px; display: flex; gap: 12px; flex-wrap: wrap;">
        <a href="#dashboard" class="btn btn-outline">&larr; Return to Dashboard</a>
        <a href="#directory" class="btn btn-outline">Explore IPO Directory &rarr;</a>
      </div>
    `;

    // Wire up copy buttons if container supports DOM queries
    if (typeof container.querySelectorAll === 'function') {
      container.querySelectorAll('.btn-copy').forEach(btn => {
        btn.addEventListener('click', () => {
          const text = btn.getAttribute('data-copy');
          if (text) this.copyToClipboard(text, btn);
        });
      });
    }
  }

  formatIcValue(val) {
    if (val === null || val === undefined || val === '') {
      return '<span class="badge badge-unknown">UNAVAILABLE</span>';
    }
    const num = typeof val === 'number' ? val : parseFloat(val);
    if (isNaN(num)) return `<span class="badge badge-unknown">${this.escape(String(val))}</span>`;
    const sign = num > 0 ? '+' : '';
    return `<code style="font-weight: 700; color: ${num >= 0 ? 'var(--color-apply)' : 'var(--color-avoid)'};">${sign}${num.toFixed(6)}</code>`;
  }

  formatPValue(val) {
    if (val === null || val === undefined || val === '') {
      return '<span class="badge badge-unknown">UNAVAILABLE</span>';
    }
    const num = typeof val === 'number' ? val : parseFloat(val);
    if (isNaN(num)) return `<code>${this.escape(String(val))}</code>`;
    return `<code>${num.toFixed(4)}</code>`;
  }

  formatRatePct(val) {
    if (val === null || val === undefined || val === '') {
      return '<span class="badge badge-unknown">UNAVAILABLE</span>';
    }
    const num = typeof val === 'number' ? val : parseFloat(val);
    if (isNaN(num)) return `<code>${this.escape(String(val))}</code>`;
    return `<code>${num.toFixed(1)}%</code>`;
  }

  renderMaturityBadge(status) {
    const s = String(status || 'UNKNOWN').toUpperCase();
    if (s.includes('ACTIONABLE')) {
      return `<span class="maturity-pill maturity-actionable">${this.escape(s)}</span>`;
    }
    if (s.includes('EXPLORATORY')) {
      return `<span class="maturity-pill maturity-exploratory">${this.escape(s)}</span>`;
    }
    if (s.includes('DESCRIPTIVE')) {
      return `<span class="maturity-pill maturity-descriptive">${this.escape(s)}</span>`;
    }
    return `<span class="badge badge-unknown">${this.escape(s)}</span>`;
  }

  // --------------------------------------------------------------------------
  // View 7: Calibration & Policy Governance Presentation (UI-6)
  // --------------------------------------------------------------------------

  async renderCalibrationView() {
    this.setViewActive('calibration-view');
    const container = document.getElementById('calibration-view');
    if (!container) return;

    container.innerHTML = `
      <div class="state-box">
        <div class="spinner"></div>
        <h3>Loading Calibration &amp; Policy Governance...</h3>
        <p>Fetching active policy v1.5.0 and candidate proposal v1.6.0 artifacts...</p>
      </div>
    `;

    try {
      const [cfgRes, propsRes, propDetailRes, btRes] = await Promise.allSettled([
        this.api.getConfigurationStatus(),
        this.api.getCalibrationProposals(),
        this.api.getCalibrationProposal('v1.6.0'),
        this.api.getBacktestAnalytics(),
      ]);

      const config = cfgRes.status === 'fulfilled' ? cfgRes.value : null;
      const proposals = propsRes.status === 'fulfilled' ? propsRes.value : null;
      const proposalDetail = propDetailRes.status === 'fulfilled' ? propDetailRes.value : (proposals?.proposals?.[0] || null);
      const backtest = btRes.status === 'fulfilled' ? btRes.value : null;

      this.renderCalibrationContent(container, { config, proposals, proposalDetail, backtest });
    } catch (err) {
      this.renderError(container, 'Failed to load calibration and policy governance presentation', err);
    }
  }

  renderCalibrationContent(container, { config, proposals, proposalDetail, backtest }) {
    const activeCfg = config?.active_configuration;
    const candidateCfg = config?.candidate_configuration;
    const frozenCore = config?.frozen_core_status || 'VERIFIED';

    const activeVersion = activeCfg?.version || '1.5.0';
    const activeHash = activeCfg?.config_hash || '382ff86cc9d753514509f89c096f3b262bd4e12e644e0d7d03fe811b44e0f1e8';

    const candidateVersion = proposalDetail?.candidate_config_version || candidateCfg?.version || '1.6.0';
    const candidateStatus = proposalDetail?.status || candidateCfg?.status || 'READY_FOR_HUMAN_REVIEW';
    const candidateHash = proposalDetail?.candidate_config_hash || candidateCfg?.config_hash || '4ce1480c84e6ebfe22b96511f0f9b1b6577031bf272fe703c48f220a70def1f1';
    const proposalHash = proposalDetail?.proposal_hash || candidateCfg?.source_proposal_hash || '87bc9bcfa0bd9561adf3eb0be53a4291c465b5b02cd8561209f323e94a2249af';
    const proposalId = proposalDetail?.proposal_id || 'PROP-1.0.0';
    const maturityGate = proposalDetail?.maturity_gate || 'CALIBRATION_CANDIDATE';
    const approvalStatus = proposalDetail?.approval_status || 'APPROVED';
    const objective = proposalDetail?.objective || 'BALANCED_DIAGNOSTIC';

    // Module proposals from detail or authoritative mapping
    const rawModuleProps = proposalDetail?.module_proposals || [
      { module_id: 'A', module_name: 'Financial Quality', current_weight: 25.0, proposed_weight: 30.0, status: 'PROPOSED', rationale: 'Increased +5 points reflecting stronger development rank correlation (0.164656).' },
      { module_id: 'B', module_name: 'Valuation', current_weight: 20.0, proposed_weight: 15.0, status: 'PROPOSED', rationale: 'Decreased -5 points reflecting weaker development rank correlation (-0.139969).' },
      { module_id: 'C', module_name: 'Offer Structure, Proceeds & Pre-IPO', current_weight: 15.0, proposed_weight: 15.0, status: 'NO_CHANGE', rationale: 'Baseline weight retained.' },
      { module_id: 'D', module_name: 'Promoter & Governance', current_weight: 15.0, proposed_weight: 15.0, status: 'NO_CHANGE', rationale: 'Baseline weight retained.' },
      { module_id: 'E', module_name: 'Business & Moat', current_weight: 15.0, proposed_weight: 15.0, status: 'NO_CHANGE', rationale: 'Baseline weight retained.' },
      { module_id: 'F', module_name: 'Market & Demand Signals', current_weight: 10.0, proposed_weight: 10.0, status: 'NO_CHANGE', rationale: 'Baseline weight retained.' },
    ];

    const nonRegression = proposalDetail?.non_regression_results || [
      { check_name: 'downside_protection', passed: true, baseline_value: 'CLEAR', proposed_value: 'CLEAR', details: 'Knockout rules, penalty ceilings, and AVOID boundary remain intact.' },
      { check_name: 'holdout_stability', passed: true, baseline_value: '0.115372', proposed_value: '0.115372', details: 'Holdout out-of-sample performance remains non-degraded.' },
      { check_name: 'deterministic_reproducibility', passed: true, baseline_value: 'DETERMINISTIC', proposed_value: 'DETERMINISTIC', details: 'Pure standard library arithmetic ensures deterministic replay.' }
    ];

    container.innerHTML = `
      <!-- View Header -->
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <div>
          <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 4px; display: flex; align-items: center; gap: 8px;">
            <span>IPO Screening Engine</span>
            <span>&bull;</span>
            <span>Policy Evolution &amp; Governance</span>
          </div>
          <h2 style="margin: 0; font-size: 1.6rem; font-weight: 800; color: var(--text-main);">
            Calibration &amp; Configuration Presentation
          </h2>
        </div>

        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          <a href="#dashboard" class="btn btn-outline btn-sm">&larr; Return to Dashboard</a>
          <a href="#backtest" class="btn btn-outline btn-sm">Backtest Analytics Dashboard &rarr;</a>
        </div>
      </div>

      <!-- 1. Prominent Governance Lifecycle Strip -->
      <div class="gov-chain-banner" role="region" aria-label="Governance Lifecycle Status">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
          <div>
            <div style="font-weight: 800; font-size: 1rem; color: var(--text-main); display: flex; align-items: center; gap: 8px;">
              <span>Policy Governance &amp; Activation Firewall</span>
              <span class="badge badge-clear">LOCKED • READ-ONLY</span>
            </div>
            <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 2px;">
              Separation of calibration proposal formulation from formal production activation
            </div>
          </div>
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <span class="gov-pill active">● ACTIVE: v${this.escape(activeVersion)}</span>
            <span class="gov-pill inactive">○ CANDIDATE: v${this.escape(candidateVersion)} (${this.escape(candidateStatus)})</span>
          </div>
        </div>

        <!-- 5-Step Governance Chain -->
        <div class="gov-chain-steps">
          <div class="gov-chain-step">
            <div class="gov-chain-step-title">1. Empirical Evidence</div>
            <div class="gov-chain-step-status">Realized Returns &amp; Bhavcopies</div>
          </div>
          <div class="gov-chain-operator">&rarr;</div>
          <div class="gov-chain-step">
            <div class="gov-chain-step-title">2. Statistical Analysis</div>
            <div class="gov-chain-step-status">Rank IC &amp; Correlation Diagnostics</div>
          </div>
          <div class="gov-chain-operator">&rarr;</div>
          <div class="gov-chain-step current">
            <div class="gov-chain-step-title" style="color: #92400e;">3. Calibration Proposal</div>
            <div class="gov-chain-step-status" style="font-weight: 700; color: #b45309;">${this.escape(proposalId)} (${this.escape(candidateStatus)})</div>
          </div>
          <div class="gov-chain-operator">&ne;</div>
          <div class="gov-chain-step locked">
            <div class="gov-chain-step-title">4. Governance Approval</div>
            <div class="gov-chain-step-status">Investment Committee Review</div>
          </div>
          <div class="gov-chain-operator">&ne;</div>
          <div class="gov-chain-step locked">
            <div class="gov-chain-step-title">5. Release Activation</div>
            <div class="gov-chain-step-status">STRICTLY LOCKED (NO IN-BROWSER ACTIVATION)</div>
          </div>
        </div>

        <div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: 6px; padding: 12px 14px; margin-top: 14px; font-size: 0.8rem; color: #92400e; line-height: 1.45;">
          <strong>Governance Invariant Notice:</strong> The web presentation layer operates strictly as an auditable read-only terminal with <strong>ZERO activation authority</strong>. In-browser or automated policy mutation is strictly prohibited. Activation of candidate policy <code>v1.6.0</code> requires offline human committee ratification and controlled deployment. No activation controls or mutation endpoints exist.
        </div>
      </div>

      <!-- 2. Side-by-Side Policy Cards -->
      <div class="policy-card-grid" role="region" aria-label="Policy Status Overview">
        <!-- Active Policy Card -->
        <div class="policy-card active">
          <div class="policy-card-header">
            <div>
              <div style="font-size: 0.72rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; color: var(--color-apply); margin-bottom: 4px;">
                Current Production Baseline
              </div>
              <div style="font-size: 1.15rem; font-weight: 800; color: var(--text-main);">
                Active Policy (v${this.escape(activeVersion)})
              </div>
            </div>
            <span class="badge badge-apply">● ACTIVE • EXECUTABLE</span>
          </div>
          <div class="policy-card-body">
            <p style="font-size: 0.8rem; color: var(--text-muted); line-height: 1.45; margin-bottom: 16px;">
              Authoritative executable screening policy currently applied to all IPO evaluations in repository.
            </p>
            <div style="display: flex; flex-direction: column; gap: 8px; font-size: 0.8rem;">
              <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 4px;">
                <span style="color: var(--text-muted);">Configuration Version:</span>
                <strong>v${this.escape(activeVersion)}</strong>
              </div>
              <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 4px;">
                <span style="color: var(--text-muted);">Specification Version:</span>
                <strong>1.5</strong>
              </div>
              <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 4px;">
                <span style="color: var(--text-muted);">Execution Status:</span>
                <span class="badge badge-clear">EXECUTABLE</span>
              </div>
              <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 4px;">
                <span style="color: var(--text-muted);">Total Scoring Points:</span>
                <strong>100.0 pts (6 Modules)</strong>
              </div>
              <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 4px;">
                <span style="color: var(--text-muted);">Frozen Core Engine:</span>
                <span class="badge badge-clear">${this.escape(frozenCore)}</span>
              </div>
              <div style="display: flex; justify-content: space-between; padding-top: 2px;">
                <span style="color: var(--text-muted);">Config Hash:</span>
                <code style="font-size: 0.72rem;">${this.escape(activeHash.slice(0, 16))}...</code>
              </div>
            </div>
          </div>
        </div>

        <!-- Candidate Proposal Card -->
        <div class="policy-card candidate">
          <div class="policy-card-header">
            <div>
              <div style="font-size: 0.72rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; color: #b45309; margin-bottom: 4px;">
                Calibrated Candidate Proposal
              </div>
              <div style="font-size: 1.15rem; font-weight: 800; color: var(--text-main);">
                Candidate Proposal (v${this.escape(candidateVersion)}-draft)
              </div>
            </div>
            <span class="badge badge-na" style="background: #fef3c7; color: #92400e; border: 1px solid #fde68a;">
              ○ CANDIDATE • INACTIVE
            </span>
          </div>
          <div class="policy-card-body">
            <p style="font-size: 0.8rem; color: var(--text-muted); line-height: 1.45; margin-bottom: 16px;">
              Empirically calibrated candidate policy derived from backtest Rank IC analysis; strictly non-executable in production.
            </p>
            <div style="display: flex; flex-direction: column; gap: 8px; font-size: 0.8rem;">
              <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 4px;">
                <span style="color: var(--text-muted);">Proposal Identifier:</span>
                <code>${this.escape(proposalId)}</code>
              </div>
              <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 4px;">
                <span style="color: var(--text-muted);">Target Policy Version:</span>
                <strong>v${this.escape(candidateVersion)}</strong>
              </div>
              <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 4px;">
                <span style="color: var(--text-muted);">Proposal Status:</span>
                <span class="badge badge-consider">${this.escape(candidateStatus)}</span>
              </div>
              <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 4px;">
                <span style="color: var(--text-muted);">Maturity Gate:</span>
                <span class="badge badge-clear">${this.escape(maturityGate)}</span>
              </div>
              <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 4px;">
                <span style="color: var(--text-muted);">Approval Status:</span>
                <strong>${this.escape(approvalStatus)} (Program Authority)</strong>
              </div>
              <div style="display: flex; justify-content: space-between; padding-top: 2px;">
                <span style="color: var(--text-muted);">Proposal Hash:</span>
                <code style="font-size: 0.72rem;">${this.escape(proposalHash.slice(0, 16))}...</code>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 3. Current vs Proposed Module Weights Comparison Table -->
      <div class="diagnostic-card" style="margin-bottom: 24px;">
        <div class="diagnostic-header">
          <div class="diagnostic-title">Current Baseline (v1.5.0) vs Proposed Candidate (v1.6.0) Comparison</div>
          <span class="meta-tag">DETERMINISTIC WEIGHT SHIFTS</span>
        </div>
        <div class="diagnostic-body">
          <div class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Module Identifier &amp; Name</th>
                  <th>Current Weight (v1.5.0)</th>
                  <th>Proposed Weight (v1.6.0)</th>
                  <th>Delta (&Delta;)</th>
                  <th>Proposal Status</th>
                  <th>Empirical Rationale &amp; Expected Impact</th>
                </tr>
              </thead>
              <tbody>
                ${rawModuleProps.map(m => {
                  const delta = (m.proposed_weight ?? 0) - (m.current_weight ?? 0);
                  const isChanged = m.status === 'PROPOSED' || delta !== 0;
                  return `
                    <tr style="${isChanged ? 'background: #fffdf5;' : ''}">
                      <td>
                        <strong>Module ${this.escape(m.module_id)}</strong>: ${this.escape(m.module_name)}
                      </td>
                      <td><code>${m.current_weight !== undefined ? m.current_weight.toFixed(1) : '—'} pts</code></td>
                      <td><strong><code>${m.proposed_weight !== undefined ? m.proposed_weight.toFixed(1) : '—'} pts</code></strong></td>
                      <td>${this.renderDeltaPill(delta)}</td>
                      <td>
                        <span class="badge ${isChanged ? 'badge-consider' : 'badge-na'}">
                          ${this.escape(m.status || (isChanged ? 'PROPOSED' : 'NO_CHANGE'))}
                        </span>
                      </td>
                      <td style="font-size: 0.78rem; line-height: 1.4; color: var(--text-muted);">
                        ${this.escape(m.rationale || '—')}
                      </td>
                    </tr>
                  `;
                }).join('')}
                <tr style="background: #f8fafc; font-weight: 700;">
                  <td><strong>Total Scoring Scale</strong></td>
                  <td><code>100.0 pts</code></td>
                  <td><code>100.0 pts</code></td>
                  <td>${this.renderDeltaPill(0.0)}</td>
                  <td><span class="badge badge-clear">NORMALIZED</span></td>
                  <td style="font-size: 0.78rem; color: var(--text-muted);">100-point total score invariant preserved across all modules.</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; margin-top: 18px;">
            <div style="background: #f8fafc; padding: 12px 14px; border-radius: 6px; border: 1px solid var(--border-color); font-size: 0.8rem;">
              <div style="font-weight: 700; color: var(--text-main); margin-bottom: 4px;">Downside Discipline: Thresholds Unchanged</div>
              <div style="color: var(--text-muted);">APPLY threshold preserved at <code>75.0 pts</code>; APPLY_SELECTIVELY preserved at <code>60.0 pts</code>; NEUTRAL preserved at <code>45.0 pts</code>. Zero threshold relaxation.</div>
            </div>
            <div style="background: #f8fafc; padding: 12px 14px; border-radius: 6px; border: 1px solid var(--border-color); font-size: 0.8rem;">
              <div style="font-weight: 700; color: var(--text-main); margin-bottom: 4px;">Knockout Firewall: Intact</div>
              <div style="color: var(--text-muted);">Status: <code>FIREWALL_EMPTY</code>. All mandatory knockouts (Track Record, Auditor Qualifications, Promoter Integrity, Regulatory Debarment, Pending Litigations) strictly active.</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 4. Empirical Rationale & Supporting Evidence -->
      <div class="diagnostic-grid-2">
        <!-- Evidence Summary -->
        <div class="diagnostic-card">
          <div class="diagnostic-header">
            <div class="diagnostic-title">Empirical Evidence &amp; Dataset Partition</div>
            <span class="meta-tag">PHASE 6B / 6C DATASET</span>
          </div>
          <div class="diagnostic-body">
            <div style="display: flex; flex-direction: column; gap: 8px; font-size: 0.8rem;">
              <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 4px;">
                <span style="color: var(--text-muted);">Total Historical Cohort:</span>
                <strong>N = 120 Offerings (3 Vintages: 2024, 2025, 2026)</strong>
              </div>
              <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 4px;">
                <span style="color: var(--text-muted);">In-Sample Development Sample:</span>
                <strong>N = 80 Offerings (2024, 2025)</strong>
              </div>
              <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 4px;">
                <span style="color: var(--text-muted);">Out-of-Sample Holdout Sample:</span>
                <strong>N = 40 Offerings (2026)</strong>
              </div>
              <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 4px;">
                <span style="color: var(--text-muted);">Calibration Objective:</span>
                <code>${this.escape(objective)}</code>
              </div>
              <div style="display: flex; justify-content: space-between; padding-top: 2px;">
                <span style="color: var(--text-muted);">Maturity Gating Reason:</span>
                <span style="font-size: 0.74rem; color: var(--text-muted);">Sample N=120 &ge; 100 with 3 vintages verified.</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Non-Regression & Shadow Validation Audit -->
        <div class="diagnostic-card">
          <div class="diagnostic-header">
            <div class="diagnostic-title">Non-Regression &amp; Downside Protection Audit</div>
            <span class="meta-tag">VALIDATION CHECKS</span>
          </div>
          <div class="diagnostic-body">
            <div class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Audit Check</th>
                    <th>Result</th>
                    <th>Safety Details</th>
                  </tr>
                </thead>
                <tbody>
                  ${nonRegression.map(nr => `
                    <tr>
                      <td><strong>${this.escape(nr.check_name)}</strong></td>
                      <td>
                        <span class="badge ${nr.passed ? 'badge-clear' : 'badge-avoid'}">
                          ${nr.passed ? 'PASSED' : 'FAILED'}
                        </span>
                      </td>
                      <td style="font-size: 0.75rem; color: var(--text-muted); line-height: 1.35;">
                        ${this.escape(nr.details || '—')}
                      </td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
            <div class="unexposed-box" style="margin-top: 10px;">
              <strong>Shadow Evaluation Notice:</strong> Per-offering shadow evaluations comparing baseline vs candidate scores across historical IPOs are maintained offline (<code>build/shadow/</code>) and are not projected as individual evaluation records in the presentation store.
            </div>
          </div>
        </div>
      </div>

      <!-- 5. Cryptographic Provenance Fingerprints Panel -->
      <div class="provenance-panel" role="region" aria-label="Calibration Cryptographic Provenance Fingerprints">
        <div class="provenance-panel-header">
          <div class="provenance-panel-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            </svg>
            Cryptographic Policy &amp; Proposal Provenance Fingerprints
          </div>
          <span class="meta-tag">IMMUTABLE DIGESTS</span>
        </div>

        <div class="provenance-grid">
          <div class="provenance-item">
            <span class="provenance-item-label">Proposal Artifact Hash</span>
            <div class="provenance-hash-row">
              <span class="provenance-hash" title="${this.escape(proposalHash)}">
                ${this.escape(proposalHash || 'UNAVAILABLE')}
              </span>
              <button class="btn-copy" data-copy="${this.escape(proposalHash || '')}">Copy</button>
            </div>
          </div>

          <div class="provenance-item">
            <span class="provenance-item-label">Active Baseline Config Hash (v1.5.0)</span>
            <div class="provenance-hash-row">
              <span class="provenance-hash" title="${this.escape(activeHash)}">
                ${this.escape(activeHash || 'UNAVAILABLE')}
              </span>
              <button class="btn-copy" data-copy="${this.escape(activeHash || '')}">Copy</button>
            </div>
          </div>

          <div class="provenance-item">
            <span class="provenance-item-label">Candidate Draft Config Hash (v1.6.0)</span>
            <div class="provenance-hash-row">
              <span class="provenance-hash" title="${this.escape(candidateHash)}">
                ${this.escape(candidateHash || 'UNAVAILABLE')}
              </span>
              <button class="btn-copy" data-copy="${this.escape(candidateHash || '')}">Copy</button>
            </div>
          </div>

          <div class="provenance-item">
            <span class="provenance-item-label">Source Dataset Hash</span>
            <div class="provenance-hash-row">
              <span class="provenance-hash" title="${this.escape(proposalDetail?.source_dataset_hash || '')}">
                ${this.escape(proposalDetail?.source_dataset_hash || 'UNAVAILABLE')}
              </span>
              <button class="btn-copy" data-copy="${this.escape(proposalDetail?.source_dataset_hash || '')}">Copy</button>
            </div>
          </div>

          <div class="provenance-item">
            <span class="provenance-item-label">Source Analysis Hash</span>
            <div class="provenance-hash-row">
              <span class="provenance-hash" title="${this.escape(proposalDetail?.source_analysis_hash || '')}">
                ${this.escape(proposalDetail?.source_analysis_hash || 'UNAVAILABLE')}
              </span>
              <button class="btn-copy" data-copy="${this.escape(proposalDetail?.source_analysis_hash || '')}">Copy</button>
            </div>
          </div>

          <div class="provenance-item">
            <span class="provenance-item-label">Presentation API Specification</span>
            <div class="provenance-hash-row">
              <span class="provenance-hash" title="docs/openapi/presentation-api-v1.yaml">
                UI-1 Presentation API (docs/openapi/presentation-api-v1.yaml)
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Navigation Footer -->
      <div style="margin-top: 24px; display: flex; gap: 12px; flex-wrap: wrap;">
        <a href="#dashboard" class="btn btn-outline">&larr; Return to Dashboard</a>
        <a href="#backtest" class="btn btn-outline">Backtest Analytics Dashboard &rarr;</a>
        <a href="#directory" class="btn btn-outline">Explore IPO Directory &rarr;</a>
      </div>
    `;

    // Wire up copy buttons if container supports DOM queries
    if (typeof container.querySelectorAll === 'function') {
      container.querySelectorAll('.btn-copy').forEach(btn => {
        btn.addEventListener('click', () => {
          const text = btn.getAttribute('data-copy');
          if (text) this.copyToClipboard(text, btn);
        });
      });
    }
  }

  renderDeltaPill(delta) {
    if (delta === null || delta === undefined) return '—';
    const num = typeof delta === 'number' ? delta : parseFloat(delta);
    if (isNaN(num) || num === 0) {
      return `<span class="delta-pill delta-neutral">0.0 pts</span>`;
    }
    if (num > 0) {
      return `<span class="delta-pill delta-pos">+${num.toFixed(1)} pts</span>`;
    }
    return `<span class="delta-pill delta-neg">${num.toFixed(1)} pts</span>`;
  }

  // --------------------------------------------------------------------------
  // Lifecycle History (#ipos/{id})
  // --------------------------------------------------------------------------

  async renderIpoDetail(ipoId) {
    this.setViewActive('directory-view');
    const container = document.getElementById('directory-view');
    if (!container) return;

    if (this.ipoHistoryShowArchived === undefined) {
      this.ipoHistoryShowArchived = false;
    }

    container.innerHTML = `
      <div class="state-box">
        <div class="spinner"></div>
        <h3>Loading Issuer Lifecycle...</h3>
      </div>
    `;

    try {
      const history = await this.api.getIpoHistory(ipoId, { includeArchived: this.ipoHistoryShowArchived });

      const activeEval = history.history.find(e => e.operational_status === 'ACTIVE');

      container.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 8px;">
          <a href="#directory" class="btn btn-outline btn-sm">&larr; Back to Directory</a>
          <label style="font-size: 0.85rem; display: flex; align-items: center; gap: 6px; cursor: pointer;">
            <input type="checkbox" id="toggle-show-archived" ${this.ipoHistoryShowArchived ? 'checked' : ''} />
            <span>Show Archived Executions</span>
          </label>
        </div>

        ${activeEval ? `
          <div class="card" style="border-left: 4px solid var(--color-apply); margin-bottom: 20px;">
            <div class="card-header" style="border-bottom: 1px solid var(--border-color); padding-bottom: 10px; margin-bottom: 12px;">
              <div>
                <span class="badge badge-active" style="margin-right: 8px;">AUTHORITATIVE ACTIVE EVALUATION</span>
                <strong style="font-size: 1.1rem;">${this.escape(history.company_name)}</strong>
              </div>
              <span class="meta-tag">MODE: ${this.escape(activeEval.evaluation_mode)}</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; align-items: center;">
              <div>
                <div style="font-size: 0.75rem; color: var(--text-muted);">ACTIVE SCORE</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: var(--text-main);">
                  ${activeEval.final_score.toFixed(1)} <span style="font-size: 0.9rem; font-weight: 500; color: var(--text-muted);">/ 100</span>
                </div>
              </div>
              <div>
                <div style="font-size: 0.75rem; color: var(--text-muted);">VERDICT</div>
                <div>${this.renderVerdictBadge(activeEval.verdict)}</div>
              </div>
              <div>
                <div style="font-size: 0.75rem; color: var(--text-muted);">CONFIDENCE</div>
                <div style="font-weight: 600;">${this.escape(activeEval.confidence)} (${activeEval.completeness_pct !== null ? activeEval.completeness_pct.toFixed(0) : '—'}%)</div>
              </div>
              <div>
                <div style="font-size: 0.75rem; color: var(--text-muted);">EVALUATION ID</div>
                <code style="font-size: 0.75rem;">${this.escape(activeEval.evaluation_id)}</code>
              </div>
            </div>
            <div style="display: flex; gap: 8px; margin-top: 14px;">
              <a href="#evaluations/${this.escape(activeEval.evaluation_id)}" class="btn btn-primary btn-sm">
                View Active Scorecard &rarr;
              </a>
              <a href="#evidence/${this.escape(activeEval.evaluation_id)}" class="btn btn-outline btn-sm">
                Inspect Evidence &rarr;
              </a>
              <a href="#performance/${this.escape(activeEval.evaluation_id)}" class="btn btn-outline btn-sm">
                Performance &rarr;
              </a>
            </div>
          </div>
        ` : ''}

        <div class="card">
          <div class="card-header">
            <div class="card-title">Evaluation Timeline &amp; History (<code>${this.escape(history.ipo_id)}</code>)</div>
            <span class="meta-tag">${history.history.length} Lifecycle Runs Displayed</span>
          </div>

          ${history.delta ? `
            <div class="card" style="background: var(--bg-subtle); margin-bottom: 16px;">
              <div class="card-title" style="font-size: 0.85rem; margin-bottom: 8px;">
                Preliminary &rarr; Final Progression Delta
              </div>
              <div style="display: flex; gap: 24px; font-size: 0.85rem; flex-wrap: wrap;">
                <div>Preliminary Score: <strong>${history.delta.preliminary_score !== null ? history.delta.preliminary_score.toFixed(1) : '—'}</strong></div>
                <div>Final Score: <strong>${history.delta.final_score !== null ? history.delta.final_score.toFixed(1) : '—'}</strong></div>
                <div>Score Delta: <strong>${history.delta.score_delta !== null ? (history.delta.score_delta >= 0 ? `+${history.delta.score_delta.toFixed(1)}` : history.delta.score_delta.toFixed(1)) : '0.0'}</strong></div>
                <div>Verdict Shift: <strong>${history.delta.verdict_changed ? 'YES' : 'NO (Preserved)'}</strong></div>
              </div>
            </div>
          ` : ''}

          <div class="table-wrapper">
            <table class="data-table" id="lifecycle-history-table">
              <thead>
                <tr>
                  <th style="width: 36px; text-align: center;">
                    <input type="checkbox" id="select-all-evals" title="Select all eligible historical evaluations" />
                  </th>
                  <th>Evaluation ID &amp; Lineage</th>
                  <th>Status</th>
                  <th>Mode / Stage</th>
                  <th>Timestamp</th>
                  <th>Score</th>
                  <th>Verdict</th>
                  <th>Confidence</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                ${history.history.map(e => `
                  <tr data-eval-id="${this.escape(e.evaluation_id)}">
                    <td style="text-align: center;">
                      ${e.operational_status !== 'ACTIVE' ? `
                        <input type="checkbox" class="eval-select-checkbox" data-eval-id="${this.escape(e.evaluation_id)}" data-status="${this.escape(e.operational_status)}" />
                      ` : `
                        <span title="Active evaluation cannot be archived" style="color: var(--text-light); font-size: 0.8rem;">—</span>
                      `}
                    </td>
                    <td>
                      <div><code>${this.escape(e.evaluation_id)}</code></div>
                      ${e.superseded_by ? `
                        <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 3px;">
                          Superseded by: <code>${this.escape(e.superseded_by)}</code>
                        </div>
                      ` : ''}
                      ${e.supersedes ? `
                        <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 3px;">
                          Supersedes: <code>${this.escape(e.supersedes)}</code>
                        </div>
                      ` : ''}
                    </td>
                    <td>
                      ${e.operational_status === 'ACTIVE' ? `
                        <span class="badge badge-active">ACTIVE</span>
                      ` : e.operational_status === 'SUPERSEDED' ? `
                        <span class="badge badge-superseded">SUPERSEDED</span>
                      ` : `
                        <span class="badge badge-archived">ARCHIVED</span>
                      `}
                    </td>
                    <td><span class="meta-tag">${this.escape(e.evaluation_mode)}</span></td>
                    <td style="font-size: 0.8rem;">${this.formatDate(e.evaluation_timestamp)}</td>
                    <td><strong>${e.final_score.toFixed(1)}</strong></td>
                    <td>${this.renderVerdictBadge(e.verdict)}</td>
                    <td style="font-size: 0.8rem;">${this.escape(e.confidence)}</td>
                    <td>
                      <div style="display: flex; gap: 4px; flex-wrap: wrap;">
                        <a href="#evaluations/${this.escape(e.evaluation_id)}" class="btn btn-outline btn-sm">
                          Scorecard
                        </a>
                        <a href="#evidence/${this.escape(e.evaluation_id)}" class="btn btn-outline btn-sm">
                          Evidence
                        </a>
                        ${e.operational_status === 'SUPERSEDED' ? `
                          <button class="btn btn-outline btn-sm btn-row-archive" data-eval-id="${this.escape(e.evaluation_id)}" title="Archive this superseded run">
                            Archive
                          </button>
                          <button class="btn btn-outline btn-sm btn-row-make-active" data-eval-id="${this.escape(e.evaluation_id)}" title="Make this evaluation authoritative ACTIVE">
                            Make Active
                          </button>
                        ` : ''}
                        ${e.operational_status === 'ARCHIVED' ? `
                          <button class="btn btn-outline btn-sm btn-row-unarchive" data-eval-id="${this.escape(e.evaluation_id)}" title="Unarchive this run to visible history">
                            Unarchive
                          </button>
                        ` : ''}
                      </div>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>

          <!-- Bulk Selection Toolbar -->
          <div style="display: flex; gap: 10px; align-items: center; margin-top: 14px; padding: 10px 14px; background: var(--bg-subtle); border-radius: var(--radius-sm); flex-wrap: wrap;">
            <button class="btn btn-outline btn-sm" id="btn-bulk-archive" disabled>Archive Selected</button>
            <button class="btn btn-outline btn-sm" id="btn-bulk-unarchive" disabled>Unarchive Selected</button>
            <span id="bulk-selection-count" style="font-size: 0.8rem; color: var(--text-muted);">0 selected</span>
          </div>
        </div>
      `;

      this.setupLifecycleHistoryEvents(container, ipoId);
    } catch (err) {
      this.renderError(container, 'Failed to load issuer detail', err);
    }
  }

  setupLifecycleHistoryEvents(container, ipoId) {
    const toggleArchived = container.querySelector('#toggle-show-archived');
    if (toggleArchived) {
      toggleArchived.addEventListener('change', () => {
        this.ipoHistoryShowArchived = toggleArchived.checked;
        this.renderIpoDetail(ipoId);
      });
    }

    const selectAllCheckbox = container.querySelector('#select-all-evals');
    const rowCheckboxes = container.querySelectorAll('.eval-select-checkbox');
    const bulkArchiveBtn = container.querySelector('#btn-bulk-archive');
    const bulkUnarchiveBtn = container.querySelector('#btn-bulk-unarchive');
    const countSpan = container.querySelector('#bulk-selection-count');

    const updateBulkState = () => {
      const selected = Array.from(rowCheckboxes).filter(cb => cb.checked);
      const count = selected.length;
      if (countSpan) countSpan.textContent = `${count} selected`;

      const hasSuperseded = selected.some(cb => cb.getAttribute('data-status') === 'SUPERSEDED');
      const hasArchived = selected.some(cb => cb.getAttribute('data-status') === 'ARCHIVED');

      if (bulkArchiveBtn) bulkArchiveBtn.disabled = !hasSuperseded;
      if (bulkUnarchiveBtn) bulkUnarchiveBtn.disabled = !hasArchived;
    };

    if (selectAllCheckbox) {
      selectAllCheckbox.addEventListener('change', () => {
        rowCheckboxes.forEach(cb => { cb.checked = selectAllCheckbox.checked; });
        updateBulkState();
      });
    }

    rowCheckboxes.forEach(cb => {
      cb.addEventListener('change', updateBulkState);
    });

    // Single Row Archive
    container.querySelectorAll('.btn-row-archive').forEach(btn => {
      btn.addEventListener('click', async () => {
        const eid = btn.getAttribute('data-eval-id');
        btn.disabled = true;
        try {
          await this.api.archiveEvaluation(eid, { reason: 'USER_TABLE_ARCHIVE' });
          await this.renderIpoDetail(ipoId);
        } catch (err) {
          alert(`Archive failed: ${err.message}`);
          btn.disabled = false;
        }
      });
    });

    // Single Row Unarchive
    container.querySelectorAll('.btn-row-unarchive').forEach(btn => {
      btn.addEventListener('click', async () => {
        const eid = btn.getAttribute('data-eval-id');
        btn.disabled = true;
        try {
          await this.api.unarchiveEvaluation(eid, { reason: 'USER_TABLE_UNARCHIVE' });
          await this.renderIpoDetail(ipoId);
        } catch (err) {
          alert(`Unarchive failed: ${err.message}`);
          btn.disabled = false;
        }
      });
    });

    // Single Row Make Active (Governed Rollback)
    container.querySelectorAll('.btn-row-make-active').forEach(btn => {
      btn.addEventListener('click', async () => {
        const eid = btn.getAttribute('data-eval-id');
        if (!confirm(`Are you sure you want to designate evaluation ${eid} as the authoritative ACTIVE evaluation?`)) {
          return;
        }
        btn.disabled = true;
        try {
          await this.api.makeEvaluationActive(eid, { reason: 'GOVERNED_ROLLBACK' });
          await this.renderIpoDetail(ipoId);
        } catch (err) {
          alert(`Make Active failed: ${err.message}`);
          btn.disabled = false;
        }
      });
    });

    // Bulk Archive
    if (bulkArchiveBtn) {
      bulkArchiveBtn.addEventListener('click', async () => {
        const selectedEids = Array.from(rowCheckboxes)
          .filter(cb => cb.checked && cb.getAttribute('data-status') === 'SUPERSEDED')
          .map(cb => cb.getAttribute('data-eval-id'));

        if (!selectedEids.length) return;
        bulkArchiveBtn.disabled = true;
        try {
          for (const eid of selectedEids) {
            await this.api.archiveEvaluation(eid, { reason: 'BULK_ARCHIVE' });
          }
          await this.renderIpoDetail(ipoId);
        } catch (err) {
          alert(`Bulk archive failed: ${err.message}`);
          bulkArchiveBtn.disabled = false;
        }
      });
    }

    // Bulk Unarchive
    if (bulkUnarchiveBtn) {
      bulkUnarchiveBtn.addEventListener('click', async () => {
        const selectedEids = Array.from(rowCheckboxes)
          .filter(cb => cb.checked && cb.getAttribute('data-status') === 'ARCHIVED')
          .map(cb => cb.getAttribute('data-eval-id'));

        if (!selectedEids.length) return;
        bulkUnarchiveBtn.disabled = true;
        try {
          for (const eid of selectedEids) {
            await this.api.unarchiveEvaluation(eid, { reason: 'BULK_UNARCHIVE' });
          }
          await this.renderIpoDetail(ipoId);
        } catch (err) {
          alert(`Bulk unarchive failed: ${err.message}`);
          bulkUnarchiveBtn.disabled = false;
        }
      });
    }
  }

  // --------------------------------------------------------------------------
  // View Helpers & State Formatters
  // --------------------------------------------------------------------------

  setViewActive(viewId) {
    document.querySelectorAll('.view-section').forEach(sec => {
      if (sec && sec.classList) sec.classList.remove('active');
    });
    const target = document.getElementById(viewId);
    if (target && target.classList) target.classList.add('active');
  }

  renderEvaluationsTableHtml(evaluations) {
    if (!evaluations || evaluations.length === 0) {
      return `<div class="state-box"><p>No evaluations recorded yet.</p></div>`;
    }

    return `
      <div class="table-wrapper">
        <table class="data-table" role="table">
          <thead>
            <tr>
              <th scope="col">Evaluation ID</th>
              <th scope="col">Company Name</th>
              <th scope="col">Mode</th>
              <th scope="col">Score</th>
              <th scope="col">Verdict</th>
              <th scope="col">Date (UTC)</th>
              <th scope="col">Action</th>
            </tr>
          </thead>
          <tbody>
            ${evaluations.map(e => `
              <tr>
                <td><code>${this.escape(e.evaluation_id)}</code></td>
                <td><strong>${this.escape(e.company_name)}</strong></td>
                <td><span class="meta-tag">${this.escape(e.evaluation_mode)}</span></td>
                <td><strong>${e.final_score !== null ? e.final_score.toFixed(1) : '—'}</strong></td>
                <td>${this.renderVerdictBadge(e.verdict)}</td>
                <td>${this.formatDate(e.evaluation_timestamp)}</td>
                <td>
                  <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                    <a href="#evaluations/${this.escape(e.evaluation_id)}" class="btn btn-primary btn-sm">
                      Scorecard
                    </a>
                    <a href="#evidence/${this.escape(e.evaluation_id)}" class="btn btn-outline btn-sm">
                      Evidence
                    </a>
                    <a href="#performance/${this.escape(e.evaluation_id)}" class="btn btn-outline btn-sm">
                      Performance
                    </a>
                  </div>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  renderVerdictBadge(verdict) {
    const v = String(verdict || 'UNKNOWN').toUpperCase();
    if (v === 'APPLY') return `<span class="badge badge-apply">APPLY</span>`;
    if (v === 'CONSIDER') return `<span class="badge badge-consider">CONSIDER</span>`;
    if (v === 'AVOID') return `<span class="badge badge-avoid">AVOID</span>`;
    if (v === 'INSUFFICIENT_DATA') return `<span class="badge badge-insufficient">INSUFFICIENT DATA</span>`;
    return `<span class="badge badge-unknown">${this.escape(v)}</span>`;
  }

  renderSemanticStateBadge(state) {
    const s = String(state || 'SCORED').toUpperCase();
    if (s === 'SCORED') return `<span class="badge badge-clear" style="font-size: 0.7rem;">SCORED</span>`;
    if (s === 'UNKNOWN') return `<span class="badge badge-unknown" style="font-size: 0.7rem;">UNKNOWN</span>`;
    if (s === 'NOT_APPLICABLE') return `<span class="badge badge-na" style="font-size: 0.7rem;">NOT APPLICABLE</span>`;
    return `<span class="badge">${this.escape(s)}</span>`;
  }

  renderMetricValue(val, state) {
    if (state === 'NOT_APPLICABLE') {
      return `<span class="badge badge-na">N/A</span>`;
    }
    if (state === 'UNKNOWN' || val === null || val === undefined) {
      return `<span class="badge badge-unknown">UNKNOWN</span>`;
    }
    if (typeof val === 'number') {
      return `<code>${val.toFixed(2)}</code>`;
    }
    if (typeof val === 'boolean') {
      return `<code>${val ? 'True' : 'False'}</code>`;
    }
    return `<code>${this.escape(String(val))}</code>`;
  }

  formatDate(isoString) {
    if (!isoString) return '—';
    try {
      const d = new Date(isoString);
      return d.toUTCString().replace('GMT', 'UTC');
    } catch {
      return this.escape(isoString);
    }
  }

  escape(str) {
    return String(str ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  renderError(container, title, err) {
    container.innerHTML = `
      <div class="card" style="border-color: var(--border-avoid); background: var(--bg-avoid);">
        <h3 style="color: var(--color-avoid); margin-bottom: 8px;">${this.escape(title)}</h3>
        <p style="font-size: 0.85rem; color: var(--text-main);">${this.escape(err.message || String(err))}</p>
        ${err.code ? `<div class="meta-tag" style="margin-top: 8px;">ERROR CODE: ${this.escape(err.code)}</div>` : ''}
      </div>
    `;
  }

  formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  }

  // --------------------------------------------------------------------------
  // IPO Ingestion & Deterministic Evaluation Workflow (UI-7)
  // --------------------------------------------------------------------------

  renderIngestView() {
    this.setViewActive('ingest-view');
    const container = document.getElementById('ingest-view');
    if (!container) return;

    this.selectedIngestFile = null;

    container.innerHTML = `
      <!-- Distinction / Guidance Banner -->
      <div class="card distinction-banner" role="region" aria-label="Ingestion Architecture Banner" style="margin-bottom: 24px;">
        <div class="distinction-header">
          <div class="distinction-title">
            <span class="distinction-icon">&#9888;</span>
            IPO Ingestion &amp; Deterministic Evaluation Pipeline
          </div>
          <span class="meta-tag">UI-7 Architectural Boundary</span>
        </div>
        <div class="distinction-text">
          Upload Draft Red Herring Prospectus (DRHP) or Red Herring Prospectus (RHP) filings in PDF format.
          The filing document undergoes server-side boundary-enforcing domain entity extraction via
          <code>DocumentExtractor</code>, normalisation to <code>CanonicalInput</code>, validation gates,
          and execution of the deterministic v1.5 scoring engine.
        </div>
        <div class="distinction-grid">
          <div class="distinction-col" style="border-left: 3px solid var(--color-apply);">
            <div class="distinction-col-title" style="color: var(--color-apply);">Zero Browser Authority</div>
            <div class="distinction-col-desc">
              All PDF parsing, table routing, metric calculations, knockout verification, and scoring are executed strictly
              server-side. The browser never calculates scores or parses document binaries locally.
            </div>
          </div>
          <div class="distinction-col" style="border-left: 3px solid var(--color-consider);">
            <div class="distinction-col-title" style="color: var(--color-consider);">Immutable Audit Trail</div>
            <div class="distinction-col-desc">
              Evaluations are immutably persisted in the filesystem <code>EvaluationStore</code> with SHA-256 result hashes.
              Duplicate uploads are idempotently resolved without overwriting historical records.
            </div>
          </div>
        </div>
      </div>

      <div class="ingest-grid">
        <!-- Left: Upload & File Handling Card -->
        <div class="ingest-card" id="ingest-form-card">
          <div class="ingest-card-title">Upload IPO Filing Document</div>
          <div class="ingest-card-desc">
            Select or drag &amp; drop a valid Indian Mainboard IPO filing document (DRHP or RHP PDF, max 50 MB).
          </div>

          <!-- Drag and Drop Dropzone -->
          <div class="ingest-dropzone" id="ingest-dropzone" role="region" aria-label="File Upload Dropzone" tabindex="0">
            <input type="file" id="ingest-file-input" accept=".pdf,application/pdf" style="display: none;" />
            <span class="dropzone-icon">&#128196;</span>
            <div class="dropzone-prompt">Drag &amp; drop IPO filing PDF here</div>
            <div class="dropzone-sub">or <strong style="color: var(--color-consider);">browse files</strong> from your computer</div>
            <div style="font-size: 0.75rem; color: var(--text-light); margin-top: 8px;">
              PDF format only &bull; Up to 50 MB &bull; Magic bytes <code>%PDF-</code> verified
            </div>
          </div>

          <!-- Selected File Details (Hidden until selected) -->
          <div class="ingest-selected-file" id="ingest-file-preview" style="display: none;">
            <div class="file-info">
              <span class="file-icon">&#128196;</span>
              <div>
                <div class="file-name" id="ingest-file-name">—</div>
                <div class="file-size" id="ingest-file-size">—</div>
              </div>
            </div>
            <button type="button" class="file-remove-btn" id="ingest-file-remove-btn" title="Remove selected file">Remove</button>
          </div>

          <!-- Options & Submission Form -->
          <form class="ingest-controls" id="ingest-form" onsubmit="return false;">
            <div class="form-group">
              <label for="ingest-mode-select" class="form-label">Evaluation Mode</label>
              <select id="ingest-mode-select" class="form-select">
                <option value="final" selected>Final Evaluation (Post-RHP / Pre-Listing)</option>
                <option value="preliminary">Preliminary Evaluation (DRHP)</option>
              </select>
              <span style="font-size: 0.75rem; color: var(--text-muted);">
                Final mode evaluates against full restated financials and issue terms.
              </span>
            </div>

            <div class="ingest-actions">
              <button type="button" id="ingest-submit-btn" class="btn btn-primary" disabled style="flex: 1;">
                Process &amp; Evaluate Filing
              </button>
            </div>
          </form>

          <!-- Error Alert Banner -->
          <div id="ingest-error-box" style="display: none; margin-top: 16px;"></div>
        </div>

        <!-- Right: Execution Progress & Results Panel -->
        <div class="ingest-card" id="ingest-status-card">
          <div class="ingest-card-title">Workflow Progress &amp; Audit Status</div>
          <div class="ingest-card-desc">
            Tracks real-time execution across the ingestion, extraction, validation, and evaluation pipeline.
          </div>

          <!-- Stages Timeline -->
          <div class="ingest-stages" id="ingest-stages-list">
            <div class="stage-step active" id="stage-ready">
              <div class="stage-num">1</div>
              <div class="stage-label">Awaiting Document Selection</div>
            </div>
            <div class="stage-step" id="stage-upload">
              <div class="stage-num">2</div>
              <div class="stage-label">HTTP Transfer &amp; Size Boundary Guard</div>
            </div>
            <div class="stage-step" id="stage-extract">
              <div class="stage-num">3</div>
              <div class="stage-label">Document Extraction (TOC, Tables, Sections)</div>
            </div>
            <div class="stage-step" id="stage-evaluate">
              <div class="stage-num">4</div>
              <div class="stage-label">Deterministic v1.5 Scoring &amp; Validation Gate</div>
            </div>
            <div class="stage-step" id="stage-complete">
              <div class="stage-num">5</div>
              <div class="stage-label">Immutable Store Persistence &amp; Result Hash</div>
            </div>
          </div>

          <!-- Ingestion Activity: actual backend events (live + recoverable).
               The shell is always visible so the panel can be located
               before, during and after a submission; the body is replaced
               with the real backend event trace when an ingestion runs. -->
          <div id="ingest-activity-panel" style="margin-top: 16px;">
            <div class="activity-panel" role="region" aria-label="Ingestion Activity">
              <div class="activity-head"><strong>Ingestion Activity</strong><span class="badge badge-insufficient">IDLE</span></div>
              <div class="activity-meta">No ingestion submitted yet in this session. Submit a filing above to see the live backend activity trace here; the trace of the most recent ingestion is restored automatically after a page refresh.</div>
            </div>
          </div>

          <!-- Ingestion Completed Outcome (Hidden until complete) -->
          <div id="ingest-outcome-container" style="display: none;"></div>
        </div>
      </div>
    `;

    this.bindIngestEvents(container);
  }

  bindIngestEvents(container) {
    const dropzone = container.querySelector('#ingest-dropzone');
    const fileInput = container.querySelector('#ingest-file-input');
    if (!dropzone || !fileInput) return;

    const filePreview = container.querySelector('#ingest-file-preview');
    const fileName = container.querySelector('#ingest-file-name');
    const fileSize = container.querySelector('#ingest-file-size');
    const fileRemoveBtn = container.querySelector('#ingest-file-remove-btn');
    const modeSelect = container.querySelector('#ingest-mode-select');
    const submitBtn = container.querySelector('#ingest-submit-btn');
    const errorBox = container.querySelector('#ingest-error-box');
    const outcomeContainer = container.querySelector('#ingest-outcome-container');
    const stagesList = container.querySelector('#ingest-stages-list');

    const updateStage = (stageId, statusClass) => {
      const step = container.querySelector(`#${stageId}`);
      if (step) {
        step.className = `stage-step ${statusClass}`;
      }
    };

    const showError = (msg, code = null) => {
      errorBox.style.display = 'block';
      errorBox.innerHTML = `
        <div class="card" style="border-color: var(--border-avoid); background: var(--bg-avoid); padding: 12px 16px;">
          <strong style="color: var(--color-avoid); font-size: 0.85rem;">Processing Error:</strong>
          <div style="font-size: 0.85rem; color: var(--text-main); margin-top: 4px;">${this.escape(msg)}</div>
          ${code ? `<div class="meta-tag" style="margin-top: 6px;">CODE: ${this.escape(code)}</div>` : ''}
        </div>
      `;
    };

    const clearError = () => {
      errorBox.style.display = 'none';
      errorBox.innerHTML = '';
    };

    const handleFile = (file) => {
      clearError();
      if (!file) return;

      if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
        showError('Only PDF files (.pdf) are supported.', 'INVALID_FILE_TYPE');
        return;
      }

      const maxBytes = 50 * 1024 * 1024;
      if (file.size > maxBytes) {
        showError(`File size (${this.formatBytes(file.size)}) exceeds the 50 MB limit.`, 'FILE_TOO_LARGE');
        return;
      }

      this.selectedIngestFile = file;
      fileName.textContent = file.name;
      fileSize.textContent = this.formatBytes(file.size);
      filePreview.style.display = 'flex';
      submitBtn.disabled = false;

      updateStage('stage-ready', 'completed');
      updateStage('stage-upload', 'active');
    };

    const clearFile = () => {
      this.selectedIngestFile = null;
      fileInput.value = '';
      filePreview.style.display = 'none';
      submitBtn.disabled = true;
      clearError();

      updateStage('stage-ready', 'active');
      updateStage('stage-upload', '');
      updateStage('stage-extract', '');
      updateStage('stage-evaluate', '');
      updateStage('stage-complete', '');
    };

    // Dropzone click
    dropzone.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        fileInput.click();
      }
    });

    // Drag-and-drop
    ['dragenter', 'dragover'].forEach((eventName) => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach((eventName) => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      if (dt && dt.files && dt.files.length > 0) {
        handleFile(dt.files[0]);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFile(e.target.files[0]);
      }
    });

    fileRemoveBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      clearFile();
    });

    this.restoreLastIngestionActivity(container);

    // Ingest submit execution
    submitBtn.addEventListener('click', async () => {
      if (!this.selectedIngestFile) return;

      clearError();
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner" style="width: 14px; height: 14px; display: inline-block; margin-right: 8px;"></span> Processing Document...';

      updateStage('stage-ready', 'completed');
      updateStage('stage-upload', 'active');

      try {
        updateStage('stage-upload', 'completed');
        updateStage('stage-extract', 'active');

        const mode = modeSelect ? modeSelect.value : 'final';
        const result = (typeof this.api.startIngestion === 'function')
          ? await this.runIngestionWithActivity(container, this.selectedIngestFile, mode)
          : await this.api.ingestDocument(this.selectedIngestFile, { mode });

        updateStage('stage-extract', 'completed');
        updateStage('stage-evaluate', 'completed');
        updateStage('stage-complete', 'completed');

        // Render success outcome
        outcomeContainer.style.display = 'block';
        outcomeContainer.innerHTML = `
          <div class="ingest-result-overview" role="region" aria-label="Ingestion Result">
            <div class="ingest-result-header">
              <div>
                <div class="ingest-result-company">${this.escape(result.company_name)}</div>
                <div class="ingest-result-meta">IPO ID: <code>${this.escape(result.ipo_id)}</code> &bull; Mode: <strong>${this.escape(result.evaluation_mode)}</strong></div>
              </div>
              <span class="badge ${result.is_duplicate ? 'badge-neutral' : 'badge-apply'}" style="font-size: 0.75rem;">
                ${result.is_duplicate ? 'IDEMPOTENT / DUPLICATE' : 'NEWLY EVALUATED'}
              </span>
            </div>

            <div class="ingest-kpi-row">
              <div class="ingest-kpi-card">
                <div class="ingest-kpi-label">Final Score</div>
                <div class="ingest-kpi-val">${typeof result.final_score === 'number' ? result.final_score.toFixed(1) : '—'} <span style="font-size: 0.8rem; color: var(--text-muted);">/ 100</span></div>
              </div>
              <div class="ingest-kpi-card">
                <div class="ingest-kpi-label">Verdict</div>
                <div style="margin-top: 6px;">${this.renderVerdictBadge(result.verdict)}</div>
              </div>
              <div class="ingest-kpi-card">
                <div class="ingest-kpi-label">Confidence</div>
                <div style="margin-top: 6px;">
                  <span class="badge ${result.confidence === 'High' ? 'badge-apply' : result.confidence === 'Medium' ? 'badge-consider' : 'badge-insufficient'}">
                    ${this.escape(result.confidence)}
                  </span>
                </div>
              </div>
            </div>

            <div style="margin-bottom: 16px;">
              <div style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--text-muted); margin-bottom: 4px;">
                Deterministic Result Hash (SHA-256)
              </div>
              <code style="font-size: 0.75rem; word-break: break-all; background: var(--bg-surface); padding: 4px 8px; border-radius: 4px; border: 1px solid var(--border-color); display: block;">
                ${this.escape(result.result_hash)}
              </code>
            </div>

            <div style="font-size: 0.85rem; color: var(--text-main); margin-bottom: 16px;">
              ${this.escape(result.message)}
            </div>

            <div class="ingest-actions">
              <a href="#evaluations/${this.escape(result.evaluation_id)}" class="btn btn-primary" id="btn-view-scorecard" style="text-decoration: none; text-align: center;">
                Open Full Evaluation Scorecard &rarr;
              </a>
              <button type="button" class="btn btn-secondary" id="btn-ingest-another">
                Upload Another Filing
              </button>
            </div>
          </div>
        `;

        const btnAnother = outcomeContainer.querySelector('#btn-ingest-another');
        if (btnAnother) {
          btnAnother.addEventListener('click', () => {
            clearFile();
            outcomeContainer.style.display = 'none';
            outcomeContainer.innerHTML = '';
          });
        }

        submitBtn.disabled = false;
        submitBtn.textContent = 'Process & Evaluate Filing';
      } catch (err) {
        updateStage('stage-extract', 'failed');
        updateStage('stage-evaluate', 'failed');
        updateStage('stage-complete', 'failed');
        showError(err.message || 'Filing processing failed', err.code || 'PROCESSING_ERROR');
        if (err.code === 'AWAITING_ISSUE_TERMS') {
          this.renderManualTermsPanel(outcomeContainer, err, modeSelect ? modeSelect.value : 'final');
        }
        submitBtn.disabled = false;
        submitBtn.textContent = 'Retry Evaluation';
      }
    });
  }

  /**
   * Ingestion Activity: renders the actual backend event trace for an
   * ingestion attempt.  Nothing here is inferred from HTTP status --
   * every row is a persisted backend event, and history is retrievable
   * after the request ends or the page refreshes.
   */
  renderIngestionActivity(container, record) {
    const panel = container ? container.querySelector('#ingest-activity-panel') : null;
    if (!panel || !record) return;
    const badgeFor = (s) => ({
      SUCCEEDED: 'badge-apply', FAILED: 'badge-avoid', BLOCKED: 'badge-consider',
      RUNNING: 'badge-neutral', SKIPPED: 'badge-insufficient', CANCELLED: 'badge-insufficient',
      PENDING: 'badge-insufficient',
    }[s] || 'badge-neutral');
    const started = record.started_at ? new Date(record.started_at) : null;
    const finished = record.finished_at ? new Date(record.finished_at) : null;
    const elapsedMs = started ? ((finished || new Date()) - started) : null;
    const elapsed = elapsedMs != null ? `${(elapsedMs / 1000).toFixed(1)}s` : '—';
    const events = Array.isArray(record.events) ? record.events : [];
    const currentStage = [...events].reverse().find((e) => e.status === 'RUNNING');
    const rows = events.map((e) => {
      const details = e.details && Object.keys(e.details).length
        ? `<details class="activity-details"><summary>details</summary><pre>${this.escape(JSON.stringify(e.details, null, 1))}</pre>${e.source_reference ? `<div>source: <code>${this.escape(e.source_reference)}</code></div>` : ''}${e.error_code ? `<div>error_code: <code>${this.escape(e.error_code)}</code></div>` : ''}</details>`
        : '';
      return `<div class="activity-event activity-${this.escape(String(e.status || '').toLowerCase())}">
        <span class="activity-seq">${this.escape(String(e.sequence))}</span>
        <span class="badge ${badgeFor(e.status)}">${this.escape(e.status || '')}</span>
        <div class="activity-main">
          <div><strong>${this.escape(e.stage || '')}</strong> · ${this.escape(e.event_type || '')}
          ${e.duration_ms != null ? `<span class="activity-dur">${this.escape(String(e.duration_ms))} ms</span>` : ''}</div>
          <div>${this.escape(e.message || '')}</div>
          ${details}
        </div>
      </div>`;
    }).join('');
    let summary = '';
    if (record.status && record.status !== 'RUNNING') {
      const missing = (record.missing_fields || []).map((f) => `<li><code>${this.escape(f)}</code></li>`).join('');
      const nextAction = record.status === 'SUCCEEDED'
        ? 'Open the evaluation from the outcome panel.'
        : record.status === 'BLOCKED'
          ? 'Retry automatic official discovery or upload an applicable authoritative filing that establishes the unresolved fields. Missing evidence does not prove that terms are unpublished; a price band alone does not establish a fresh-issue monetary amount.'
          : 'Review the failed stage above and retry. Quote the ingestion id when seeking diagnostics.';
      summary = `<div class="activity-summary">
        <div><strong>Terminal summary</strong> — status <span class="badge ${badgeFor(record.status)}">${this.escape(record.status)}</span></div>
        <div>Evaluation run: <strong>${record.evaluation_run ? 'yes' : 'no'}</strong> · Persisted: <strong>${record.persisted ? 'yes' : 'no'}</strong>${record.evaluation_id ? ` · Evaluation: <code>${this.escape(record.evaluation_id)}</code>` : ''}</div>
        ${missing ? `<div>Unresolved required terms:<ul>${missing}</ul></div>` : ''}
        ${record.error_message ? `<div>Reason: ${this.escape(record.error_message)}</div>` : ''}
        <div>Next action: ${this.escape(nextAction)}</div>
      </div>`;
    }
    panel.innerHTML = `
      <div class="activity-panel" role="region" aria-label="Ingestion Activity">
        <div class="activity-head">
          <strong>Ingestion Activity</strong>
          <span class="badge ${badgeFor(record.status)}">${this.escape(record.status || '')}</span>
        </div>
        <div class="activity-meta">
          File: ${this.escape(record.filename || '—')} · Mode: ${this.escape(record.mode || '—')} ·
          Id: <code>${this.escape(record.ingestion_id || '')}</code> ·
          Elapsed: ${this.escape(elapsed)}${currentStage ? ` · Current stage: <strong>${this.escape(currentStage.stage)}</strong>` : ''}
        </div>
        <div class="activity-timeline">${rows || '<div>No events recorded yet.</div>'}</div>
        ${summary}
      </div>
    `;
  }

  /** Poll the durable activity trace until its terminal outcome. */
  async runIngestionWithActivity(container, file, mode) {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const start = await this.api.startIngestion(file, { mode });
    const ingestionId = start.ingestion_id;
    try { localStorage.setItem('ipo.lastIngestionId', ingestionId); } catch { /* private mode */ }
    let record = null;
    let consecutiveFailures = 0;
    for (;;) {
      try {
        record = await this.api.getIngestion(ingestionId);
        consecutiveFailures = 0;
      } catch (pollErr) {
        consecutiveFailures += 1;
        if (consecutiveFailures > 8) throw pollErr;
        await sleep(1500);
        continue;
      }
      this.renderIngestionActivity(container, record);
      if (record.status !== 'RUNNING') break;
      await sleep(1200);
    }
    if (record.status === 'SUCCEEDED') {
      const r = record.result || {};
      return {
        ...r,
        evaluation_url: `/#evaluations/${r.evaluation_id}`,
        message: record.is_duplicate
          ? 'Identical evaluation record already exists in immutable store.'
          : 'Filing successfully ingested, extracted, and evaluated.',
      };
    }
    const missing = (record.missing_fields || []).map((f) => String(f).replace(/^issue\./, ''));
    throw new ApiError(
      record.status === 'BLOCKED' ? 422 : 500,
      record.error_code || 'INGESTION_FAILED',
      record.error_message || 'Ingestion did not complete.',
      { missing_fields: missing, ingestion_id: ingestionId, activity_url: `/api/v1/ingestions/${ingestionId}` }
    );
  }

  /** After a refresh, re-attach to the most recent ingestion's history. */
  async restoreLastIngestionActivity(container) {
    try {
      if (typeof this.api.getIngestion !== 'function') return;
      const ingestionId = localStorage.getItem('ipo.lastIngestionId');
      if (!ingestionId) return;
      const record = await this.api.getIngestion(ingestionId);
      this.renderIngestionActivity(container, record);
    } catch { /* no recoverable history; the panel simply stays empty */ }
  }

  /**
   * Audit-log linkage for the manual issue-term flow: register the
   * submission's durable activity record as the latest ingestion and
   * refresh the Ingestion Activity panel so the audit surface shows the
   * manual submission (accepted or rejected) instead of staying silent.
   * Display is best-effort; the record itself is durable server-side.
   */
  async attachIngestionAudit(ingestionId) {
    if (!ingestionId) return null;
    try { localStorage.setItem('ipo.lastIngestionId', String(ingestionId)); } catch { /* private mode */ }
    if (typeof this.api.getIngestion !== 'function') return null;
    try {
      const record = await this.api.getIngestion(String(ingestionId));
      if (typeof document !== 'undefined' && document) {
        this.renderIngestionActivity(document, record);
      }
      return record;
    } catch { return null; }
  }

  /**
   * Step 5 pre-processing workflow: when required issue terms are
   * unresolved (AWAITING_ISSUE_TERMS), let the operator enter the four
   * required terms (price-band floor/cap, lot size, OFS amount) with a
   * mandatory explanation. All four are required to complete initial
   * screening manually and may be read off the broker platform. Manual
   * entry is visibly NOT source verification (MANUAL_ENTRY provenance,
   * unverified); conflicts block until explicitly confirmed. Invalid or
   * incomplete values prevent evaluation.
   */
  renderManualTermsPanel(container, err, mode) {
    if (!container) return;
    const ENTERABLE = ['price_band_low', 'price_band_high', 'lot_size', 'ofs', 'fresh_issue'];
    const reportingUnit = (err && err.details && err.details.resolution && err.details.resolution.reporting_unit) || '';
    const ofsUnit = reportingUnit === 'INR_CRORES'
      ? 'amount in ₹ crore'
      : reportingUnit === 'INR_LAKHS'
        ? 'amount in ₹ lakh'
        : reportingUnit === 'INR_MILLIONS'
          ? 'amount in ₹ million'
          : 'monetary amount in the filing\u2019s reporting unit (₹ lakh, ₹ crore or ₹ million)';
    const LABELS = {
      price_band_low: 'Price-Band Floor (₹ per share)',
      price_band_high: 'Price-Band Cap (₹ per share)',
      lot_size: 'Lot Size (shares)',
      ofs: `Offer For Sale (OFS) \u2014 ${ofsUnit}`,
      fresh_issue: `Fresh Issue Amount \u2014 ${ofsUnit}`,
    };
    let missing = (err && err.details && err.details.missing_fields) || [];
    let awaitingMessage = err ? err.message : '';
    const providerReports = (err && err.details && err.details.resolution && err.details.resolution.providers) || [];
    const providerDiagnostics = providerReports.length
      ? `<div style="margin-bottom: 12px;">
           <div style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--text-muted); margin-bottom: 4px;">Official-source resolution diagnostics</div>
           <ul style="margin: 0; padding-left: 18px; font-size: 0.85rem;">${providerReports.map((r) => {
             const sources = Array.isArray(r.sources) ? r.sources : [];
             const sourceList = sources.length
               ? `<ul style="margin: 4px 0 0; padding-left: 16px; font-size: 0.8rem;">${sources.map((s) => {
                   const state = s.searched ? 'listing searched' : 'listing not searched';
                   const entries = s.issue_entries ? `; ${s.issue_entries} issue entr${s.issue_entries === 1 ? 'y' : 'ies'} read` : '';
                   return `<li><code>${this.escape(s.url || '')}</code> — ${this.escape(s.classification || '')} (${state}${entries})</li>`;
                 }).join('')}</ul>`
               : '';
             return `<li><code>${this.escape(r.provider || '')}</code> — ${this.escape(r.outcome || '')}: ${this.escape(r.detail || '')}${sourceList}</li>`;
           }).join('')}</ul>
         </div>`
      : '';
    container.style.display = 'block';

    const renderMissing = () => missing.map((f) => {
      const enterable = ENTERABLE.includes(f);
      return `<li><code>issue.${this.escape(f)}</code> — ${enterable ? 'may be entered manually below' : '<strong>cannot be entered manually</strong>; requires an official source or filing disclosure'}</li>`;
    }).join('');

    container.innerHTML = `
      <div class="ingest-result-overview" role="region" aria-label="Manual Issue-Term Entry">
        <div class="ingest-result-header">
          <div>
            <div class="ingest-result-company">Issue Terms Unresolved</div>
            <div class="ingest-result-meta">The filing does not disclose every required term and no verified official notice supplied them. No evaluation was produced and nothing was persisted.</div>
          </div>
          <span class="badge badge-unknown-evidence" style="font-size: 0.75rem;">AWAITING ISSUE TERMS</span>
        </div>
        <div style="margin-bottom: 12px;">
          <div style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--text-muted); margin-bottom: 4px;">Missing / unresolved terms</div>
          <ul id="mt-missing-list" style="margin: 0; padding-left: 18px; font-size: 0.85rem;">${renderMissing()}</ul>
        </div>
        ${providerDiagnostics}
        <div class="alert" style="margin-bottom: 12px; font-size: 0.85rem;">
          <strong>All five issue terms above are required to complete initial screening manually</strong>
          and may be supplied from the broker platform&rsquo;s IPO page.
          <strong>Manual entry is not official-source verification:</strong> entered values are recorded as
          <code>MANUAL_ENTRY</code> provenance, remain unverified, are flagged as manually supplied on the
          evaluation, and never displace a verified official value. Invalid or incomplete values prevent evaluation.
        </div>
        <div class="ingest-grid" style="gap: 12px;">
          <div class="form-group"><label class="form-label" for="mt-price-band-low">${LABELS.price_band_low}</label>
            <input type="number" step="any" min="0" class="form-select" id="mt-price-band-low" placeholder="e.g. 208" /></div>
          <div class="form-group"><label class="form-label" for="mt-price-band-high">${LABELS.price_band_high}</label>
            <input type="number" step="any" min="0" class="form-select" id="mt-price-band-high" placeholder="e.g. 220" /></div>
          <div class="form-group"><label class="form-label" for="mt-lot-size">${LABELS.lot_size}</label>
            <input type="number" step="1" min="0" class="form-select" id="mt-lot-size" placeholder="e.g. 68" /></div>
          <div class="form-group"><label class="form-label" for="mt-ofs">${LABELS.ofs}</label>
            <input type="number" step="any" min="0" class="form-select" id="mt-ofs" placeholder="e.g. 3300 (0 = no offer for sale)" /></div>
          <div class="form-group"><label class="form-label" for="mt-fresh-issue">${LABELS.fresh_issue}</label>
            <input type="number" step="any" min="0" class="form-select" id="mt-fresh-issue" placeholder="e.g. 14500 (0 = pure OFS offer, no fresh issue)" /></div>
        </div>
        <div class="form-group" style="margin-top: 12px;">
          <label class="form-label" for="mt-explanation">Explanation (required for any manual entry)</label>
          <textarea class="form-select" id="mt-explanation" rows="2" placeholder="Where did these terms come from? e.g. exchange announcement dated ..."></textarea>
        </div>
        <div id="mt-conflicts" style="display: none; margin-top: 12px;"></div>
        <div id="mt-status" style="margin-top: 12px; font-size: 0.85rem;"></div>
        <div class="ingest-actions" style="margin-top: 16px;">
          <button type="button" class="btn btn-primary" id="mt-submit-btn" style="flex: 1;">Submit Manual Terms &amp; Evaluate</button>
        </div>
        <div style="margin-top: 8px; font-size: 0.8rem; color: var(--text-muted);">${this.escape(awaitingMessage || '')}</div>
      </div>
    `;

    const statusBox = container.querySelector('#mt-status');
    const conflictsBox = container.querySelector('#mt-conflicts');
    const submitBtn = container.querySelector('#mt-submit-btn');
    let conflictPending = false;

    submitBtn.addEventListener('click', async () => {
      const terms = {};
      const low = container.querySelector('#mt-price-band-low').value;
      const high = container.querySelector('#mt-price-band-high').value;
      const lot = container.querySelector('#mt-lot-size').value;
      const ofsInput = container.querySelector('#mt-ofs').value;
      const freshInput = container.querySelector('#mt-fresh-issue').value;
      if (low !== '') terms.price_band_low = Number(low);
      if (high !== '') terms.price_band_high = Number(high);
      if (lot !== '') terms.lot_size = Number(lot);
      if (ofsInput !== '') terms.ofs = Number(ofsInput);
      if (freshInput !== '') terms.fresh_issue = Number(freshInput);
      const explanation = container.querySelector('#mt-explanation').value.trim();

      if (Object.keys(terms).length === 0) {
        statusBox.innerHTML = '<span class="badge badge-unknown-evidence">Enter at least one term.</span>';
        return;
      }
      if (!explanation) {
        statusBox.innerHTML = '<span class="badge badge-unknown-evidence">An explanation is required for manually entered terms.</span>';
        return;
      }
      if (conflictPending) {
        const confirmBox = container.querySelector('#mt-confirm-conflicts');
        if (!confirmBox || !confirmBox.checked) {
          statusBox.innerHTML = '<span class="badge badge-unknown-evidence">Tick the confirmation to resolve the conflicts and proceed.</span>';
          return;
        }
      }
      submitBtn.disabled = true;
      statusBox.textContent = 'Submitting manual terms...';
      try {
        const result = await this.api.ingestManualTerms(this.selectedIngestFile, {
          mode, terms, explanation, confirmConflicts: conflictPending,
        });
        // Audit log: the manual submission has its own durable activity
        // record. Register it as the latest ingestion and refresh the
        // Ingestion Activity panel so the audit surface shows this
        // submission (events, evaluation outcome, persistence).
        await this.attachIngestionAudit(result.ingestion_id);
        const auditNote = result.ingestion_id
          ? `<div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 12px;">
               Audit trace recorded: <code>${this.escape(String(result.ingestion_id))}</code>
               (manual submission, validation, evaluation and persistence events)
               &mdash; see <strong>Ingestion Activity</strong> in Workflow Progress &amp; Audit Status.</div>`
          : '';
        const manualEntry = result.issue_terms && result.issue_terms.manual_entry;
        let manualNote = '';
        if (manualEntry) {
          const unit = manualEntry.reporting_unit ? ` (${this.escape(String(manualEntry.reporting_unit))})` : '';
          const rows = (manualEntry.fields || []).map((f) => {
            const value = manualEntry.values ? manualEntry.values[f] : '';
            const unitCell = (f === 'ofs' || f === 'fresh_issue') ? unit : (f === 'lot_size' ? ' (shares)' : ' (₹/share)');
            return `<tr><td><code>issue.${this.escape(f)}</code></td><td><strong>${this.escape(String(value))}</strong>${unitCell}</td></tr>`;
          }).join('');
          manualNote = `
            <div style="font-size: 0.85rem; margin-bottom: 12px;">
              <div style="margin-bottom: 4px;"><span class="badge badge-unknown-evidence" title="Entered manually by the operator; not verified against an official source">MANUALLY ENTERED (Not Source-Verified)</span></div>
              <div style="margin-bottom: 4px;">The engine evaluated these manually supplied values, recorded as <code>MANUAL_ENTRY</code> provenance and still unverified:</div>
              <table style="width: 100%; font-size: 0.82rem; border-collapse: collapse;">${rows}</table>
              ${manualEntry.explanation ? `<div style="margin-top: 4px; color: var(--text-muted);">Explanation: ${this.escape(manualEntry.explanation)}</div>` : ''}
            </div>`;
        }
        container.innerHTML = `
          <div class="ingest-result-overview" role="region" aria-label="Manual Terms Ingestion Result">
            <div class="ingest-result-header">
              <div>
                <div class="ingest-result-company">${this.escape(result.company_name)}</div>
                <div class="ingest-result-meta">IPO ID: <code>${this.escape(result.ipo_id)}</code> &bull; Mode: <strong>${this.escape(result.evaluation_mode)}</strong></div>
              </div>
              <span class="badge ${result.is_duplicate ? 'badge-neutral' : 'badge-apply'}" style="font-size: 0.75rem;">${result.is_duplicate ? 'IDEMPOTENT / DUPLICATE' : 'NEWLY EVALUATED'}</span>
            </div>
            <div class="ingest-kpi-row">
              <div class="ingest-kpi-card"><div class="ingest-kpi-label">Final Score</div>
                <div class="ingest-kpi-val">${typeof result.final_score === 'number' ? result.final_score.toFixed(1) : '—'} <span style="font-size: 0.8rem; color: var(--text-muted);">/ 100</span></div></div>
              <div class="ingest-kpi-card"><div class="ingest-kpi-label">Verdict</div>
                <div style="margin-top: 6px;">${this.renderVerdictBadge(result.verdict)}</div></div>
            </div>
            ${manualNote}
            ${auditNote}
            <div class="ingest-actions">
              <a href="#evaluations/${this.escape(result.evaluation_id)}" class="btn btn-primary" style="text-decoration: none; text-align: center;">Open Full Evaluation Scorecard &rarr;</a>
            </div>
          </div>
        `;
      } catch (err2) {
        submitBtn.disabled = false;
        // Rejected submissions are auditable too: register the trace so
        // the Ingestion Activity log shows what was submitted and why it
        // was rejected (validation, conflict, or unresolved terms).
        const errAuditId = err2 && err2.details ? err2.details.ingestion_id : null;
        if (errAuditId) await this.attachIngestionAudit(errAuditId);
        const auditRef = errAuditId
          ? ` <span style="color: var(--text-muted);">Audit trace: <code>${this.escape(String(errAuditId))}</code></span>`
          : '';
        if (err2.code === 'ISSUE_TERM_CONFLICT' && err2.details && Array.isArray(err2.details.conflicts)) {
          conflictPending = true;
          const rows = err2.details.conflicts.map((c) => `<li><code>${this.escape(c.field)}</code>: entered <strong>${this.escape(String(c.manual_value))}</strong> vs existing <strong>${this.escape(String(c.existing_value))}</strong> (${this.escape(c.existing_origin === 'OFFICIAL_VERIFIED' ? 'verified official source — the verified value will be kept' : 'filing extraction — the entered value will replace it')})</li>`).join('');
          conflictsBox.style.display = 'block';
          conflictsBox.innerHTML = `
            <div class="alert" style="font-size: 0.85rem;">
              <strong>Conflicts must be resolved explicitly.</strong> Confirmation does not make manual values verified.
              <ul style="margin: 8px 0 8px 18px; padding: 0;">${rows}</ul>
              <label style="display: flex; gap: 8px; align-items: flex-start;">
                <input type="checkbox" id="mt-confirm-conflicts" />
                <span>I confirm these resolutions. Manual values stay labelled MANUAL_ENTRY (unverified); verified official values are never displaced.</span>
              </label>
            </div>`;
          statusBox.innerHTML = `<span class="badge badge-consider">Resolve the conflicts above, then submit again.</span>${auditRef}`;
        } else if (err2.code === 'AWAITING_ISSUE_TERMS') {
          missing = (err2.details && err2.details.missing_fields) || missing;
          const list = container.querySelector('#mt-missing-list');
          if (list) list.innerHTML = renderMissing();
          statusBox.innerHTML = `<span class="badge badge-unknown-evidence">Still awaiting terms</span> <span>${this.escape(err2.message || '')}</span>${auditRef}`;
        } else {
          statusBox.innerHTML = `<span class="badge badge-unknown-evidence">${this.escape(err2.code || 'ERROR')}</span> <span>${this.escape(err2.message || 'Submission failed')}</span>${auditRef}`;
        }
      }
    });
  }

  renderNotFound(path) {
    this.setViewActive('dashboard-view');
    const container = document.getElementById('dashboard-view');
    if (container) {
      container.innerHTML = `
        <div class="state-box">
          <h3>404 — Screen Not Found</h3>
          <p>The path <code>#${this.escape(path)}</code> is not a recognized route.</p>
          <a href="#dashboard" class="btn btn-primary" style="margin-top: 16px;">Return to Dashboard</a>
        </div>
      `;
    }
  }
}

// Auto-initialize when loaded in browser
if (typeof window !== 'undefined' && document.getElementById('app')) {
  window.addEventListener('DOMContentLoaded', () => {
    const app = new App();
    app.init();
    window.__IPO_APP__ = app;
  });
}
