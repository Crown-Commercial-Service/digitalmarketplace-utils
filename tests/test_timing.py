from dmutils import timing

from collections import OrderedDict
from contextlib import contextmanager
from functools import lru_cache
from itertools import product
import json
import logging
import mock
from numbers import Number
import re
import sys
from time import sleep

from flask import request
import pytest


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
        super().__init__(lambda other: self._regex.match(other))

    def __repr__(self):
        return f"{self.__class__.__name__}({self._regex})"


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
    (  # sampling_decision values
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
    sampling_decision,
    sleep_time,
    message,
    log_level,
    condition,
    raise_exception,
    inject_context,
):
    """return whether to expect a log line to be output or not"""
    return (
        (condition is timing.default_condition and sampling_decision)
        or (condition is _duration_real_gt_075 and sleep_time >= 0.08)
        or (condition is _default_and_no_exception and sampling_decision and raise_exception is None)
        or (condition in (True, None,))
    )


@pytest.mark.parametrize(
    (
        "sampling_decision",
        "sleep_time",
        "message",
        "log_level",
        "condition",
        "raise_exception",
        "inject_context",
        "expected_call_args_list",
    ),
    tuple(
        (
            sampling_decision,
            sleep_time,
            message,
            log_level,
            condition,
            raise_exception,
            inject_context,
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
                sampling_decision,
                sleep_time,
                message,
                log_level,
                condition,
                raise_exception,
                inject_context,
            ) else []
        ) for  # noqa - i don't know what you want me to do here flake8 nor do i care
            sampling_decision,
            sleep_time,
            message,
            log_level,
            condition,
            raise_exception,
            inject_context
        in _parameter_combinations
    )
)
def test_logged_duration_mock_logger(
    app,
    sampling_decision,
    sleep_time,
    message,
    log_level,
    condition,
    raise_exception,
    inject_context,
    expected_call_args_list,
):
    with app.test_request_context("/", headers={}):
        request.sampling_decision = sampling_decision
        mock_logger = mock.Mock(spec_set=("log",))

        with (null_context_manager() if raise_exception is None else pytest.raises(raise_exception)):
            with timing.logged_duration(
                logger=mock_logger,
                message=message,
                log_level=log_level,
                condition=condition,
            ) as log_context:
                assert mock_logger.log.call_args_list == []
                sleep(sleep_time)
                if inject_context is not None:
                    log_context.update(inject_context)
                if raise_exception is not None:
                    raise raise_exception("Boo")

    assert mock_logger.log.call_args_list == expected_call_args_list


@pytest.mark.parametrize(
    (
        "sampling_decision",
        "sleep_time",
        "message",
        "log_level",
        "condition",
        "raise_exception",
        "inject_context",
        "expected_logs",
    ),
    tuple(
        (
            sampling_decision,
            sleep_time,
            message,
            log_level,
            condition,
            raise_exception,
            inject_context,
            (  # expected_logs
                *(  # in cases where our format string expects an extra parameter that wasn't supplied ("street" here),
                    # our log output will be lead by a warning about the missing parameter - I feel it's important to
                    # include this permutation to prove that we don't end up swallowing a genuine exception if we
                    # inadvertantly raise an exception while outputting our log message
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
                sampling_decision,
                sleep_time,
                message,
                log_level,
                condition,
                raise_exception,
                inject_context,
            ) else ()
        ) for  # noqa - i don't know what you want me to do here flake8 nor do i care
            sampling_decision,
            sleep_time,
            message,
            log_level,
            condition,
            raise_exception,
            inject_context
        in _parameter_combinations
    )
)
def test_logged_duration_real_logger(
    app_logtofile,
    sampling_decision,
    sleep_time,
    message,
    log_level,
    condition,
    raise_exception,
    inject_context,
    expected_logs,
):
    with open(app_logtofile.config["DM_LOG_PATH"], "r") as log_file:
        # consume log initialization line
        log_file.read()

        with app_logtofile.test_request_context("/", headers={}):
            request.sampling_decision = sampling_decision

            with (null_context_manager() if raise_exception is None else pytest.raises(raise_exception)):
                with timing.logged_duration(
                    logger=app_logtofile.logger.getChild("foobar"),
                    message=message,
                    log_level=log_level,
                    condition=condition,
                ) as log_context:
                    sleep(sleep_time)
                    if inject_context is not None:
                        log_context.update(inject_context)
                    if raise_exception is not None:
                        raise raise_exception("Boo")

        # ensure buffers are flushed
        logging.shutdown()

        all_lines = tuple(json.loads(line) for line in log_file.read().splitlines())
        assert all_lines == expected_logs
