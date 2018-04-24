from contextlib import contextmanager
import logging
import sys
from time import perf_counter, process_time

from flask import request
from flask.ctx import has_request_context


#
# logged_duration's defaults are exposed here so that a caller is able to defer to the default or simply use a wrapper
# for the default when customizing the call.
#


def default_message(log_context):
    return "Block {} in {{duration_real}}s of real-time".format(
        "executed" if sys.exc_info()[0] is None else "raised {}".format(sys.exc_info()[0].__name__)
    )


def default_condition(log_context):
    return has_request_context() and getattr(request, "sampling_decision", False)


def default_log_func(logger, message, log_level, log_context):
    final_message = message(log_context) if callable(message) else message
    logger.log(log_level, final_message, exc_info=(sys.exc_info()[0] is not None), extra=log_context)


# exposing this allows a caller to specify default_logger.getChild(...) as their logger
default_logger = logging.getLogger(__name__)


@contextmanager
def logged_duration(
    logger=default_logger,
    message=default_message,
    log_level=logging.DEBUG,
    condition=default_condition,
    log_func=default_log_func,
):
    """
        returns a context manager which will monitor the amount of time spent "inside" its code block and emit a log
        message on exiting block if ``condition`` passes. Uses a ``log_context`` dictionary as the log call's ``extra``
        parameter which will contain the parameters ``duration_real`` and ``duration_process``, each being a float
        duration in seconds. Additional parameters can be added to this ``log_context`` dictionary by annotating them
        to the dictionary which is yielded by the context manager, e.g.::

            with logged_duration(message="Received result {foo} in {duration_real}s") as log_context:
                ...
                log_context["foo"] = do_something()
                ...

        Logging action is triggered whether execution fell out of the block naturally or the code raised an exception.
        If log messages are not desired on exeptions these can always be excluded by a custom ``condition``.

        Can also be used as a function decorator.

        :param logger:    The logger to log the message to. It's best to set this at the very least to give the log
                          reader a clue as to what block of code is being timed.
        :param message:   Message format string to emit. Can be a callable which should return the desired message
                          format string when passed a ``log_context``.
        :param log_level: Numeric log level to use.
        :param condition: Callable accepting a single dictionary argument of the ``log_context``. Should return a
                          boolean signalling whether a log message should be emitted or not. Default condition emits a
                          log if there is a current Flask request with a True `sampling_decision` attribute. A
                          condition of True or None will cause logs to *always* be emitted.
        :param log_func:  The actual logging function which will be called if `condition` passes. Arguments passed are:
                          ``logger``, ``message``, ``log_level`` (all verbatim as passed to ``logged_duration``) and
                          ``log_context``.
    """
    original_real_time = perf_counter()
    # NOTE this is *process* time, not *thread* time. if multiple threads are running in this process it will include
    # their cpu time too. getting *thread* time will be possible in python 3.7+ (but even then it doesn't work on older
    # macos)
    original_process_time = process_time()

    log_context = {}

    try:
        yield log_context
    finally:
        duration_real = perf_counter() - original_real_time
        duration_process = process_time() - original_process_time

        log_context["duration_real"] = duration_real
        log_context["duration_process"] = duration_process

        if condition in (True, None,) or condition(log_context):
            log_func(logger, message, log_level, log_context)
