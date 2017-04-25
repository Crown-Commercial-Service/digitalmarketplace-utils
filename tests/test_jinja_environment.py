import mock
from dmutils.jinja2_environment import DMSandboxedEnvironment


def test_custom_filters_added():
    with mock.patch('dmutils.jinja2_environment.CUSTOM_FILTERS', {'test_filter': 'test_filter_method'}):
        env = DMSandboxedEnvironment()
        assert 'test_filter' in env.filters
        assert 'test_filter_method' == env.filters['test_filter']
