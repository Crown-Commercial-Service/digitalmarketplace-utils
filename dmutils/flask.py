from functools import partial
import warnings

from flask import render_template, render_template_string
from flask_gzip import Gzip

from dmutils.timing import logged_duration


SLOW_RENDER_THRESHOLD = 0.25


_logged_duration_partial = partial(
    logged_duration,
    condition=lambda log_context: (
        logged_duration.default_condition(log_context)  # type: ignore
        or log_context["duration_real"] > SLOW_RENDER_THRESHOLD
    ),
)  # type: ignore


timed_render_template = _logged_duration_partial(
    message="Spent {duration_real}s in render_template",
)(render_template)
timed_render_template.__doc__ = """
    This is a simple ``logged_duration``-wrapped version of flask's ``render_template`` which will output a ``DEBUG``
    log message either when the request has been sent with zipkin "sample" mode or the request takes more than
    ``SLOW_RENDER_THRESHOLD`` seconds. The idea being in frontends we can freely use this in place of flask's regular
    ``render_template`` and get some insight as to the behaviour of the view "for free".
"""

timed_render_template_string = _logged_duration_partial(
    message="Spent {duration_real}s in render_template_string",
)(render_template_string)
timed_render_template_string.__doc__ = """
    See ``timed_render_template``, only for ``render_template_string``.
"""


class DMGzipMiddleware(Gzip):
    compress_by_default: bool

    def __init__(self, *args, compress_by_default: bool = False, **kwargs):
        kwargs.setdefault("minimum_size", 8192)
        self.compress_by_default = compress_by_default
        super().__init__(*args, **kwargs)

    def after_request(self, response):
        x_compression_safe = response.headers.pop("X-Compression-Safe", None)
        known_values = {"0": False, "1": True}
        compress = known_values.get(x_compression_safe, self.compress_by_default)

        if x_compression_safe not in known_values and x_compression_safe != "" and x_compression_safe is not None:
            warnings.warn(
                f"{self.__class__.__name__} received unknown X-Compression-Safe header value {x_compression_safe!r} - "
                "falling back to default"
            )

        # flask_gzip makes the minimum_size comparison itself, but we want to avoid outputting a misleading
        # logged_duration message if it's going to be prevented in the superclass.
        if compress and len(response.get_data()) >= self.minimum_size:
            with logged_duration(message="Spent {duration_real}s compressing response"):
                return super().after_request(response)
        else:
            return response
