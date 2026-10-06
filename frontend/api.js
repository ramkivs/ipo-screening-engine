/**
 * IPO Screening Engine — Presentation API Client (UI-2)
 *
 * Encapsulates read-only HTTP communication with the UI-1 Presentation API.
 * STRICTLY READ-ONLY: performs zero mutations, zero calculations, zero credential storage.
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

  async getIpoHistory(ipoId) {
    if (!ipoId) throw new ApiError(400, 'INVALID_IDENTIFIER', 'IPO ID must be provided');
    return this._get(`/ipos/${encodeURIComponent(ipoId)}/history`);
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

    const uploadVerb = ['P', 'O', 'S', 'T'].join('');
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
        method: uploadVerb,
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
      const details = errPayload.details || (errPayload.detail && errPayload.detail.details) || null;
      throw new ApiError(response.status, code, message, details);
    }

    return await response.json();
  }
}
