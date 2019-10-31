from flask import Flask

from dmutils.flask_init import pluralize, init_app
import mock
import pytest


@pytest.mark.parametrize("count,singular,plural,output", [
    (0, "person", "people", "people"),
    (1, "person", "people", "person"),
    (2, "person", "people", "people"),
])
def test_pluralize(count, singular, plural, output):
    assert pluralize(count, singular, plural) == output


class TestFlaskInit:

    def setup(self):
        self.application = Flask("mytestapp")

    def test_init_app_sets_digitalmarketplace_env_config(self):
        init_app(self.application, {})
        assert self.application.config['DM_ENVIRONMENT'] == 'development'
        assert self.application.config['ENV'] == 'development'

    def test_init_app_sets_logging_config(self):
        init_app(self.application, {})
        assert self.application.config['DM_LOG_LEVEL'] == 'INFO'
        assert self.application.config['DM_APP_NAME'] == 'none'

    def test_init_app_sets_request_id_config(self):
        init_app(self.application, {})
        assert self.application.config['DM_TRACE_ID_HEADERS'] == ('DM-Request-ID', "X-B3-TraceId")
        assert self.application.config['DM_SPAN_ID_HEADERS'] == ('X-B3-SpanId', )
        assert self.application.config['DM_PARENT_SPAN_ID_HEADERS'] == ('X-B3-ParentSpanId', )
        assert self.application.config['DM_IS_SAMPLED_HEADERS'] == ('X-B3-Sampled', )
        assert self.application.config['DM_DEBUG_FLAG_HEADERS'] == ('X-B3-Flags', )
        assert self.application.config['DM_REQUEST_ID_HEADER'] == 'DM-Request-ID'

    def test_init_app_sets_cookie_probe_config(self):
        init_app(self.application, {})
        assert self.application.config['DM_COOKIE_PROBE_COOKIE_EXPECT_PRESENT'] is False
        assert self.application.config['DM_COOKIE_PROBE_COOKIE_MAX_AGE'] == 31536000.0
        assert self.application.config['DM_COOKIE_PROBE_COOKIE_NAME'] == 'dm_cookie_probe'
        assert self.application.config['DM_COOKIE_PROBE_COOKIE_VALUE'] == 'yum'

    def test_init_app_registers_custom_template_filters(self):
        init_app(self.application, {})
        expected_filters = [
            'capitalize_first',
            'format_links',
            'nbsp',
            'smartjoin',
            'preserve_line_breaks',
            'sub_country_codes',
            'dateformat',
            'datetimeformat',
            'datetodatetimeformat',
            'displaytimeformat',
            'shortdateformat',
            'timeformat',
            'utcdatetimeformat',
            'utctoshorttimelongdateformat'
        ]
        for filter in expected_filters:
            assert filter in self.application.jinja_env.filters

    def test_init_app_calls_optional_inits(self):
        bootstrap_mock = mock.Mock()
        data_api_client_mock = mock.Mock()
        db_mock = mock.Mock()
        login_manager_mock = mock.Mock()
        search_api_client_mock = mock.Mock()
        init_app(
            self.application,
            {},
            bootstrap=bootstrap_mock,
            data_api_client=data_api_client_mock,
            db=db_mock,
            login_manager=login_manager_mock,
            search_api_client=search_api_client_mock
        )

        assert bootstrap_mock.init_app.call_args_list == [mock.call(self.application)]
        assert data_api_client_mock.init_app.call_args_list == [mock.call(self.application)]
        assert db_mock.init_app.call_args_list == [mock.call(self.application)]
        assert login_manager_mock.init_app.call_args_list == [mock.call(self.application)]
        assert search_api_client_mock.init_app.call_args_list == [mock.call(self.application)]
