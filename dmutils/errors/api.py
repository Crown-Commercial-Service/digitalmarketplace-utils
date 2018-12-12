import json

from flask import current_app, jsonify
from werkzeug.exceptions import BadRequest


class ValidationError(ValueError):
    @property
    def message(self):
        return self.args[0]


def json_error_handler(e):
    try:
        # initially we'll try and assume this is an HTTPException of some sort.  for the most part, the default
        # HTTPExceptions render themselves in the desired way if returned as a response. the only change we want to
        # make is to enclose the error description in json.
        response = e.get_response()
        response.set_data(json.dumps({"error": e.description}))
        response.mimetype = current_app.config["JSONIFY_MIMETYPE"]

        return response
    except Exception:
        # either `e` wasn't an HTTPException or something went wrong in trying to jsonify it
        return jsonify(error="Internal error"), 500


def validation_error_handler(validation_error):
    return json_error_handler(BadRequest(description=validation_error.message))
