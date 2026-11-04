"""Focused presentation contract parity and runtime response checks."""
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, RefResolver

from ipo_screening.presentation.api import create_app
from ipo_screening.presentation.service import PresentationConfig, PresentationService

CONTRACT = Path(__file__).with_name("presentation-api-v1.yaml")
METHODS = {"get", "post", "put", "patch", "delete"}


@pytest.fixture(scope="module")
def spec():
    return yaml.safe_load(CONTRACT.read_text())


@pytest.fixture(scope="module")
def runtime():
    return create_app().openapi()


def operations(paths, prefix=""):
    return {(p.removeprefix(prefix), m): op for p, value in paths.items()
            for m, op in value.items() if m in METHODS}


def clean(value):
    """Ignore documentation annotations while comparing JSON Schema constraints."""
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()
                if k not in {"title", "description", "example", "examples"}}
    return value


def test_route_and_parameter_parity(spec, runtime):
    actual = operations(runtime["paths"], "/api/v1")
    documented = operations(spec["paths"])
    assert set(documented) == set(actual)
    for key, op in actual.items():
        doc = documented[key]
        params = {(p["in"], p["name"]): p for p in doc.get("parameters", [])
                  if (p["in"], p["name"]) != ("header", "Origin")}
        expected = {(p["in"], p["name"]): p for p in op.get("parameters", [])}
        assert clean(params) == clean(expected), key
        if key[1] == "post":
            assert any(p["name"] == "Origin" and p["required"] for p in doc["parameters"])
        if "requestBody" in op and not key[0].endswith(("/archive", "/unarchive", "/make-active")):
            assert clean(doc["requestBody"]) == clean(op["requestBody"]), key
        for code in op["responses"]:
            if key == ("/ingestions/start", "post") and code == "200":
                assert "202" in doc["responses"] and "200" not in doc["responses"]
            else:
                assert code in doc["responses"], (key, code)
        assert "400" in doc["responses"]
        if key[1] == "post":
            assert "403" in doc["responses"]


def test_pydantic_schema_parity(spec, runtime):
    documented = spec["components"]["schemas"]
    for name, model in runtime["components"]["schemas"].items():
        assert name in documented, name
        actual, expected = deepcopy(documented[name]), deepcopy(model)
        # API-01 documents the more specific artifact projection; Pydantic uses dicts.
        if name == "BacktestAnalyticsResponse":
            for field in ("vintage_analysis", "holdout_analysis"):
                actual["properties"].pop(field)
                expected["properties"].pop(field)
        assert clean(actual) == clean(expected), name


def test_schema_references_and_openapi_31_nullability(spec):
    assert spec["openapi"] == "3.1.0"
    def walk(value):
        if isinstance(value, dict):
            assert "nullable" not in value
            if "$ref" in value:
                node = spec
                for part in value["$ref"].removeprefix("#/").split("/"):
                    node = node[part.replace("~1", "/").replace("~0", "~")]
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)
    walk(spec)
    for schema in spec["components"]["schemas"].values():
        Draft202012Validator.check_schema(schema)


def validate_response(spec, path, method, response):
    schema = spec["paths"][path][method]["responses"][str(response.status_code)]["content"]["application/json"]["schema"]
    Draft202012Validator(schema, resolver=RefResolver.from_schema(spec)).validate(response.json())


def test_live_validation_errors_and_activity(spec, tmp_path):
    config = PresentationConfig(store_root=str(tmp_path / "evaluations"))
    service = PresentationService(config)
    app = create_app(service)
    client = TestClient(app, base_url="http://localhost")
    origin = {"Origin": "http://localhost"}
    for path in ("/ingest/document", "/ingest/manual-terms", "/ingestions/start"):
        res = client.post("/api/v1" + path, headers=origin)
        assert res.status_code == 422
        validate_response(spec, path, "post", res)
        res = client.post("/api/v1" + path)
        assert res.status_code == 403
        validate_response(spec, path, "post", res)
    res = client.get('/api/v1/ingestions?limit=0')
    assert res.status_code == 422
    validate_response(spec, '/ingestions', 'get', res)
    for path in ('/comparison/{evaluation_id}', '/ingestions/{ingestion_id}', '/ingestions/{ingestion_id}/events'):
        res = client.get('/api/v1' + path.replace('{evaluation_id}', 'missing').replace('{ingestion_id}', 'missing'))
        assert res.status_code == 404
        validate_response(spec, path, 'get', res)
    recorder = service.activity_store.new_recorder(filename='example.pdf', mode='final')
    for path, url in (('/ingestions', '/ingestions'),
                      ('/ingestions/{ingestion_id}', '/ingestions/' + recorder.ingestion_id),
                      ('/ingestions/{ingestion_id}/events', '/ingestions/' + recorder.ingestion_id + '/events?after_sequence=0')):
        res = client.get('/api/v1' + url)
        assert res.status_code == 200
        validate_response(spec, path, 'get', res)
    service.start_ingestion_async = lambda **kwargs: recorder
    res = client.post('/api/v1/ingestions/start', headers=origin, files={'file': ('example.pdf', b'%PDF-1.4')})
    assert res.status_code == 202
    validate_response(spec, '/ingestions/start', 'post', res)


def test_vintage_and_holdout_nulls_and_decimal_values(spec):
    schema = spec['components']['schemas']['BacktestAnalyticsResponse']
    validator = Draft202012Validator(schema, resolver=RefResolver.from_schema(spec))
    base = {'analysis_hash': 'a', 'dataset_hash': 'd', 'leakage_audit_passed': True}
    validator.validate(base | {'vintage_analysis': None, 'holdout_analysis': None})
    vintage = {'vintage_year': 2024, 'n': 2, 'mean_score': 50}
    for horizon in ('1w', '1m', '6m'):
        vintage['mean_return_' + horizon] = .12
        vintage['mean_excess_return_' + horizon] = None
        vintage['positive_rate_' + horizon] = .5
    holdout = {'development_period': '2020-2023', 'holdout_period': '2024', 'n_development': 4,
               'n_holdout': 2, 'dev_mean_score': 50, 'dev_mean_return_1w': .1,
               'holdout_mean_score': None, 'holdout_mean_return_1w': .12, 'status': 'CALCULATED'}
    validator.validate(base | {'vintage_analysis': [vintage], 'holdout_analysis': holdout})
    assert 'Decimal' in spec['components']['schemas']['VintageDiagnostic']['properties']['positive_rate_1w']['description']


def test_declared_success_models_and_explicit_statuses(spec, runtime):
    docs = operations(spec['paths'])
    for key, op in operations(runtime['paths'], '/api/v1').items():
        runtime_schema = op['responses']['200']['content']['application/json']['schema']
        if '$ref' in runtime_schema:
            assert docs[key]['responses']['200']['content']['application/json']['schema'] == runtime_schema, key
    expected = {
        ('/ipos/{ipo_id}', 'get'): {'404'},
        ('/ipos/{ipo_id}/history', 'get'): {'404'},
        ('/evaluations/{evaluation_id}', 'get'): {'404'},
        ('/evaluations/{evaluation_id}/input', 'get'): {'404'},
        ('/comparison/{evaluation_id}', 'get'): {'404'},
        ('/evaluations/{evaluation_id}/evidence', 'get'): {'404'},
        ('/evidence/{evidence_id}', 'get'): {'404'},
        ('/evaluations/{evaluation_id}/post-listing', 'get'): {'404'},
        ('/evaluations/{evaluation_id}/performance', 'get'): {'404'},
        ('/backtest/analytics', 'get'): {'404'},
        ('/calibration/proposals/{proposal_id}', 'get'): {'404'},
        ('/evaluations/{evaluation_id}/archive', 'post'): {'403', '404', '409'},
        ('/evaluations/{evaluation_id}/unarchive', 'post'): {'404', '409'},
        ('/evaluations/{evaluation_id}/make-active', 'post'): {'400', '404', '409'},
        ('/ingest/document', 'post'): {'200', '201', '400', '413', '422', '500'},
        ('/ingest/manual-terms', 'post'): {'200', '201', '400', '409', '413', '422', '500'},
        ('/ingestions/start', 'post'): {'202', '400', '413', '422'},
        ('/ingestions/{ingestion_id}', 'get'): {'404'},
        ('/ingestions/{ingestion_id}/events', 'get'): {'404'},
    }
    for key, statuses in expected.items():
        assert statuses <= set(docs[key]['responses']), key


def test_ingestion_success_and_domain_errors(spec, tmp_path):
    from ipo_screening.presentation.models import IngestionResponse
    from ipo_screening.presentation.service import IngestionAwaitingIssueTermsError, IngestionIssueTermConflictError

    service = PresentationService(PresentationConfig(store_root=str(tmp_path / 'evaluations')))
    client = TestClient(create_app(service), base_url='http://localhost')
    headers = {'Origin': 'http://localhost'}
    result = IngestionResponse(evaluation_id='e', ipo_id='i', company_name='c', evaluation_mode='FINAL',
                               result_hash='h', final_score=20, verdict='v', confidence='Low', evaluation_url='/e')
    for path in ('/ingest/document', '/ingest/manual-terms'):
        for duplicate in (True, False):
            result.is_duplicate = duplicate
            service.ingest_document = lambda **kwargs: result
            res = client.post('/api/v1' + path, headers=headers, files={'file': ('filing.pdf', b'%PDF')})
            assert res.status_code == (200 if duplicate else 201)
            validate_response(spec, path, 'post', res)
        def fail(**kwargs):
            raise IngestionAwaitingIssueTermsError('missing', missing_fields=['lot_size'], resolution={})
        service.ingest_document = fail
        res = client.post('/api/v1' + path, headers=headers, files={'file': ('filing.pdf', b'%PDF')})
        assert res.status_code == 422 and res.json()['code'] == 'AWAITING_ISSUE_TERMS'
        validate_response(spec, path, 'post', res)
    def conflict(**kwargs):
        raise IngestionIssueTermConflictError('conflict', conflicts=[{'field': 'issue.ofs'}])
    service.ingest_document = conflict
    res = client.post('/api/v1/ingest/manual-terms', headers=headers, files={'file': ('filing.pdf', b'%PDF')})
    assert res.status_code == 409
    validate_response(spec, '/ingest/manual-terms', 'post', res)
