from datetime import timedelta

from flask import current_app, request


DEFAULT_DM_COOKIE_PROBE_COOKIE_NAME = "dm_cookie_probe"
DEFAULT_DM_COOKIE_PROBE_COOKIE_VALUE = "yum"
DEFAULT_DM_COOKIE_PROBE_COOKIE_MAX_AGE = timedelta(days=365).total_seconds()
DEFAULT_DM_COOKIE_PROBE_EXPECT_PRESENT = False


def init_app(app):
    """
        Unconditionally sets a long-lived cookie on all responses from `app`, which we will
        easily be able to check for when trying to determine whether cookies are working for a
        particular client at all.
    """
    app.config.setdefault("DM_COOKIE_PROBE_COOKIE_NAME", DEFAULT_DM_COOKIE_PROBE_COOKIE_NAME)
    app.config.setdefault("DM_COOKIE_PROBE_COOKIE_VALUE", DEFAULT_DM_COOKIE_PROBE_COOKIE_VALUE)
    app.config.setdefault("DM_COOKIE_PROBE_COOKIE_MAX_AGE", DEFAULT_DM_COOKIE_PROBE_COOKIE_MAX_AGE)
    app.config.setdefault("DM_COOKIE_PROBE_COOKIE_EXPECT_PRESENT", DEFAULT_DM_COOKIE_PROBE_EXPECT_PRESENT)

    @app.after_request
    def set_probe_cookie(response):
        response.set_cookie(
            app.config["DM_COOKIE_PROBE_COOKIE_NAME"],
            app.config["DM_COOKIE_PROBE_COOKIE_VALUE"],
            max_age=app.config["DM_COOKIE_PROBE_COOKIE_MAX_AGE"],
        )
        return response


def expected_probe_cookie_missing() -> bool:
    # DM_COOKIE_PROBE_EXPECT_PRESENT controls whether we expect the probe cookie to be present at all - allowing the
    # check to be rolled out and enabled gracefully among multiple frontends.
    is_missing = current_app.config.get(
        "DM_COOKIE_PROBE_EXPECT_PRESENT",
        DEFAULT_DM_COOKIE_PROBE_EXPECT_PRESENT
    ) and (
        request.cookies.get(
            current_app.config.get("DM_COOKIE_PROBE_COOKIE_NAME", DEFAULT_DM_COOKIE_PROBE_COOKIE_NAME)
        ) != current_app.config.get("DM_COOKIE_PROBE_COOKIE_VALUE", DEFAULT_DM_COOKIE_PROBE_COOKIE_VALUE)
    )

    if is_missing:
        current_app.logger.info(
            "cookie_probe.failed: cookies probably not working for this user"
        )

    return bool(is_missing)
