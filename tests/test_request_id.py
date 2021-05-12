from flask import request
from itertools import chain, product
import pytest
from unittest import mock

from dmtestutils.mocking import assert_args_and_return
from dmtestutils.comparisons import AnySupersetOf

from dmutils.request_id import (
    init_app as request_id_init_app,
    RequestIdRequestMixin,
)


_GENERATED_TRACE_VALUE = 0xd15ea5e5deadbeefbaadf00dabadcafe
_GENERATED_SPAN_VALUE = 0xc001d00dbeefcace

_GENERATED_TRACE_HEX = hex(_GENERATED_TRACE_VALUE)[2:]
_GENERATED_SPAN_HEX = hex(_GENERATED_SPAN_VALUE)[2:]


def _abbreviate_id(value):
    if value == _GENERATED_TRACE_VALUE:
        return "GEN_TRACE_VAL"
    elif value == _GENERATED_SPAN_VALUE:
        return "GEN_SPAN_VAL"
    elif value == ():
        return "EMPTYTUP"
    elif value == {}:
        return "EMPTYDCT"


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
        # expect_trace_random_call
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
        _GENERATED_TRACE_HEX,
        # expect_trace_random_call
        True,
        # expected_onwards_req_headers
        {
            "DM-REQUEST-ID": _GENERATED_TRACE_HEX,
            "X-B3-TraceId": _GENERATED_TRACE_HEX,
        },
        # expected_resp_headers
        {
            "DM-REQUEST-ID": _GENERATED_TRACE_HEX,
            "X-B3-TraceId": _GENERATED_TRACE_HEX,
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
        _GENERATED_TRACE_HEX,
        # expect_trace_random_call
        True,
        # expected_onwards_req_headers
        {
            "DM-REQUEST-ID": _GENERATED_TRACE_HEX,
            "DOWNSTREAM-REQUEST-ID": _GENERATED_TRACE_HEX,
        },
        # expected_resp_headers
        {
            "DM-REQUEST-ID": _GENERATED_TRACE_HEX,
            "DOWNSTREAM-REQUEST-ID": _GENERATED_TRACE_HEX,
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
        _GENERATED_TRACE_HEX,
        # expect_trace_random_call
        True,
        # expected_onwards_req_headers
        {
            "DM-Request-ID": _GENERATED_TRACE_HEX,
            "DOWNSTREAM-REQUEST-ID": _GENERATED_TRACE_HEX,
        },
        # expected_resp_headers
        {
            "DM-Request-ID": _GENERATED_TRACE_HEX,
            "DOWNSTREAM-REQUEST-ID": _GENERATED_TRACE_HEX,
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
        _GENERATED_TRACE_HEX,
        # expect_trace_random_call
        True,
        # expected_onwards_req_headers
        {
            "x-tommy-caffrey": _GENERATED_TRACE_HEX,
            "y-jacky-caffrey": _GENERATED_TRACE_HEX,
        },
        # expected_resp_headers
        {
            "x-tommy-caffrey": _GENERATED_TRACE_HEX,
            "y-jacky-caffrey": _GENERATED_TRACE_HEX,
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
        # expect_trace_random_call
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
        # expect_trace_random_call
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
            ("x-b3-parentspanid", "Muttoning",),
        ),
        # expected_span_id
        "Steak, kidney, liver, mashed",
        # expected_parent_span_id
        "Muttoning",
        # expected_onwards_req_headers
        {
            "X-B3-SpanId": _GENERATED_SPAN_HEX,
            "X-B3-ParentSpanId": "Steak, kidney, liver, mashed",
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
        # expected_parent_span_id
        None,
        # expected_onwards_req_headers
        {
            "X-B3-SpanId": _GENERATED_SPAN_HEX,
        },
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
        # expected_parent_span_id
        None,
        # expected_onwards_req_headers
        {
            "X-B3-ParentSpanId": "huge-pork-kidney",
            "barrels-and-boxes": _GENERATED_SPAN_HEX,
            "Bloomusalem": _GENERATED_SPAN_HEX,
        },
        # expected_resp_headers
        {
            "barrels-and-boxes": "huge-pork-kidney",
            "Bloomusalem": "huge-pork-kidney",
        },
    ),
    (
        # extra_config
        {
            "DM_PARENT_SPAN_ID_HEADERS": ("Potato-Preservative", "X-WANDERING-SOAP",),
        },
        # extra_req_headers
        (
            ("POTATO-PRESERVATIVE", "Plage and Pestilence",),  # also checking header case-insensitivity here
            ("X-WANDERING-SOAP", "Flower of the Bath",),  # should be ignored in favour of POTATO-PRESERVATIVE's value
            ("X-B3-SpanId", "colossal-edifice",),
        ),
        # expected_span_id
        "colossal-edifice",
        # expected_parent_span_id
        "Plage and Pestilence",
        # expected_onwards_req_headers
        {
            "Potato-Preservative": "colossal-edifice",
            "X-WANDERING-SOAP": "colossal-edifice",
            "X-B3-SpanId": _GENERATED_SPAN_HEX,
        },
        # expected_resp_headers
        {
            "X-B3-SpanId": "colossal-edifice",
        },
    ),
)


_debug_sampling_related_params = (
    (
        # extra_config
        {},
        # extra_req_headers
        (),
        # expected_is_sampled
        None,
        # expected_debug_flag
        None,
        # expected_onwards_req_headers
        {},
    ),
    (
        # extra_config
        {},
        # extra_req_headers
        (
            ("X-B3-SAMPLED", "1",),  # also checking header case-insensitivity here
        ),
        # expected_is_sampled
        True,
        # expected_debug_flag
        None,
        # expected_onwards_req_headers
        {
            "X-B3-Sampled": "1",
        },
    ),
    (
        # extra_config
        {
            "DM_IS_SAMPLED_HEADERS": ("Brown-Bread", "GOLDEN-SYRUP",),
        },
        # extra_req_headers
        (
            ("X-B3-Sampled", "1"),  # should be ignored because of DM_SAMPLE_DECISION_HEADERS setting
            ("golden-syrup", "yes",),  # also checking header case-insensitivity here
        ),
        # expected_is_sampled
        False,
        # expected_debug_flag
        None,
        # expected_onwards_req_headers
        {
            "Brown-Bread": "0",
            "GOLDEN-SYRUP": "0",
        },
    ),
    (
        # extra_config
        {},
        # extra_req_headers
        (
            ("X-B3-Flags", "1",),
        ),
        # expected_is_sampled
        True,
        # expected_debug_flag
        True,
        # expected_onwards_req_headers
        {
            "X-B3-Flags": "1",
        },
    ),
    (
        # extra_config
        {
            "DM_IS_SAMPLED_HEADERS": ("Castor", "Oil",),
            "DM_DEBUG_FLAG_HEADERS": ("Spades", "Buckets",),
        },
        # extra_req_headers
        (
            ("Castor", "0",),
            ("Spades", "1",),
            ("Buckets", "0",),
        ),
        # expected_is_sampled
        True,
        # expected_debug_flag
        True,
        # expected_onwards_req_headers
        {
            "Spades": "1",
            "Buckets": "1",
        },
    ),
)


_param_combinations = tuple(
    # to prove that the behaviour of trace_id, span_id and parent_span_id is independent, we use the cartesian product
    # of all sets of parameters to test every possible combination of scenarios we've provided...
    (
        # extra_config
        dict(chain(t_extra_config.items(), s_extra_config.items(), d_extra_config.items(),)),
        # extra_req_headers
        tuple(chain(t_extra_req_headers, s_extra_req_headers, d_extra_req_headers)),
        expected_trace_id,
        expect_trace_random_call,
        expected_span_id,
        expected_parent_span_id,
        expected_is_sampled,
        expected_debug_flag,
        # expected_onwards_req_headers
        dict(chain(
            t_expected_onwards_req_headers.items(),
            s_expected_onwards_req_headers.items(),
            d_expected_onwards_req_headers.items(),
        )),
        # expected_resp_headers
        dict(chain(t_expected_resp_headers.items(), s_expected_resp_headers.items(),)),
        expected_dm_request_id_header_final_value,
    ) for (
        t_extra_config,
        t_extra_req_headers,
        expected_trace_id,
        expect_trace_random_call,
        t_expected_onwards_req_headers,
        t_expected_resp_headers,
        expected_dm_request_id_header_final_value,
    ), (
        s_extra_config,
        s_extra_req_headers,
        expected_span_id,
        expected_parent_span_id,
        s_expected_onwards_req_headers,
        s_expected_resp_headers,
    ), (
        d_extra_config,
        d_extra_req_headers,
        expected_is_sampled,
        expected_debug_flag,
        d_expected_onwards_req_headers,
    ) in product(
        _trace_id_related_params,
        _span_id_related_params,
        _debug_sampling_related_params,
    )
)


@pytest.mark.parametrize(
    (
        "extra_config",
        "extra_req_headers",
        "expected_trace_id",
        "expect_trace_random_call",
        "expected_span_id",
        "expected_parent_span_id",
        "expected_is_sampled",
        "expected_debug_flag",
        "expected_onwards_req_headers",
        "expected_resp_headers",
        "expected_dm_request_id_header_final_value",
    ),
    _param_combinations,
    ids=_abbreviate_id,
)
@mock.patch.object(RequestIdRequestMixin, "_traceid_random", autospec=True)
@mock.patch.object(RequestIdRequestMixin, "_spanid_random", autospec=True)
def test_request_header(
    spanid_random_mock,
    traceid_random_mock,
    app,
    extra_config,
    extra_req_headers,
    expected_trace_id,
    expect_trace_random_call,
    expected_span_id,
    expected_parent_span_id,
    expected_is_sampled,
    expected_debug_flag,
    expected_onwards_req_headers,
    expected_resp_headers,  # unused here
    expected_dm_request_id_header_final_value,
):
    app.config.update(extra_config)
    request_id_init_app(app)

    assert app.config.get("DM_REQUEST_ID_HEADER") == expected_dm_request_id_header_final_value

    traceid_random_mock.randrange.side_effect = assert_args_and_return(_GENERATED_TRACE_VALUE, 1 << 128)
    spanid_random_mock.randrange.side_effect = assert_args_and_return(_GENERATED_SPAN_VALUE, 1 << 64)

    with app.test_request_context(headers=extra_req_headers):
        assert request.request_id == request.trace_id == expected_trace_id
        assert request.span_id == expected_span_id
        assert request.parent_span_id == expected_parent_span_id
        assert request.is_sampled == expected_is_sampled
        assert request.debug_flag == expected_debug_flag
        assert request.get_onwards_request_headers() == expected_onwards_req_headers
        assert app.config.get("DM_REQUEST_ID_HEADER") == expected_dm_request_id_header_final_value
        assert request.get_extra_log_context() == {
            "trace_id": expected_trace_id,
            "span_id": expected_span_id,
            "parent_span_id": expected_parent_span_id,
            "is_sampled": "1" if expected_is_sampled else "0",
            "debug_flag": "1" if expected_debug_flag else "0",
        }

    assert traceid_random_mock.randrange.called is expect_trace_random_call
    assert spanid_random_mock.randrange.called is True


@mock.patch.object(RequestIdRequestMixin, "_traceid_random", autospec=True)
@mock.patch.object(RequestIdRequestMixin, "_spanid_random", autospec=True)
def test_request_header_zero_padded(
    spanid_random_mock,
    traceid_random_mock,
    app,
):
    request_id_init_app(app)

    traceid_random_mock.randrange.side_effect = assert_args_and_return(0xbeef, 1 << 128)
    spanid_random_mock.randrange.side_effect = assert_args_and_return(0xa, 1 << 64)

    with app.test_request_context():
        assert request.request_id == request.trace_id == "0000000000000000000000000000beef"
        assert request.span_id is None
        assert request.get_onwards_request_headers() == {
            "DM-Request-ID": "0000000000000000000000000000beef",
            "X-B3-TraceId": "0000000000000000000000000000beef",
            "X-B3-SpanId": "000000000000000a",
        }
        assert request.get_extra_log_context() == AnySupersetOf({
            'parent_span_id': None,
            'span_id': None,
            'trace_id': '0000000000000000000000000000beef',
        })

    assert traceid_random_mock.randrange.called is True
    assert spanid_random_mock.randrange.called is True


@pytest.mark.parametrize(
    (
        "extra_config",
        "extra_req_headers",
        "expected_trace_id",
        "expect_trace_random_call",
        "expected_span_id",
        "expected_parent_span_id",
        "expected_is_sampled",
        "expected_debug_flag",
        "expected_onwards_req_headers",
        "expected_resp_headers",
        "expected_dm_request_id_header_final_value",
    ),
    _param_combinations,
    ids=_abbreviate_id,
)
@mock.patch.object(RequestIdRequestMixin, "_traceid_random", autospec=True)
@mock.patch.object(RequestIdRequestMixin, "_spanid_random", autospec=True)
def test_response_headers_regular_response(
    spanid_random_mock,
    traceid_random_mock,
    app,
    extra_config,
    extra_req_headers,
    expected_trace_id,  # unused here
    expect_trace_random_call,
    expected_span_id,  # unused here
    expected_parent_span_id,  # unused here
    expected_is_sampled,  # unused here
    expected_debug_flag,  # unused here
    expected_onwards_req_headers,  # unused here
    expected_resp_headers,
    expected_dm_request_id_header_final_value,  # unused here
):
    app.config.update(extra_config)
    request_id_init_app(app)
    client = app.test_client()

    traceid_random_mock.randrange.side_effect = assert_args_and_return(_GENERATED_TRACE_VALUE, 1 << 128)

    with app.app_context():
        response = client.get('/', headers=extra_req_headers)
        # note using these mechanisms we're not able to test for the *absence* of a header
        assert dict(response.headers) == AnySupersetOf(expected_resp_headers)

    assert traceid_random_mock.randrange.called is expect_trace_random_call
    assert spanid_random_mock.randrange.called is False


@pytest.mark.parametrize(
    (
        "extra_config",
        "extra_req_headers",
        "expected_trace_id",
        "expect_trace_random_call",
        "expected_span_id",
        "expected_parent_span_id",
        "expected_is_sampled",
        "expected_debug_flag",
        "expected_onwards_req_headers",
        "expected_resp_headers",
        "expected_dm_request_id_header_final_value",
    ),
    _param_combinations,
    ids=_abbreviate_id,
)
@mock.patch.object(RequestIdRequestMixin, "_traceid_random", autospec=True)
@mock.patch.object(RequestIdRequestMixin, "_spanid_random", autospec=True)
def test_response_headers_error_response(
    spanid_random_mock,
    traceid_random_mock,
    app,
    extra_config,
    extra_req_headers,
    expected_trace_id,  # unused here
    expect_trace_random_call,
    expected_span_id,  # unused here
    expected_parent_span_id,  # unused here
    expected_is_sampled,  # unused here
    expected_debug_flag,  # unused here
    expected_onwards_req_headers,  # unused here
    expected_resp_headers,
    expected_dm_request_id_header_final_value,  # unused here
):
    app.config.update(extra_config)
    request_id_init_app(app)
    client = app.test_client()

    traceid_random_mock.randrange.side_effect = assert_args_and_return(_GENERATED_TRACE_VALUE, 1 << 128)

    @app.route('/')
    def error_route():
        raise Exception()

    with app.app_context():
        response = client.get('/', headers=extra_req_headers)
        assert response.status_code == 500
        assert dict(response.headers) == AnySupersetOf(expected_resp_headers)

    assert traceid_random_mock.randrange.called is expect_trace_random_call
    assert spanid_random_mock.randrange.called is False
