from flask import request
from itertools import chain, product
import mock
import pytest

from dmutils.request_id import init_app as request_id_init_app


_GENERATED_TRACE_VALUE = "d15ea5e5deadbeefbaadf00dabadcafe"


_trace_id_related_params = (
    (
        # extra_config
        {
            "DM_REQUEST_ID_HEADER": "DM-REQUEST-ID",
            "DM_DOWNSTREAM_REQUEST_ID_HEADER": "DOWNSTREAM-REQUEST-ID",
        },
        # extra_req_headers
        (
            ("DM-REQUEST-ID", "from-header",),
            ("DOWNSTREAM-REQUEST-ID", "from-downstream",),
        ),
        # expected_trace_id
        "from-header",
        # expect_uuid_call
        False,
        # expected_onwards_req_headers
        {
            "DM-REQUEST-ID": "from-header",
            "DOWNSTREAM-REQUEST-ID": "from-header",
        },
        # expected_resp_headers
        {
            "DM-REQUEST-ID": "from-header",
            "DOWNSTREAM-REQUEST-ID": "from-header",
        },
        # expected_dm_request_id_header_final_value
        "DM-REQUEST-ID",
    ),
    (
        # extra_config
        {
            "DM_REQUEST_ID_HEADER": "DM-REQUEST-ID",
            "DM_DOWNSTREAM_REQUEST_ID_HEADER": "DOWNSTREAM-REQUEST-ID",
        },
        # extra_req_headers
        (
            ("DOWNSTREAM-REQUEST-ID", "from-downstream",),
        ),
        # expected_trace_id
        "from-downstream",
        False,
        # expected_onwards_req_headers
        {
            "DM-REQUEST-ID": "from-downstream",
            "DOWNSTREAM-REQUEST-ID": "from-downstream",
        },
        # expected_resp_headers
        {
            "DM-REQUEST-ID": "from-downstream",
            "DOWNSTREAM-REQUEST-ID": "from-downstream",
        },
        # expected_dm_request_id_header_final_value
        "DM-REQUEST-ID",
    ),
    (
        # extra_config
        {
            "DM_REQUEST_ID_HEADER": "DM-REQUEST-ID",
            "DM_DOWNSTREAM_REQUEST_ID_HEADER": "",
        },
        # extra_req_headers
        (),
        # expected_trace_id
        _GENERATED_TRACE_VALUE,
        # expect_uuid_call
        True,
        # expected_onwards_req_headers
        {
            "DM-REQUEST-ID": _GENERATED_TRACE_VALUE,
            "X-B3-TraceId": _GENERATED_TRACE_VALUE,
        },
        # expected_resp_headers
        {
            "DM-REQUEST-ID": _GENERATED_TRACE_VALUE,
            "X-B3-TraceId": _GENERATED_TRACE_VALUE,
        },
        # expected_dm_request_id_header_final_value
        "DM-REQUEST-ID",
    ),
    (
        # extra_config
        {
            "DM_REQUEST_ID_HEADER": "DM-REQUEST-ID",
            "DM_DOWNSTREAM_REQUEST_ID_HEADER": "DOWNSTREAM-REQUEST-ID",
        },
        # extra_req_headers
        (),
        # expected_trace_id
        _GENERATED_TRACE_VALUE,
        # expect_uuid_call
        True,
        # expected_onwards_req_headers
        {
            "DM-REQUEST-ID": _GENERATED_TRACE_VALUE,
            "DOWNSTREAM-REQUEST-ID": _GENERATED_TRACE_VALUE,
        },
        # expected_resp_headers
        {
            "DM-REQUEST-ID": _GENERATED_TRACE_VALUE,
            "DOWNSTREAM-REQUEST-ID": _GENERATED_TRACE_VALUE,
        },
        # expected_dm_request_id_header_final_value
        "DM-REQUEST-ID",
    ),
    (
        # extra_config
        {
            # not setting DM_REQUEST_ID_HEADER should cause it to fall back to the default, DM-Request-ID
            "DM_DOWNSTREAM_REQUEST_ID_HEADER": "DOWNSTREAM-REQUEST-ID",
        },
        # extra_req_headers
        (
            ("X-B3-TraceId", "H. M. S. Belleisle",),  # should be ignored as default header name has been overwritten
        ),
        # expected_trace_id
        _GENERATED_TRACE_VALUE,
        # expect_uuid_call
        True,
        # expected_onwards_req_headers
        {
            "DM-Request-ID": _GENERATED_TRACE_VALUE,
            "DOWNSTREAM-REQUEST-ID": _GENERATED_TRACE_VALUE,
        },
        # expected_resp_headers
        {
            "DM-Request-ID": _GENERATED_TRACE_VALUE,
            "DOWNSTREAM-REQUEST-ID": _GENERATED_TRACE_VALUE,
        },
        # expected_dm_request_id_header_final_value
        "DM-Request-ID",
    ),
    (
        # extra_config
        {
            "DM_TRACE_ID_HEADERS": ("x-tommy-caffrey", "y-jacky-caffrey",),
            "DM_REQUEST_ID_HEADER": "DM-REQUEST-ID",
            "DM_DOWNSTREAM_REQUEST_ID_HEADER": "DOWNSTREAM-REQUEST-ID",
        },
        # extra_req_headers
        (
            # these should both be ignored because of the presence of the DM_TRACE_ID_HEADERS setting
            ("DM-REQUEST-ID", "from-header",),
            ("DOWNSTREAM-REQUEST-ID", "from-downstream",),
        ),
        # expected_trace_id
        _GENERATED_TRACE_VALUE,
        # expect_uuid_call
        True,
        # expected_onwards_req_headers
        {
            "x-tommy-caffrey": _GENERATED_TRACE_VALUE,
            "y-jacky-caffrey": _GENERATED_TRACE_VALUE,
        },
        # expected_resp_headers
        {
            "x-tommy-caffrey": _GENERATED_TRACE_VALUE,
            "y-jacky-caffrey": _GENERATED_TRACE_VALUE,
        },
        # expected_dm_request_id_header_final_value
        "x-tommy-caffrey",
    ),
    (
        # extra_config
        {
            "DM_TRACE_ID_HEADERS": ("x-tommy-caffrey", "y-jacky-caffrey",),
        },
        # extra_req_headers
        (
            ("y-jacky-caffrey", "jacky-header-value",),
            ("x-tommy-caffrey", "tommy-header-value",),
        ),
        # expected_trace_id
        "tommy-header-value",
        # expect_uuid_call
        False,
        # expected_onwards_req_headers
        {
            "x-tommy-caffrey": "tommy-header-value",
            "y-jacky-caffrey": "tommy-header-value",
        },
        # expected_resp_headers
        {
            "x-tommy-caffrey": "tommy-header-value",
            "y-jacky-caffrey": "tommy-header-value",
        },
        # expected_dm_request_id_header_final_value
        "x-tommy-caffrey",
    ),
    (
        # extra_config
        {
            "DM_REQUEST_ID_HEADER": "DM-REQUEST-ID",
            # not setting DM_DOWNSTREAM_REQUEST_ID_HEADER should cause it to fall back to the default, X-B3-TraceId
        },
        # extra_req_headers
        (
            ("x-kidneys", "pork",),
            ("x-b3-traceid", "Grilled Mutton",),  # also checking header case-insensitivity here
        ),
        # expected_trace_id
        "Grilled Mutton",
        # expect_uuid_call
        False,
        # expected_onwards_req_headers
        {
            "DM-REQUEST-ID": "Grilled Mutton",
            "X-B3-TraceId": "Grilled Mutton",
        },
        # expected_resp_headers
        {
            "DM-REQUEST-ID": "Grilled Mutton",
            "X-B3-TraceId": "Grilled Mutton",
        },
        # expected_dm_request_id_header_final_value
        "DM-REQUEST-ID",
    ),
)


_span_id_related_params = (
    (
        # extra_config
        {},
        # extra_req_headers
        (
            ("x-b3-spanid", "Steak, kidney, liver, mashed",),  # also checking header case-insensitivity here
        ),
        # expected_span_id
        "Steak, kidney, liver, mashed",
        # expected_onwards_req_headers
        {
            "X-B3-SpanId": "Steak, kidney, liver, mashed",
        },
        # expected_resp_headers
        {
            "X-B3-SpanId": "Steak, kidney, liver, mashed",
        },
    ),
    (
        # extra_config
        {},
        # extra_req_headers
        (),
        # expected_span_id
        None,
        # expected_onwards_req_headers
        {},
        # expected_resp_headers
        {},
    ),
    (
        # extra_config
        {
            "DM_SPAN_ID_HEADERS": ("barrels-and-boxes", "Bloomusalem",),
        },
        # extra_req_headers
        (
            ("bloomusalem", "huge-pork-kidney",),  # also checking header case-insensitivity here
        ),
        # expected_span_id
        "huge-pork-kidney",
        # expected_onwards_req_headers
        {
            "barrels-and-boxes": "huge-pork-kidney",
            "Bloomusalem": "huge-pork-kidney",
        },
        # expected_resp_headers
        {
            "barrels-and-boxes": "huge-pork-kidney",
            "Bloomusalem": "huge-pork-kidney",
        },
    ),
)


_parent_span_id_related_params = (
    (
        # extra_config
        {},
        # extra_req_headers
        (
            ("X-B3-PARENTSPAN", "colossal-edifice",),
            ("X-WANDERING-SOAP", "Flower of the Bath",),
        ),
        # expected_parent_span_id
        "colossal-edifice",
    ),
    (
        # extra_config
        {},
        # extra_req_headers
        (),
        # expected_parent_span_id
        None,
    ),
    (
        # extra_config
        {
            "DM_PARENT_SPAN_ID_HEADERS": ("Potato-Preservative",),
        },
        # extra_req_headers
        (
            ("POTATO-PRESERVATIVE", "Plage and Pestilence",),  # also checking header case-insensitivity here
        ),
        # expected_parent_span_id
        "Plage and Pestilence",
    ),
)


_param_combinations = tuple(
    # to prove that the behaviour of trace_id, span_id and parent_span_id is independent, we use the cartesian product
    # of all sets of parameters to test every possible combination of scenarios we've provided...
    (
        # extra_config
        dict(chain(t_extra_config.items(), s_extra_config.items(), p_extra_config.items(),)),
        # extra_req_headers
        tuple(chain(t_extra_req_headers, s_extra_req_headers, p_extra_req_headers)),
        expected_trace_id,
        expect_uuid_call,
        expected_span_id,
        expected_parent_span_id,
        # expected_onwards_req_headers
        dict(chain(t_expected_onwards_req_headers.items(), s_expected_onwards_req_headers.items(),)),
        # expected_resp_headers
        dict(chain(t_expected_resp_headers.items(), s_expected_resp_headers.items(),)),
        expected_dm_request_id_header_final_value,
    ) for (
        t_extra_config,
        t_extra_req_headers,
        expected_trace_id,
        expect_uuid_call,
        t_expected_onwards_req_headers,
        t_expected_resp_headers,
        expected_dm_request_id_header_final_value,
    ), (
        s_extra_config,
        s_extra_req_headers,
        expected_span_id,
        s_expected_onwards_req_headers,
        s_expected_resp_headers,
    ), (
        p_extra_config,
        p_extra_req_headers,
        expected_parent_span_id,
    ) in product(_trace_id_related_params, _span_id_related_params, _parent_span_id_related_params)
)


@pytest.mark.parametrize(
    (
        "extra_config",
        "extra_req_headers",
        "expected_trace_id",
        "expect_uuid_call",
        "expected_span_id",
        "expected_parent_span_id",
        "expected_onwards_req_headers",
        "expected_resp_headers",
        "expected_dm_request_id_header_final_value",
    ),
    _param_combinations,
)
@mock.patch('dmutils.request_id.uuid.uuid4', autospec=True)
def test_request_header(
    uuid4_mock,
    app,
    extra_config,
    extra_req_headers,
    expected_trace_id,
    expect_uuid_call,
    expected_span_id,
    expected_parent_span_id,
    expected_onwards_req_headers,
    expected_resp_headers,  # unused here
    expected_dm_request_id_header_final_value,
):
    app.config.update(extra_config)
    request_id_init_app(app)

    assert app.config.get("DM_REQUEST_ID_HEADER") == expected_dm_request_id_header_final_value

    uuid4_mock.return_value = mock.Mock(hex=_GENERATED_TRACE_VALUE)

    with app.test_request_context(headers=extra_req_headers):
        assert request.request_id == request.trace_id == expected_trace_id
        assert request.span_id == expected_span_id
        assert request.parent_span_id == expected_parent_span_id
        assert request.get_onwards_request_headers() == expected_onwards_req_headers
        assert app.config.get("DM_REQUEST_ID_HEADER") == expected_dm_request_id_header_final_value
        assert request.get_extra_log_context() == {
            "trace_id": expected_trace_id,
            "span_id": expected_span_id,
            "parent_span_id": expected_parent_span_id,
        }

    assert uuid4_mock.called is expect_uuid_call


@pytest.mark.parametrize(
    (
        "extra_config",
        "extra_req_headers",
        "expected_trace_id",
        "expect_uuid_call",
        "expected_span_id",
        "expected_parent_span_id",
        "expected_onwards_req_headers",
        "expected_resp_headers",
        "expected_dm_request_id_header_final_value",
    ),
    _param_combinations,
)
@mock.patch('dmutils.request_id.uuid.uuid4', autospec=True)
def test_response_headers_regular_response(
    uuid4_mock,
    app,
    extra_config,
    extra_req_headers,
    expected_trace_id,  # unused here
    expect_uuid_call,
    expected_span_id,  # unused here
    expected_parent_span_id,  # unused here
    expected_onwards_req_headers,  # unused here
    expected_resp_headers,
    expected_dm_request_id_header_final_value,  # unused here
):
    app.config.update(extra_config)
    request_id_init_app(app)
    client = app.test_client()

    uuid4_mock.return_value = mock.Mock(hex=_GENERATED_TRACE_VALUE)

    with app.app_context():
        response = client.get('/', headers=extra_req_headers)
        # note using these mechanisms we're not able to test for the *absence* of a header
        assert {k: v for k, v in response.headers.items() if k in expected_onwards_req_headers} == expected_resp_headers

    assert uuid4_mock.called is expect_uuid_call


@pytest.mark.parametrize(
    (
        "extra_config",
        "extra_req_headers",
        "expected_trace_id",
        "expect_uuid_call",
        "expected_span_id",
        "expected_parent_span_id",
        "expected_onwards_req_headers",
        "expected_resp_headers",
        "expected_dm_request_id_header_final_value",
    ),
    _param_combinations,
)
@mock.patch('dmutils.request_id.uuid.uuid4', autospec=True)
def test_response_headers_error_response(
    uuid4_mock,
    app,
    extra_config,
    extra_req_headers,
    expected_trace_id,  # unused here
    expect_uuid_call,
    expected_span_id,  # unused here
    expected_parent_span_id,  # unused here
    expected_onwards_req_headers,  # unused here
    expected_resp_headers,
    expected_dm_request_id_header_final_value,  # unused here
):
    app.config.update(extra_config)
    request_id_init_app(app)
    client = app.test_client()

    uuid4_mock.return_value = mock.Mock(hex=_GENERATED_TRACE_VALUE)

    @app.route('/')
    def error_route():
        raise Exception()

    with app.app_context():
        response = client.get('/', headers=extra_req_headers)
        assert response.status_code == 500
        assert {k: v for k, v in response.headers.items() if k in expected_onwards_req_headers} == expected_resp_headers

    assert uuid4_mock.called is expect_uuid_call
