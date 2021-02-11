from contextlib import contextmanager
import inspect
import logging
import sys
import time

from flask import request
from flask.ctx import has_request_context


SLOW_EXTERNAL_CALL_THRESHOLD = 0.25
SLOW_DEFAULT_CALL_THRESHOLD = 0.5


def _logged_duration_default_message(log_context):
    return "Block {} in {{duration_real}}s of real-time".format(
        "executed" if sys.exc_info()[0] is None else "raised {}".format(sys.exc_info()[0].__name__)
    )


def _logged_duration_default_condition(log_context):
    return has_request_context() and (
        getattr(request, "is_sampled", False) or log_context.get("duration_real", 0) > SLOW_DEFAULT_CALL_THRESHOLD
    )


def _logged_duration_default_log_func(logger, message, log_level, log_context):
    final_message = message(log_context) if callable(message) else message
    logger.log(log_level, final_message, exc_info=(sys.exc_info()[0] is not None), extra=log_context)


_logged_duration_default_logger = logging.getLogger(__name__)


@contextmanager
def logged_duration(
    logger=_logged_duration_default_logger,
    message=_logged_duration_default_message,
    log_level=logging.DEBUG,
    condition=_logged_duration_default_condition,
    log_func=_logged_duration_default_log_func,
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
                          log if there is a current Flask request with a True `is_sampled` attribute. A
                          condition of True or None will cause logs to *always* be emitted.
        :param log_func:  The actual logging function which will be called if `condition` passes. Arguments passed are:
                          ``logger``, ``message``, ``log_level`` (all verbatim as passed to ``logged_duration``) and
                          ``log_context``.
    """
    original_real_time = time.perf_counter()
    # NOTE this is *process* time, not *thread* time. if multiple threads are running in this process it will include
    # their cpu time too. getting *thread* time will be possible in python 3.7+ (but even then it doesn't work on older
    # macos)
    original_process_time = time.process_time()

    log_context = {}

    try:
        yield log_context
    finally:
        duration_real = time.perf_counter() - original_real_time
        duration_process = time.process_time() - original_process_time

        log_context["duration_real"] = duration_real
        log_context["duration_process"] = duration_process

        if condition in (True, None,) or condition(log_context):
            log_func(logger, message, log_level, log_context)


#
# logged_duration's defaults are exposed here so that a caller is able to defer to the default or simply use a wrapper
# for the default when customizing the call. annotating them *onto* logged_duration itself allows these defaults to be
# used without needing an extra import.
#
logged_duration.default_log_func = _logged_duration_default_log_func  # type: ignore
logged_duration.default_message = _logged_duration_default_message  # type: ignore
logged_duration.default_condition = _logged_duration_default_condition  # type: ignore
# exposing this allows a caller to specify default_logger.getChild(...) as their logger
logged_duration.default_logger = _logged_duration_default_logger  # type: ignore


def exceeds_slow_external_call_threshold(log_context):
    """A public condition that will return True if the duration is above the threshold we have defined as acceptable for
    calls to external services (e.g. Notify, Mailchimp, S3, etc)."""
    return log_context['duration_real'] > SLOW_EXTERNAL_CALL_THRESHOLD


def request_is_sampled(log_context):
    """A public condition that returns True if the request has the X-B3-Sampled flag set in its headers. While this is
    the default condition for logged_duration, exposing it publically allows it to be easily combined with other
    conditions."""
    return has_request_context() and getattr(request, "is_sampled", False)


def exception_in_stack():
    """Return true if we are currently in the process of handling an exception, ie one has been caught in a try block.

    https://docs.python.org/3/library/sys.html#sys.exc_info
    """
    return sys.exc_info()[0] is not None


def different_message_for_success_or_error(success_message, error_message):
    """Can be passed into `logged_duration` as `message=different_message_for_success_or_error(x, y)` in order to
    generate different log messages depending on whether the block completed successfully or raised an exception."""
    return lambda _: success_message if not exception_in_stack() else error_message


def request_context_and_any_of_slow_call_or_sampled_request_or_exception_in_stack(log_context):
    return has_request_context() and (
        exceeds_slow_external_call_threshold(log_context) or request_is_sampled(log_context) or exception_in_stack()
    )


def logged_duration_for_external_request(service, description=None, success_message=None, error_message=None,
                                         logger=None):
    """A default implementation of `logged_duration` to wrap around calls to external services (such as Notify,
    Mailchimp, S3, ...) to generate log messages on these events in a standardised manner.

    This implementation will not log durations outside of a Flask request context (e.g. when running scripts).

    Use to wrap a call to a third-party service like so [note the final () call which accepts additional args]:
    >>> with logged_duration_for_external_request('Notify'):
    >>>     notify_client.send_email('user@email.com')
    """
    if not description:
        # Returns the name of the calling function
        description = inspect.stack()[1].function

    success_message = (
        success_message
        if success_message else
        f'Call to {service} ({description}) executed in {{duration_real}}s'
    )
    error_message = (
        error_message
        if error_message else
        f'Exception from call to {service} ({description}) after {{duration_real}}s'
    )

    return logged_duration(
        message=different_message_for_success_or_error(success_message=success_message, error_message=error_message),
        condition=request_context_and_any_of_slow_call_or_sampled_request_or_exception_in_stack,
        **{'logger': logger} if logger else {}
    )
