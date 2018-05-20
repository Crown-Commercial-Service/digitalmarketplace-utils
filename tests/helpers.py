from contextlib import contextmanager
from datetime import datetime
from functools import lru_cache
from io import BytesIO
import re
import six

import mock
from testfixtures import logcapture


class IsDatetime(object):
    def __eq__(self, other):
        return isinstance(other, datetime)


class MockFile(BytesIO):
    def __init__(self, initial=b"", filename="", name=""):
        super().__init__(initial)
        self._name = name
        self._filename = filename

    @property
    def name(self):
        return self._name

    @property
    def filename(self):
        # weird flask property
        return self._filename


class MalleableAny:
    def __init__(self, condition):
        self._condition = condition

    def __eq__(self, other):
        return self._condition(other)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._condition})"

    def __hash__(self):
        return None


class AnySupersetOf(MalleableAny):
    def __init__(self, subset_dict):
        self._subset_dict = subset_dict
        super().__init__(lambda other: self._subset_dict == {k: v for k, v in other.items() if k in self._subset_dict})

    def __repr__(self):
        return f"{self.__class__.__name__}({self._subset_dict})"


class AnyStringMatching(MalleableAny):
    _cached_re_compile = staticmethod(lru_cache(maxsize=32)(re.compile))

    def __init__(self, *args, **kwargs):
        self._regex = self._cached_re_compile(*args, **kwargs)
        super().__init__(lambda other: isinstance(other, six.string_types) and self._regex.match(other))

    def __repr__(self):
        return f"{self.__class__.__name__}({self._regex})"


@contextmanager
def assert_log_entry(modules, message, count=1):
    """A context manager that can be used to wrap a block of code under test to assert that a specific message is
    logged. Works well with the AnyStringMatching malleable above to assert a message meeting a given format.

    This is designed to most easily assert a single kind of message being logged one or more times, but if you
    assign the context manager to a variable you can access the `records` attribute to see all log records and make
    further inspections.

    Example:
        with assert_log_entry(message=AnyStringMatching('^My unknown string with a random word \w+$', count=2)) as logs:
            do_something_that_produces_a_log()

        assert any('some other log message' in record.msg for record in logs.records)
    """
    log_catcher = logcapture.LogCapture(names=modules, install=False)

    log_catcher.install()

    try:
        yield log_catcher

    finally:
        log_catcher.uninstall_all()

        matching_records = [True for record in log_catcher.records if message == record.msg]
        assert len(matching_records) == count, f'{len(matching_records)} log records were seen that matched ' \
                                               f'`{message}`: expected {count}'


def assert_external_service_log_entry(service='\w+', description='.+', successful_call=True, extra_modules=None,
                                      count=1):
    """A subclass of AssertLogEntry specialised to inspect for the standardised message that is logged when
    making calls to backing services (Notify, Mandrill, S3, etc)."""
    if successful_call:
        expected_message = r'Call to {service} \({description}\) executed in {{duration_real}}s'
    else:
        expected_message = r'Exception from call to {service} \({description}\) after {{duration_real}}s'

    expected_message = expected_message.format(service=service, description=description)

    modules = ['dmutils.timing']
    if extra_modules:
        modules += extra_modules

    return assert_log_entry(modules=tuple(modules), message=AnyStringMatching(expected_message), count=count)


class PatchExternalServiceLogConditionMixin:
    def setup(self):
        self.log_condition_patch = mock.patch('dmutils.timing.request_context_and_any_of_slow_call_or_sampled_request')
        self.log_condition = self.log_condition_patch.start()
        self.log_condition.return_value = True

    def teardown(self):
        self.log_condition_patch.stop()
