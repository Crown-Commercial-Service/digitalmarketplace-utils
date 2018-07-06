from functools import partial

from flask import render_template, render_template_string

from dmutils.timing import logged_duration


SLOW_RENDER_THRESHOLD = 0.25


_logged_duration_partial = partial(
    logged_duration,
    condition=lambda log_context: (
        logged_duration.default_condition(log_context) or log_context["duration_real"] > SLOW_RENDER_THRESHOLD
    ),
)


timed_render_template = _logged_duration_partial(
    message=lambda log_context: f"Spent >{SLOW_RENDER_THRESHOLD}s in render_template",
)(render_template)
timed_render_template.__doc__ = """
    This is a simple ``logged_duration``-wrapped version of flask's ``render_template`` which will output a ``DEBUG``
    log message either when the request has been sent with zipkin "sample" mode or the request takes more than
    ``SLOW_RENDER_THRESHOLD`` seconds. The idea being in frontends we can freely use this in place of flask's regular
    ``render_template`` and get some insight as to the behaviour of the view "for free".
"""

timed_render_template_string = _logged_duration_partial(
    message=lambda log_context: f"Spent >{SLOW_RENDER_THRESHOLD}s in render_template_string",
)(render_template_string)
timed_render_template_string.__doc__ = """
    See ``timed_render_template``, only for ``render_template_string``.
"""
