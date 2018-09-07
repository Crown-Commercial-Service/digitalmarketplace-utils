from dmutils import timing
from dmtestutils.comparisons import RestrictedAny, AnySupersetOf, AnyStringMatching

from collections import OrderedDict
from contextlib import contextmanager
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
    # this is only a context manager so it can be swapped out in place of mock_time_functions, which uses mock.patch
    # extensively
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
    return timing.logged_duration.default_condition(log_context) and sys.exc_info()[0] is None


# a dictionary of messages to be passed to logged_duration mapped against a tuple of values to expect, the first of
# these in the case that log message formatting has *not* yet taken place, the second assuming it *has*.
_messages_expected = OrderedDict((
    (
        timing.logged_duration.default_message,
        (
            {
                'success': "Block executed in {duration_real}s of real-time",
                'error': AnyStringMatching(r"Block raised \w+ in \{duration_real\}s of real-time"),
            },
            {
                'success': AnyStringMatching(r"Block executed in [0-9eE.-]+s of real-time"),
                'error': AnyStringMatching(r"Block raised \w+ in [0-9eE.-]+s of real-time"),
            },
        ),
    ),
    (
        timing.different_message_for_success_or_error(
            success_message='Block succeeded in {duration_real}s',
            error_message='Block raised {exc_info[0]} in {duration_real}s',
        ),
        (
            {
                'success': "Block succeeded in {duration_real}s",
                'error': "Block raised {exc_info[0]} in {duration_real}s",
            },
            {
                'success': AnyStringMatching(r"Block succeeded in [0-9eE.-]+s"),
                'error': AnyStringMatching(r"Block raised \w+ in [0-9eE.-]+s"),
            },
        ),
    ),
    (
        "{name}: {street} - {duration_process}s",
        (
            {
                'success': "{name}: {street} - {duration_process}s",
                'error': "{name}: {street} - {duration_process}s",
            },
            {
                'success': AnyStringMatching(r"flask\.app\.foobar: (\{.*\}|eccles) - [0-9eE.-]+s"),
                'error': AnyStringMatching(r"flask\.app\.foobar: (\{.*\}|eccles) - [0-9eE.-]+s"),
            },
        ),
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
        timing.logged_duration.default_condition,
        _duration_real_gt_075,
        _default_and_no_exception,
        timing.exceeds_slow_external_call_threshold,
        timing.request_is_sampled
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
        (condition is timing.logged_duration.default_condition and is_sampled)
        or (condition is _duration_real_gt_075 and sleep_time >= 0.08)
        or (condition is _default_and_no_exception and is_sampled and raise_exception is None)
        or (condition is timing.exceeds_slow_external_call_threshold
            and sleep_time >= timing.SLOW_EXTERNAL_CALL_THRESHOLD)
        or (condition is timing.request_is_sampled and is_sampled)
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
                        _messages_expected[message][0].get('error' if raise_exception else 'success'),
                        exc_info=bool(raise_exception),
                        extra={
                            "duration_real": RestrictedAny(
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
        (   #
            # we include a few explicit test cases using unmocked time functions to ensure the functions *actually* work
            # as expected
            #
            (
                # is_sampled
                True,
                # sleep_time
                0.5,
                # message
                "Touched the obedient {key}s for {duration_real}s",
                # log_level
                logging.WARNING,
                # condition
                timing.logged_duration.default_condition,
                # raise_exception
                None,
                # inject_context
                {
                    "key": "D#",
                    "keyes": "House Of",
                },
                # mock_time
                False,
                # expected_call_args_list
                [mock.call(
                    logging.WARNING,
                    "Touched the obedient {key}s for {duration_real}s",
                    exc_info=False,
                    extra={
                        "key": "D#",
                        "keyes": "House Of",
                        "duration_real": RestrictedAny(lambda value: 0.48 < value < 0.6),
                        "duration_process": RestrictedAny(lambda value: isinstance(value, Number)),
                    },
                )],
            ),
            (
                # is_sampled
                None,
                # sleep_time
                0.2,
                # message
                "The obedient {item}s feeding in {exc_info}",
                # log_level
                logging.ERROR,
                # condition
                True,
                # raise_exception
                ValueError,
                # inject_context
                None,
                # mock_time
                False,
                # expected_call_args_list
                [mock.call(
                    logging.ERROR,
                    "The obedient {item}s feeding in {exc_info}",
                    exc_info=True,
                    extra={
                        "duration_real": RestrictedAny(lambda value: 0.18 < value < 0.35),
                        "duration_process": RestrictedAny(lambda value: isinstance(value, Number)),
                    },
                )],
            ),
        ),
    ))
)
def test_logged_duration_mock_logger(
    app_with_mocked_logger,
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
    with app_with_mocked_logger.test_request_context("/", headers={}):
        request.is_sampled = is_sampled

        with (mock_time_functions() if mock_time else actual_time_functions()) as (
            _sleep,
            _perf_counter,
            _process_time,
        ):
            with (null_context_manager() if raise_exception is None else pytest.raises(raise_exception)):
                with timing.logged_duration(
                    logger=app_with_mocked_logger.logger,
                    message=message,
                    log_level=log_level,
                    condition=condition,
                ) as log_context:
                    assert app_with_mocked_logger.logger.log.call_args_list == []
                    _sleep(sleep_time)
                    if inject_context is not None:
                        log_context.update(inject_context)
                    if raise_exception is not None:
                        raise raise_exception("Boo")

    assert app_with_mocked_logger.logger.log.call_args_list == expected_call_args_list


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
                        (AnySupersetOf({"levelname": "WARNING"}),)
                        if ("street" in str(message) and "street" not in (inject_context or {})) else ()
                    ),
                    AnySupersetOf({
                        "name": "flask.app.foobar",
                        "levelname": logging.getLevelName(log_level),
                        "message": _messages_expected[message][1].get('error' if raise_exception else 'success'),
                        "duration_real": RestrictedAny(
                            # a double-closure here to get around python's weird behaviour when capturing iterated
                            # variables (in this case `sleep_time`)
                            (lambda st: lambda val: st * 0.95 < val < st * 1.5)(sleep_time)
                        ),
                        "duration_process": RestrictedAny(lambda value: isinstance(value, Number)),
                        **(inject_context or {}),
                        **(
                            {
                                "exc_info": AnyStringMatching(
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
        (   #
            # we include a few explicit test cases using unmocked time functions to ensure the functions *actually* work
            # as expected
            #
            (
                # is_sampled
                True,
                # sleep_time
                0.5,
                # message
                "Touched the obedient {key}s for {duration_real}s",
                # log_level
                logging.WARNING,
                # condition
                timing.logged_duration.default_condition,
                # raise_exception
                None,
                # inject_context
                {
                    "key": "D#",
                    "keyes": "House Of",
                },
                # mock_time
                False,
                # expected_logs
                (AnySupersetOf({
                    "message": AnyStringMatching(r"Touched the obedient D#s for [0-9Ee.-]+s"),
                    "levelname": "WARNING",
                    "key": "D#",
                    "duration_real": RestrictedAny(lambda value: 0.48 < value < 0.6),
                    "duration_process": RestrictedAny(lambda value: isinstance(value, Number)),
                    "name": "flask.app.foobar",
                }),),
            ),
            (
                # is_sampled
                None,
                # sleep_time
                0.2,
                # message
                "The obedient {item}s feeding in {exc_info}",
                # log_level
                logging.ERROR,
                # condition
                True,
                # raise_exception
                ValueError,
                # inject_context
                None,
                # mock_time
                False,
                # expected_logs
                (
                    AnySupersetOf({
                        "levelname": "WARNING",
                        "message": AnyStringMatching(r".*missing key.*", flags=re.IGNORECASE),
                    }),
                    AnySupersetOf({
                        "message": AnyStringMatching(
                            r"The obedient \{.*\}s feeding in .*ValueError.*",
                            flags=re.DOTALL,
                        ),
                        "levelname": "ERROR",
                        "exc_info": AnyStringMatching(
                            r".*ValueError.*",
                            flags=re.DOTALL,
                        ),
                        "duration_real": RestrictedAny(lambda value: 0.18 < value < 0.35),
                        "duration_process": RestrictedAny(lambda value: isinstance(value, Number)),
                        "name": "flask.app.foobar",
                    }),
                ),
            ),
        )
    ))
)
def test_logged_duration_real_logger(
    app_with_stream_logger,
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
    app, stream = app_with_stream_logger

    with app.test_request_context("/", headers={}):
        request.is_sampled = is_sampled

        with (mock_time_functions() if mock_time else actual_time_functions()) as (
            _sleep,
            _perf_counter,
            _process_time,
        ):
            with (null_context_manager() if raise_exception is None else pytest.raises(raise_exception)):
                with timing.logged_duration(
                    logger=app.logger.getChild("foobar"),
                    message=message,
                    log_level=log_level,
                    condition=condition,
                ) as log_context:
                    _sleep(sleep_time)
                    if inject_context is not None:
                        log_context.update(inject_context)
                    if raise_exception is not None:
                        raise raise_exception("Boo")

    stream.seek(0)
    all_lines = tuple(json.loads(line) for line in stream.read().splitlines())

    assert all_lines == (AnySupersetOf({"levelname": "INFO", "message": "Logging configured"}),) + expected_logs
