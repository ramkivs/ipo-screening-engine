/**
 * IPO Screening Engine — Presentation Application (UI-2 & UI-3)
 *
 * Implements:
 * 1. Executive Dashboard (#dashboard)
 * 2. IPO Directory (#directory)
 * 3. Evaluation Detail Scorecard (#evaluations/{id})
 * 4. Evidence & Provenance Explorer (#evidence/{id})
 *
 * STRICTLY READ-ONLY: all figures, verdicts, and bounds are delivered by UI-1.
 * ZERO client-side scoring calculations; ZERO API keys stored.
 */

import { ApiClient } from './api.js';

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
            <span class="meta-tag">POLICY: v${this.escape(cfg.active_configuration.version)}</span>
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
                  </td>
                  <td>
                    ${ipo.latest_score !== null ? `<strong>${ipo.latest_score.toFixed(1)}</strong> / 100` : '<span class="badge badge-unknown">UNKNOWN</span>'}
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
            ${penalties.length === 0 ? `
              <p style="color: var(--text-muted); font-size: 0.85rem;">Zero penalties triggered for this evaluation.</p>
            ` : `
              <ul style="list-style: none;">
                ${penalties.map(p => `
                  <li style="padding: 8px 0; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem;">
                    <div>
                      <strong>${this.escape(p.id)}:</strong> ${this.escape(p.label)}
                    </div>
                    <span class="badge badge-avoid">${p.points.toFixed(1)} pts</span>
                  </li>
                `).join('')}
              </ul>
            `}
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

      let distinctionBadge = '';
      if (isQuotePresent) {
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
                ${isExtractedPresent ? `<code>${this.escape(String(item.extracted_value))}</code>` : '<span class="badge badge-unknown">UNKNOWN</span>'}
                ${item.unit ? `<span class="unit-badge">${this.escape(item.unit)}</span>` : ''}
              </span>
            </div>

            <!-- Verbatim Quotation Block -->
            ${isQuotePresent ? `
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

    let provenanceStatusLabel = 'SOURCE EVIDENCE (Extracted from Filing)';
    if (!isExtractedPresent) {
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
                <span class="badge ${isQuotePresent ? 'badge-source-evidence' : !isExtractedPresent ? 'badge-unknown-evidence' : 'badge-derived-value'}">
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
                ${isExtractedPresent ? `<strong>${this.escape(String(item.extracted_value))}</strong>` : '<span class="badge badge-unknown">UNKNOWN</span>'}
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
              <span class="inspector-label">Verbatim Quoted Citation</span>
              ${isQuotePresent ? `
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
          ` : `
            <div style="font-size: 0.78rem; color: var(--text-muted); background: var(--bg-surface); padding: 8px 12px; border-radius: 4px; border: 1px solid var(--border-color);">
              <span class="badge badge-unknown" style="font-size: 0.7rem;">NO RUN ARTIFACT</span>
              No pre-computed backtest analytics artifact on disk (<code>build/analytics/</code>).
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
  // Lifecycle History (#ipos/{id})
  // --------------------------------------------------------------------------

  async renderIpoDetail(ipoId) {
    this.setViewActive('directory-view');
    const container = document.getElementById('directory-view');
    if (!container) return;

    container.innerHTML = `
      <div class="state-box">
        <div class="spinner"></div>
        <h3>Loading Issuer Lifecycle...</h3>
      </div>
    `;

    try {
      const history = await this.api.getIpoHistory(ipoId);

      container.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
          <a href="#directory" class="btn btn-outline btn-sm">&larr; Back to Directory</a>
          <span class="meta-tag">Issuer Progression</span>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">${this.escape(history.company_name)} (<code>${this.escape(history.ipo_id)}</code>)</div>
            <span class="meta-tag">${history.history.length} Lifecycle Evaluations</span>
          </div>

          ${history.delta ? `
            <div class="card" style="background: var(--bg-subtle); margin-bottom: 16px;">
              <div class="card-title" style="font-size: 0.85rem; margin-bottom: 8px;">
                Preliminary &rarr; Final Progression Delta
              </div>
              <div style="display: flex; gap: 24px; font-size: 0.85rem;">
                <div>Preliminary Score: <strong>${history.delta.preliminary_score !== null ? history.delta.preliminary_score.toFixed(1) : '—'}</strong></div>
                <div>Final Score: <strong>${history.delta.final_score !== null ? history.delta.final_score.toFixed(1) : '—'}</strong></div>
                <div>Score Delta: <strong>${history.delta.score_delta !== null ? (history.delta.score_delta >= 0 ? `+${history.delta.score_delta.toFixed(1)}` : history.delta.score_delta.toFixed(1)) : '0.0'}</strong></div>
                <div>Verdict Shift: <strong>${history.delta.verdict_changed ? 'YES' : 'NO (Preserved)'}</strong></div>
              </div>
            </div>
          ` : ''}

          <div class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Evaluation ID</th>
                  <th>Mode / Stage</th>
                  <th>Timestamp</th>
                  <th>Final Score</th>
                  <th>Verdict</th>
                  <th>Confidence</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                ${history.history.map(e => `
                  <tr>
                    <td><code>${this.escape(e.evaluation_id)}</code></td>
                    <td><span class="meta-tag">${this.escape(e.evaluation_mode)}</span></td>
                    <td>${this.formatDate(e.evaluation_timestamp)}</td>
                    <td><strong>${e.final_score.toFixed(1)}</strong></td>
                    <td>${this.renderVerdictBadge(e.verdict)}</td>
                    <td>${this.escape(e.confidence)} (${e.completeness_pct !== null ? e.completeness_pct.toFixed(0) : '—'}%)</td>
                    <td>
                      <div style="display: flex; gap: 6px;">
                        <a href="#evaluations/${this.escape(e.evaluation_id)}" class="btn btn-outline btn-sm">
                          Scorecard
                        </a>
                        <a href="#evidence/${this.escape(e.evaluation_id)}" class="btn btn-outline btn-sm">
                          Evidence
                        </a>
                      </div>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    } catch (err) {
      this.renderError(container, 'Failed to load issuer detail', err);
    }
  }

  // --------------------------------------------------------------------------
  // View Helpers & State Formatters
  // --------------------------------------------------------------------------

  setViewActive(viewId) {
    document.querySelectorAll('.view-section').forEach(sec => {
      sec.classList.remove('active');
    });
    const target = document.getElementById(viewId);
    if (target) target.classList.add('active');
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
