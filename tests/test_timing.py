from dmutils import timing

from collections import OrderedDict
from contextlib import contextmanager
from functools import lru_cache
from itertools import chain, product
import json
import logging
import mock
from numbers import Number
import random
import re
import sys
import time

from flask import request
import pytest
import six


class malleable_ANY:
    def __init__(self, condition):
        self._condition = condition

    def __eq__(self, other):
        return self._condition(other)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._condition})"

    def __hash__(self):
        return None


class ANY_superset_of(malleable_ANY):
    def __init__(self, subset_dict):
        self._subset_dict = subset_dict
        super().__init__(lambda other: self._subset_dict == {k: v for k, v in other.items() if k in self._subset_dict})

    def __repr__(self):
        return f"{self.__class__.__name__}({self._subset_dict})"


class ANY_string_matching(malleable_ANY):
    _cached_re_compile = staticmethod(lru_cache(maxsize=32)(re.compile))

    def __init__(self, *args, **kwargs):
        self._regex = self._cached_re_compile(*args, **kwargs)
        super().__init__(lambda other: isinstance(other, six.string_types) and self._regex.match(other))

    def __repr__(self):
        return f"{self.__class__.__name__}({self._regex})"


@contextmanager
def mock_time_functions():
    with mock.patch.multiple("time", perf_counter=mock.DEFAULT, process_time=mock.DEFAULT) as time_mocks:
        # to simulate the behaviour of these time functions, we create them all as closures capturing these common
        # "state" variables tracking the apparent pseudo-time according to each sampling function
        perf_counter_state = random.uniform(1000, 10000)
        process_time_state = random.uniform(1000, 10000)

        # the sampling functions just return the current state
        time_mocks["perf_counter"].side_effect = lambda: perf_counter_state
        time_mocks["process_time"].side_effect = lambda: process_time_state

        # the associated sleep function increments the apparent pseudo-times with an amount of randomness. it may seem
        # a bad idea to introduce randomness to "unit" tests, but the alternatives these are replacing are the *actual*
        # timing functions, which add much more noise & randomness to the process, and the tests have been written to
        # cope with that
        def _sleep(sleep_seconds):
            nonlocal perf_counter_state, process_time_state
            # allow for a small amount of "oversleep"
            perf_counter_state += random.uniform(sleep_seconds, sleep_seconds * 1.3)
            # the process may have been servicing other thread(s) during this period
            process_time_state += random.uniform(sleep_seconds * 0.001, sleep_seconds)

        yield _sleep, time_mocks["perf_counter"], time_mocks["process_time"]


@contextmanager
def actual_time_functions():
    yield time.sleep, time.perf_counter, time.process_time


# python 3.7 has an in-built version of this, but for now...
@contextmanager
def null_context_manager():
    yield


class SentinelError(Exception):
    """An exception that can't be mistaken for a genuine problem"""
    pass


def _duration_real_gt_075(log_context):
    return log_context["duration_real"] > 0.075


def _default_and_no_exception(log_context):
    return timing.default_condition(log_context) and sys.exc_info()[0] is None


# a dictionary of messages to be passed to logged_duration mapped against a tuple of values to expect, the first of
# these in the case that log message formatting has *not* yet taken place, the second assuming it *has*.
_messages_expected = OrderedDict((
    (
        timing.default_message,
        (
            ANY_string_matching(r"Block (executed|raised \w+) in \{duration_real\}s of real-time"),
            ANY_string_matching(r"Block (executed|raised \w+) in [0-9eE.-]+s of real-time"),
        ),
    ),
    (
        "{name}: {street} - {duration_process}s",
        (
            "{name}: {street} - {duration_process}s",
            ANY_string_matching(r"conftest\.foobar: (\{.*\}|eccles) - [0-9eE.-]+s"),
        )
    ),
))


_parameter_combinations = tuple(product(
    (  # is_sampled values
        False,
        None,
        True,
    ),
    (  # sleep_time values
        0.04,
        0.08,
    ),
    # message values
    _messages_expected.keys(),
    (  # log_level values
        logging.INFO,
        logging.WARNING,
    ),
    (  # condition values
        True,
        None,
        timing.default_condition,
        _duration_real_gt_075,
        _default_and_no_exception,
    ),
    (  # raise_exception values
        None,
        SentinelError,
    ),
    (  # inject_context values
        None,
        {
            "street": "eccles",
        },
    ),
))


def _expect_log(
    is_sampled,
    sleep_time,
    message,
    log_level,
    condition,
    raise_exception,
    inject_context,
):
    """return whether to expect a log line to be output or not"""
    return (
        (condition is timing.default_condition and is_sampled)
        or (condition is _duration_real_gt_075 and sleep_time >= 0.08)
        or (condition is _default_and_no_exception and is_sampled and raise_exception is None)
        or (condition in (True, None,))
    )


@pytest.mark.parametrize(
    (
        "is_sampled",
        "sleep_time",
        "message",
        "log_level",
        "condition",
        "raise_exception",
        "inject_context",
        "mock_time",
        "expected_call_args_list",
    ),
    tuple(chain(
        (
            (
                is_sampled,
                sleep_time,
                message,
                log_level,
                condition,
                raise_exception,
                inject_context,
                True,  # mock_time
                [  # expected_call_args_list
                    mock.call(
                        log_level,
                        _messages_expected[message][0],
                        exc_info=bool(raise_exception),
                        extra={
                            "duration_real": malleable_ANY(
                                # a double-closure here to get around python's weird behaviour when capturing iterated
                                # variables (in this case `sleep_time`)
                                (lambda st: lambda val: st * 0.95 < val < st * 1.5)(sleep_time)
                            ),
                            "duration_process": mock.ANY,
                            **(inject_context or {}),
                        },
                    )
                ] if _expect_log(
                    is_sampled,
                    sleep_time,
                    message,
                    log_level,
                    condition,
                    raise_exception,
                    inject_context,
                ) else []
            ) for  # noqa - i don't know what you want me to do here flake8 nor do i care
                is_sampled,
                sleep_time,
                message,
                log_level,
                condition,
                raise_exception,
                inject_context
            in _parameter_combinations
        ),
        (  # we include a few explicit test cases using unmocked time functions to ensure the functions *actually* work
           # as expected
            (
                True,
                0.5,
                "Touched the obedient {key}s for {duration_real}s",
                logging.WARNING,
                timing.default_condition,
                None,
                {
                    "key": "D#",
                    "keyes": "House Of",
                },
                False,
                [mock.call(
                    logging.WARNING,
                    "Touched the obedient {key}s for {duration_real}s",
                    exc_info=False,
                    extra={
                        "key": "D#",
                        "keyes": "House Of",
                        "duration_real": malleable_ANY(lambda value: 0.48 < value < 0.6),
                        "duration_process": malleable_ANY(lambda value: isinstance(value, Number)),
                    },
                )],
            ),
            (
                None,
                0.2,
                "The obedient {item}s feeding in {exc_info}",
                logging.ERROR,
                True,
                ValueError,
                None,
                False,
                [mock.call(
                    logging.ERROR,
                    "The obedient {item}s feeding in {exc_info}",
                    exc_info=True,
                    extra={
                        "duration_real": malleable_ANY(lambda value: 0.18 < value < 0.35),
                        "duration_process": malleable_ANY(lambda value: isinstance(value, Number)),
                    },
                )],
            ),
        ),
    ))
)
def test_logged_duration_mock_logger(
    app,
    # value to set the is_sampled flag to on the mock request
    is_sampled,
    # how long to sleep in seconds
    sleep_time,
    # message, log_level, condition - values to pass as arguments of logged_duration verbatim
    message,
    log_level,
    condition,
    # exception (class) to raise inside logged_duration, None to raise no exception
    raise_exception,
    # dict to update log_context with inside logged_duration, None perform no update
    inject_context,
    # whether to use mocked time primitives to speed up the test
    mock_time,
    # sequence of log dicts to expect to be output as json logs
    expected_call_args_list,
):
    with app.test_request_context("/", headers={}):
        request.is_sampled = is_sampled
        mock_logger = mock.Mock(spec_set=("log",))

        with (mock_time_functions() if mock_time else actual_time_functions()) as (
            _sleep,
            _perf_counter,
            _process_time,
        ):
            with (null_context_manager() if raise_exception is None else pytest.raises(raise_exception)):
                with timing.logged_duration(
                    logger=mock_logger,
                    message=message,
                    log_level=log_level,
                    condition=condition,
                ) as log_context:
                    assert mock_logger.log.call_args_list == []
                    _sleep(sleep_time)
                    if inject_context is not None:
                        log_context.update(inject_context)
                    if raise_exception is not None:
                        raise raise_exception("Boo")

    assert mock_logger.log.call_args_list == expected_call_args_list


@pytest.mark.parametrize(
    (
        "is_sampled",
        "sleep_time",
        "message",
        "log_level",
        "condition",
        "raise_exception",
        "inject_context",
        "mock_time",
        "expected_logs",
    ),
    tuple(chain(
        (
            (
                is_sampled,
                sleep_time,
                message,
                log_level,
                condition,
                raise_exception,
                inject_context,
                True,  # mock_time
                (  # expected_logs
                    *(  # in cases where our format string expects an extra parameter that wasn't supplied ("street"
                        # here), our log output will be lead by a warning about the missing parameter - I feel it's
                        # important to include this permutation to prove that we don't end up swallowing a genuine
                        # exception if we inadvertantly raise an exception while outputting our log message
                        (ANY_superset_of({"levelname": "WARNING"}),)
                        if ("street" in str(message) and "street" not in (inject_context or {})) else ()
                    ),
                    ANY_superset_of({
                        "name": "conftest.foobar",
                        "levelname": logging.getLevelName(log_level),
                        "message": _messages_expected[message][1],
                        "duration_real": malleable_ANY(
                            # a double-closure here to get around python's weird behaviour when capturing iterated
                            # variables (in this case `sleep_time`)
                            (lambda st: lambda val: st * 0.95 < val < st * 1.5)(sleep_time)
                        ),
                        "duration_process": malleable_ANY(lambda value: isinstance(value, Number)),
                        **(inject_context or {}),
                        **(
                            {
                                "exc_info": ANY_string_matching(
                                    r".*{}.*".format(re.escape(raise_exception.__name__)),
                                    flags=re.DOTALL,
                                ),
                            } if raise_exception else {}
                        ),
                    }),
                ) if _expect_log(
                    is_sampled,
                    sleep_time,
                    message,
                    log_level,
                    condition,
                    raise_exception,
                    inject_context,
                ) else ()
            ) for  # noqa - i don't know what you want me to do here flake8 nor do i care
                is_sampled,
                sleep_time,
                message,
                log_level,
                condition,
                raise_exception,
                inject_context
            in _parameter_combinations
        ),
        (  # we include a few explicit test cases using unmocked time functions to ensure the functions *actually* work
           # as expected
            (
                True,
                0.5,
                "Touched the obedient {key}s for {duration_real}s",
                logging.WARNING,
                timing.default_condition,
                None,
                {
                    "key": "D#",
                    "keyes": "House Of",
                },
                False,
                (ANY_superset_of({
                    "message": ANY_string_matching(r"Touched the obedient D#s for [0-9Ee.-]+s"),
                    "levelname": "WARNING",
                    "key": "D#",
                    "duration_real": malleable_ANY(lambda value: 0.48 < value < 0.6),
                    "duration_process": malleable_ANY(lambda value: isinstance(value, Number)),
                    "name": "conftest.foobar",
                }),),
            ),
            (
                None,
                0.2,
                "The obedient {item}s feeding in {exc_info}",
                logging.ERROR,
                True,
                ValueError,
                None,
                False,
                (
                    ANY_superset_of({
                        "levelname": "WARNING",
                        "message": ANY_string_matching(r".*missing key.*", flags=re.IGNORECASE),
                    }),
                    ANY_superset_of({
                        "message": ANY_string_matching(
                            r"The obedient \{.*\}s feeding in .*ValueError.*",
                            flags=re.DOTALL,
                        ),
                        "levelname": "ERROR",
                        "exc_info": ANY_string_matching(
                            r".*ValueError.*",
                            flags=re.DOTALL,
                        ),
                        "duration_real": malleable_ANY(lambda value: 0.18 < value < 0.35),
                        "duration_process": malleable_ANY(lambda value: isinstance(value, Number)),
                        "name": "conftest.foobar",
                    }),
                ),
            ),
        )
    ))
)
def test_logged_duration_real_logger(
    app_logtofile,
    # value to set the is_sampled flag to on the mock request
    is_sampled,
    # how long to sleep in seconds
    sleep_time,
    # message, log_level, condition - values to pass as arguments of logged_duration verbatim
    message,
    log_level,
    condition,
    # exception (class) to raise inside logged_duration, None to raise no exception
    raise_exception,
    # dict to update log_context with inside logged_duration, None perform no update
    inject_context,
    # whether to use mocked time primitives to speed up the test
    mock_time,
    # sequence of log dicts to expect to be output as json logs
    expected_logs,
):
    with open(app_logtofile.config["DM_LOG_PATH"], "r") as log_file:
        # consume log initialization line
        log_file.read()

        with app_logtofile.test_request_context("/", headers={}):
            request.is_sampled = is_sampled

            with (mock_time_functions() if mock_time else actual_time_functions()) as (
                _sleep,
                _perf_counter,
                _process_time,
            ):
                with (null_context_manager() if raise_exception is None else pytest.raises(raise_exception)):
                    with timing.logged_duration(
                        logger=app_logtofile.logger.getChild("foobar"),
                        message=message,
                        log_level=log_level,
                        condition=condition,
                    ) as log_context:
                        _sleep(sleep_time)
                        if inject_context is not None:
                            log_context.update(inject_context)
                        if raise_exception is not None:
                            raise raise_exception("Boo")

        # ensure buffers are flushed
        logging.shutdown()

        all_lines = tuple(json.loads(line) for line in log_file.read().splitlines())
        assert all_lines == expected_logs
