/**
 * IPO Screening Engine — UI-2 Presentation Application
 *
 * Implements Executive Dashboard, IPO Directory, and Evaluation Scorecard.
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
  }

  init() {
    window.addEventListener('hashchange', () => this.handleRouting());
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
          CORE: ${this.escape(cfg.frozen_core_status)}
        </span>
      `;
    } catch {
      bannerEl.innerHTML = `<span class="badge badge-unknown">Gov Status Unavailable</span>`;
    }
  }

  // --------------------------------------------------------------------------
  // 1. Executive Dashboard View
  // --------------------------------------------------------------------------

  async renderDashboard() {
    this.setViewActive('dashboard-view');
    const container = document.getElementById('dashboard-view');
    if (!container) return;

    container.innerHTML = `
      <div class="state-box">
        <div class="spinner"></div>
        <h3>Loading Executive Dashboard...</h3>
        <p>Fetching authoritative evaluations and portfolio metrics from engine store.</p>
      </div>
    `;

    try {
      const [iposResp, evalsResp, configStatus] = await Promise.all([
        this.api.listIpos({ page: 1, pageSize: 50 }),
        this.api.listEvaluations({ page: 1, pageSize: 50 }),
        this.api.getConfigurationStatus(),
      ]);

      const ipoCount = iposResp.total;
      const evalCount = evalsResp.total;

      // Group verdict counts from authoritative evaluation list
      const verdictCounts = { APPLY: 0, CONSIDER: 0, AVOID: 0, INSUFFICIENT_DATA: 0 };
      evalsResp.items.forEach(e => {
        if (verdictCounts[e.verdict] !== undefined) {
          verdictCounts[e.verdict]++;
        }
      });

      container.innerHTML = `
        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-label">IPO Issuers</div>
            <div class="kpi-value">${ipoCount}</div>
            <div class="kpi-subtext">Evaluated in repository</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Total Evaluations</div>
            <div class="kpi-value">${evalCount}</div>
            <div class="kpi-subtext">Preliminary & Final runs</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Active Config</div>
            <div class="kpi-value" style="font-size: 1.4rem;">${this.escape(configStatus.active_configuration.version)}</div>
            <div class="kpi-subtext">Executable Policy (Active)</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Candidate v1.6</div>
            <div class="kpi-value" style="font-size: 1.4rem; color: var(--text-muted);">${this.escape(configStatus.candidate_configuration.status)}</div>
            <div class="kpi-subtext">Gated, Promotion Inactive</div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">Verdict Distribution</div>
            <span class="meta-tag">Authoritative Engine Allocations</span>
          </div>
          <div style="display: flex; gap: 16px; flex-wrap: wrap;">
            <div class="badge badge-apply" style="padding: 8px 14px; font-size: 0.9rem;">
              APPLY: ${verdictCounts.APPLY}
            </div>
            <div class="badge badge-consider" style="padding: 8px 14px; font-size: 0.9rem;">
              CONSIDER: ${verdictCounts.CONSIDER}
            </div>
            <div class="badge badge-avoid" style="padding: 8px 14px; font-size: 0.9rem;">
              AVOID: ${verdictCounts.AVOID}
            </div>
            <div class="badge badge-insufficient" style="padding: 8px 14px; font-size: 0.9rem;">
              INSUFFICIENT DATA: ${verdictCounts.INSUFFICIENT_DATA}
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">Recent Evaluations</div>
            <a href="#directory" class="btn btn-outline btn-sm">View All in Directory &rarr;</a>
          </div>
          ${this.renderEvaluationsTableHtml(evalsResp.items.slice(0, 10))}
        </div>
      `;
    } catch (err) {
      this.renderError(container, 'Failed to load executive dashboard', err);
    }
  }

  // --------------------------------------------------------------------------
  // 2. IPO Directory View
  // --------------------------------------------------------------------------

  async renderDirectory() {
    this.setViewActive('directory-view');
    const container = document.getElementById('directory-view');
    if (!container) return;

    container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <div class="card-title">IPO Issuer Directory</div>
          <div class="filter-bar" style="margin: 0;">
            <input 
              type="text" 
              id="dir-search" 
              class="search-input" 
              placeholder="Search by issuer name or IPO ID..." 
              value="${this.escape(this.directoryState.search)}"
            />
          </div>
        </div>
        <div id="dir-table-container">
          <div class="state-box">
            <div class="spinner"></div>
            <p>Loading IPO directory...</p>
          </div>
        </div>
        <div id="dir-pagination" class="filter-bar" style="margin-top: 16px;"></div>
      </div>
    `;

    // Hook search event
    const searchInput = document.getElementById('dir-search');
    if (searchInput) {
      let debounceTimeout;
      searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => {
          this.directoryState.search = e.target.value.trim();
          this.directoryState.page = 1;
          this.fetchAndRenderDirectoryTable();
        }, 300);
      });
    }

    await this.fetchAndRenderDirectoryTable();
  }

  async fetchAndRenderDirectoryTable() {
    const tableContainer = document.getElementById('dir-table-container');
    const pagContainer = document.getElementById('dir-pagination');
    if (!tableContainer) return;

    try {
      const resp = await this.api.listIpos({
        page: this.directoryState.page,
        pageSize: this.directoryState.pageSize,
        search: this.directoryState.search || null,
      });

      if (resp.items.length === 0) {
        tableContainer.innerHTML = `
          <div class="state-box">
            <h3>No IPO Issuers Found</h3>
            <p>${this.directoryState.search ? `No issuers matched "${this.escape(this.directoryState.search)}".` : 'The evaluation store is empty.'}</p>
          </div>
        `;
        if (pagContainer) pagContainer.innerHTML = '';
        return;
      }

      tableContainer.innerHTML = `
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>IPO Identifier</th>
                <th>Company Name</th>
                <th>Sector Profile</th>
                <th>Evaluations</th>
                <th>Latest Mode</th>
                <th>Latest Score</th>
                <th>Latest Verdict</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              ${resp.items.map(ipo => `
                <tr>
                  <td><code>${this.escape(ipo.ipo_id)}</code></td>
                  <td><strong>${this.escape(ipo.company_name)}</strong></td>
                  <td><span class="meta-tag">${this.escape(ipo.sector_profile || 'standard')}</span></td>
                  <td>${ipo.evaluation_count}</td>
                  <td><span class="meta-tag">${this.escape(ipo.latest_evaluation_mode || '—')}</span></td>
                  <td><strong>${ipo.latest_score !== null ? ipo.latest_score.toFixed(1) : '<span class="badge badge-unknown">UNKNOWN</span>'}</strong></td>
                  <td>${this.renderVerdictBadge(ipo.latest_verdict)}</td>
                  <td>
                    ${ipo.latest_evaluation_id ? `
                      <a href="#evaluations/${this.escape(ipo.latest_evaluation_id)}" class="btn btn-outline btn-sm">
                        View Scorecard
                      </a>
                    ` : `
                      <a href="#ipos/${this.escape(ipo.ipo_id)}" class="btn btn-outline btn-sm">
                        Inspect
                      </a>
                    `}
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;

      // Pagination controls
      if (pagContainer) {
        pagContainer.innerHTML = `
          <div class="kpi-subtext">
            Showing Page <strong>${resp.page}</strong> of <strong>${resp.pages}</strong> (${resp.total} total issuers)
          </div>
          <div class="pagination-controls">
            <button id="btn-prev-page" class="btn btn-outline btn-sm" ${resp.page <= 1 ? 'disabled' : ''}>
              &larr; Previous
            </button>
            <button id="btn-next-page" class="btn btn-outline btn-sm" ${resp.page >= resp.pages ? 'disabled' : ''}>
              Next &rarr;
            </button>
          </div>
        `;

        document.getElementById('btn-prev-page')?.addEventListener('click', () => {
          if (this.directoryState.page > 1) {
            this.directoryState.page--;
            this.fetchAndRenderDirectoryTable();
          }
        });

        document.getElementById('btn-next-page')?.addEventListener('click', () => {
          if (this.directoryState.page < resp.pages) {
            this.directoryState.page++;
            this.fetchAndRenderDirectoryTable();
          }
        });
      }
    } catch (err) {
      this.renderError(tableContainer, 'Error loading IPO directory', err);
    }
  }

  // --------------------------------------------------------------------------
  // 3. IPO Evaluation Scorecard View
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
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
          <a href="#directory" class="btn btn-outline btn-sm">&larr; Back to Directory</a>
          <div style="display: flex; gap: 8px;">
            <a href="#ipos/${this.escape(evaluation.ipo_id)}" class="btn btn-outline btn-sm">Lifecycle History</a>
            <span class="meta-tag">UI-3 Evidence (Planned)</span>
            <span class="meta-tag">UI-4 Post-Listing (Planned)</span>
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
                VERDICT UNCERTAIN (WIDE RANGE)
              </div>
            ` : ''}
          </div>
        </div>

        <!-- 3. Knockouts Inspection Gate (K1-K6) -->
        <div class="card">
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
                        <th>Reason</th>
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
  // 4. IPO Detail / Historical Progression View
  // --------------------------------------------------------------------------

  async renderIpoDetail(ipoId) {
    this.setViewActive('scorecard-view');
    const container = document.getElementById('scorecard-view');
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
                      <a href="#evaluations/${this.escape(e.evaluation_id)}" class="btn btn-outline btn-sm">
                        View Scorecard
                      </a>
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
        <table class="data-table">
          <thead>
            <tr>
              <th>Evaluation ID</th>
              <th>Issuer</th>
              <th>Mode</th>
              <th>Final Score</th>
              <th>Verdict</th>
              <th>Confidence</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            ${evaluations.map(e => `
              <tr>
                <td><code>${this.escape(e.evaluation_id.slice(0, 16))}...</code></td>
                <td><strong>${this.escape(e.company_name)}</strong></td>
                <td><span class="meta-tag">${this.escape(e.evaluation_mode)}</span></td>
                <td><strong>${e.final_score.toFixed(1)}</strong></td>
                <td>${this.renderVerdictBadge(e.verdict)}</td>
                <td>${this.escape(e.confidence)}</td>
                <td>
                  <a href="#evaluations/${this.escape(e.evaluation_id)}" class="btn btn-outline btn-sm">
                    Scorecard &rarr;
                  </a>
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
          <p>The path <code>#${this.escape(path)}</code> is not a recognized UI-2 route.</p>
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
