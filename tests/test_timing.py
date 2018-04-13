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


def _duration_real_gt_095(log_context):
    return log_context["duration_real"] > 0.095


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
        "{name} - {duration_process}s",
        (
            "{name} - {duration_process}s",
            ANY_string_matching(r"[a-zA-Z_.-]+ - [0-9eE.-]+s"),
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
        0.05,
        0.1,
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
        _duration_real_gt_095,
        _default_and_no_exception,
    ),
    (  # raise_exception values
        None,
        SentinelError,
    ),
))


def _expect_log(
    sampling_decision,
    sleep_time,
    message,
    log_level,
    condition,
    raise_exception,
):
    """return whether to expect a log line to be output or not"""
    return (
        (condition is timing.default_condition and sampling_decision)
        or (condition is _duration_real_gt_095 and sleep_time >= 0.1)
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
                    },
                )
            ] if _expect_log(
                sampling_decision,
                sleep_time,
                message,
                log_level,
                condition,
                raise_exception,
            ) else []
        ) for  # noqa - i don't know what you want me to do here flake8 nor do i care
            sampling_decision,
            sleep_time,
            message,
            log_level,
            condition,
            raise_exception
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
            ):
                assert mock_logger.log.call_args_list == []
                sleep(sleep_time)
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
            (  # expected_logs
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
            ) else ()
        ) for  # noqa - i don't know what you want me to do here flake8 nor do i care
            sampling_decision,
            sleep_time,
            message,
            log_level,
            condition,
            raise_exception
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
                ):
                    sleep(sleep_time)
                    if raise_exception is not None:
                        raise raise_exception("Boo")

        # ensure buffers are flushed
        logging.shutdown()

        assert tuple(json.loads(line) for line in log_file.read().splitlines()) == expected_logs
