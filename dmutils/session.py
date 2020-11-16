
import flask_session
import redis

import dmutils.cloudfoundry as cf


def init_app(app):
    if not app.config.get("SESSION_REDIS"):
        if app.config.get("DM_ENVIRONMENT") == "development":
            app.config["SESSION_REDIS"] = redis.Redis()
        else:
            vcap_services = cf.get_vcap_services()

            redis_service_name = app.config["DM_REDIS_SERVICE_NAME"]
            redis_service = cf.get_service_by_name_from_vcap_services(vcap_services, redis_service_name)

            app.config["SESSION_REDIS"] = redis.from_url(redis_service["credentials"]["uri"])

    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_TYPE"] = 'redis'
    flask_session.Session(app)
