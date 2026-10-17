/**
 * IPO Screening Engine — Presentation API Client (UI-2)
 *
 * Encapsulates presentation API calls: GET read models plus explicit filing-ingestion
 * and evaluation-lifecycle POST actions. It never computes scores or stores credentials.
 */

export class ApiError extends Error {
  constructor(status, code, message, details = null) {
    super(message || `API error ${status}: ${code}`);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export class ApiClient {
  /**
   * @param {string} baseUrl - Base URL for API calls. Defaults to window.__API_BASE__ or empty string for relative paths.
   */
  constructor(baseUrl = '') {
    this.baseUrl = baseUrl || (typeof window !== 'undefined' && window.__API_BASE__) || '';
    this.apiPrefix = `${this.baseUrl}/api/v1`;
  }

  /**
   * Internal GET request wrapper with deterministic error parsing.
   * Strictly enforces GET method (no mutation).
   */
  async _get(path, params = {}) {
    const url = new URL(`${this.apiPrefix}${path}`, typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000');
    
    for (const [key, val] of Object.entries(params)) {
      if (val !== null && val !== undefined && val !== '') {
        url.searchParams.set(key, String(val));
      }
    }

    let response;
    try {
      response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });
    } catch (networkErr) {
      throw new ApiError(0, 'NETWORK_ERROR', `Network failure: ${networkErr.message}`);
    }

    if (!response.ok) {
      let errPayload = {};
      try {
        errPayload = await response.json();
      } catch {
        // Non-JSON response
      }
      throw new ApiError(
        response.status,
        errPayload.code || `HTTP_${response.status}`,
        errPayload.message || response.statusText,
        errPayload.details || null
      );
    }

    return await response.json();
  }

  async _sendLifecycleAction(path, payload = null) {
    const url = new URL(`${this.apiPrefix}${path}`, typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000');
    let response;
    try {
      response = await fetch(url.toString(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: payload ? JSON.stringify(payload) : JSON.stringify({}),
      });
    } catch (networkErr) {
      throw new ApiError(0, 'NETWORK_ERROR', `Network failure: ${networkErr.message}`);
    }

    if (!response.ok) {
      let errPayload = {};
      try {
        errPayload = await response.json();
      } catch {
        // Non-JSON response
      }
      const code = errPayload.code || (errPayload.detail && errPayload.detail.code) || `HTTP_${response.status}`;
      const message = errPayload.message || (errPayload.detail && errPayload.detail.message) || (typeof errPayload.detail === 'string' ? errPayload.detail : response.statusText);
      const detailObj = errPayload.detail && typeof errPayload.detail === 'object' ? errPayload.detail : {};
      const details = { ...(detailObj.details || {}), ...(errPayload.details || {}) };
      if (detailObj.missing_fields) details.missing_fields = detailObj.missing_fields;
      if (detailObj.resolution) details.resolution = detailObj.resolution;
      if (detailObj.conflicts) details.conflicts = detailObj.conflicts;
      throw new ApiError(response.status, code, message, Object.keys(details).length ? details : null);
    }

    return await response.json();
  }

  // --------------------------------------------------------------------------
  // System & Governance Endpoints
  // --------------------------------------------------------------------------

  async getHealth() {
    return this._get('/health');
  }

  async getMeta() {
    return this._get('/meta');
  }

  async getConfigurationStatus() {
    return this._get('/configuration/current');
  }

  // --------------------------------------------------------------------------
  // IPO Discovery & Detail Endpoints
  // --------------------------------------------------------------------------

  async listIpos({ page = 1, pageSize = 20, search = null, sectorProfile = null } = {}) {
    return this._get('/ipos', {
      page,
      page_size: pageSize,
      search,
      sector_profile: sectorProfile,
    });
  }

  async getIpo(ipoId) {
    if (!ipoId) throw new ApiError(400, 'INVALID_IDENTIFIER', 'IPO ID must be provided');
    return this._get(`/ipos/${encodeURIComponent(ipoId)}`);
  }

  async getIpoHistory(ipoId, { includeArchived = false } = {}) {
    if (!ipoId) throw new ApiError(400, 'INVALID_IDENTIFIER', 'IPO ID must be provided');
    const params = includeArchived ? { include_archived: true } : {};
    return this._get(`/ipos/${encodeURIComponent(ipoId)}/history`, params);
  }

  // --------------------------------------------------------------------------
  // Lifecycle Governance Endpoints
  // --------------------------------------------------------------------------

  async archiveEvaluation(evaluationId, { reason = null, actor = null } = {}) {
    if (!evaluationId) throw new ApiError(400, 'INVALID_IDENTIFIER', 'Evaluation ID must be provided');
    return this._sendLifecycleAction(`/evaluations/${encodeURIComponent(evaluationId)}/archive`, {
      reason,
      actor,
    });
  }

  async unarchiveEvaluation(evaluationId, { reason = null, actor = null } = {}) {
    if (!evaluationId) throw new ApiError(400, 'INVALID_IDENTIFIER', 'Evaluation ID must be provided');
    return this._sendLifecycleAction(`/evaluations/${encodeURIComponent(evaluationId)}/unarchive`, {
      reason,
      actor,
    });
  }

  async makeEvaluationActive(evaluationId, { reason = null, actor = null } = {}) {
    if (!evaluationId) throw new ApiError(400, 'INVALID_IDENTIFIER', 'Evaluation ID must be provided');
    return this._sendLifecycleAction(`/evaluations/${encodeURIComponent(evaluationId)}/make-active`, {
      reason,
      actor,
    });
  }

  // --------------------------------------------------------------------------
  // Evaluation Discovery & Detail Endpoints
  // --------------------------------------------------------------------------

  async listEvaluations({
    page = 1,
    pageSize = 20,
    ipoId = null,
    mode = null,
    verdict = null,
    confidence = null,
    engineVersion = null,
    configVersion = null,
  } = {}) {
    return this._get('/evaluations', {
      page,
      page_size: pageSize,
      ipo_id: ipoId,
      mode,
      verdict,
      confidence,
      engine_version: engineVersion,
      config_version: configVersion,
    });
  }

  async getEvaluation(evaluationId) {
    if (!evaluationId) throw new ApiError(400, 'INVALID_IDENTIFIER', 'Evaluation ID must be provided');
    return this._get(`/evaluations/${encodeURIComponent(evaluationId)}`);
  }

  // --------------------------------------------------------------------------
  // Future Surface Read Handlers (Read-Only)
  // --------------------------------------------------------------------------

  async getEvaluationEvidence(evaluationId) {
    if (!evaluationId) throw new ApiError(400, 'INVALID_IDENTIFIER', 'Evaluation ID must be provided');
    return this._get(`/evaluations/${encodeURIComponent(evaluationId)}/evidence`);
  }

  async getEvidence(evidenceId) {
    if (!evidenceId) throw new ApiError(400, 'INVALID_IDENTIFIER', 'Evidence ID must be provided');
    return this._get(`/evidence/${encodeURIComponent(evidenceId)}`);
  }

  async getPostListing(evaluationId) {
    if (!evaluationId) throw new ApiError(400, 'INVALID_IDENTIFIER', 'Evaluation ID must be provided');
    return this._get(`/evaluations/${encodeURIComponent(evaluationId)}/post-listing`);
  }

  async getPerformance(evaluationId) {
    if (!evaluationId) throw new ApiError(400, 'INVALID_IDENTIFIER', 'Evaluation ID must be provided');
    return this._get(`/evaluations/${encodeURIComponent(evaluationId)}/performance`);
  }

  async getBacktestAnalytics() {
    return this._get('/backtest/analytics');
  }

  async getBacktestDatasets() {
    return this._get('/backtest/datasets');
  }

  async getCalibrationProposals() {
    return this._get('/calibration/proposals');
  }

  async getCalibrationProposal(proposalId) {
    if (!proposalId) throw new ApiError(400, 'INVALID_IDENTIFIER', 'Proposal ID must be provided');
    return this._get(`/calibration/proposals/${encodeURIComponent(proposalId)}`);
  }

  /**
   * Ingest and evaluate an IPO filing document (PDF).
   * Orchestrates server-side document extraction, canonical building,
   * deterministic evaluation, and immutable persistence.
   *
   * @param {File|Blob} file - PDF filing to upload
   * @param {Object} [options] - Ingestion options
   * @param {string} [options.mode] - 'final' or 'preliminary' (default: 'final')
   * @returns {Promise<Object>} Ingestion response containing evaluation_id, score, verdict, etc.
   */
  async ingestDocument(file, options = {}) {
    if (!file) {
      throw new ApiError(400, 'INVALID_FILE', 'A filing document file is required.');
    }

    const formData = new FormData();
    let blobFile = file;
    if (typeof Blob !== 'undefined' && !(file instanceof Blob)) {
      blobFile = new Blob([file], { type: 'application/pdf' });
    }
    formData.append('file', blobFile, file.name || 'filing.pdf');

    if (options.mode) {
      formData.append('mode', options.mode);
    }

    const url = new URL(
      `${this.apiPrefix}/ingest/document`,
      typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000'
    );

    let response;
    try {
      response = await fetch(url.toString(), {
        method: 'POST',
        headers: {
          Accept: 'application/json',
        },
        body: formData,
      });
    } catch (networkErr) {
      throw new ApiError(0, 'NETWORK_ERROR', `Network failure during upload: ${networkErr.message}`);
    }

    if (!response.ok) {
      let errPayload;
      try {
        errPayload = await response.json();
      } catch {
        throw new ApiError(response.status, 'HTTP_ERROR', `Server error (${response.status})`);
      }
      const code = errPayload.code || (errPayload.detail && errPayload.detail.code) || 'INGESTION_ERROR';
      const message =
        errPayload.message ||
        (errPayload.detail && errPayload.detail.message) ||
        (typeof errPayload.detail === 'string' ? errPayload.detail : 'Filing ingestion failed');
      // FastAPI nests the payload under `detail`; preserve the
      // AWAITING_ISSUE_TERMS diagnostics (missing fields + per-provider
      // resolution reports) so the UI can show WHY terms are unresolved
      // instead of only the generic message.
      const detailObj = errPayload.detail && typeof errPayload.detail === 'object' ? errPayload.detail : {};
      const details = { ...(detailObj.details || {}), ...(errPayload.details || {}) };
      if (detailObj.missing_fields) details.missing_fields = detailObj.missing_fields;
      if (detailObj.resolution) details.resolution = detailObj.resolution;
      if (detailObj.conflicts) details.conflicts = detailObj.conflicts;
      throw new ApiError(response.status, code, message, Object.keys(details).length ? details : null);
    }

    return await response.json();
  }

  /**
   * Step 5: ingest with bounded manual issue-term entry.
   * Manual values (price_band_low / price_band_high / lot_size) are
   * provenance-labelled MANUAL_ENTRY server-side and never verified.
   */
  async ingestManualTerms(file, options = {}) {
    if (!file) {
      throw new ApiError(400, 'INVALID_FILE', 'A filing document file is required.');
    }
    const formData = new FormData();
    let blobFile = file;
    if (typeof Blob !== 'undefined' && !(file instanceof Blob)) {
      blobFile = new Blob([file], { type: 'application/pdf' });
    }
    formData.append('file', blobFile, file.name || 'filing.pdf');
    if (options.mode) formData.append('mode', options.mode);
    const terms = options.terms || {};
    if (terms.price_band_low !== undefined && terms.price_band_low !== null && terms.price_band_low !== '') formData.append('price_band_low', String(terms.price_band_low));
    if (terms.price_band_high !== undefined && terms.price_band_high !== null && terms.price_band_high !== '') formData.append('price_band_high', String(terms.price_band_high));
    if (terms.lot_size !== undefined && terms.lot_size !== null && terms.lot_size !== '') formData.append('lot_size', String(terms.lot_size));
    if (options.explanation) formData.append('explanation', options.explanation);
    if (options.confirmConflicts) formData.append('confirm_conflicts', 'true');

    const url = new URL(
      `${this.apiPrefix}/ingest/manual-terms`,
      typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000'
    );
    let response;
    try {
      response = await fetch(url.toString(), { method: 'POST', headers: { Accept: 'application/json' }, body: formData });
    } catch (networkErr) {
      throw new ApiError(0, 'NETWORK_ERROR', `Network failure during upload: ${networkErr.message}`);
    }
    if (!response.ok) {
      let errPayload;
      try {
        errPayload = await response.json();
      } catch {
        throw new ApiError(response.status, 'HTTP_ERROR', `Server error (${response.status})`);
      }
      const code = errPayload.code || (errPayload.detail && errPayload.detail.code) || 'INGESTION_ERROR';
      const message = errPayload.message || (errPayload.detail && errPayload.detail.message) || (typeof errPayload.detail === 'string' ? errPayload.detail : 'Manual-terms ingestion failed');
      const detailObj = errPayload.detail && typeof errPayload.detail === 'object' ? errPayload.detail : {};
      const details = { ...(detailObj.details || {}), ...(errPayload.details || {}) };
      if (detailObj.missing_fields) details.missing_fields = detailObj.missing_fields;
      if (detailObj.resolution) details.resolution = detailObj.resolution;
      if (detailObj.conflicts) details.conflicts = detailObj.conflicts;
      throw new ApiError(response.status, code, message, Object.keys(details).length ? details : null);
    }
    return response.json();
  }
}
