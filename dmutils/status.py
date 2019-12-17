import math
import os
import sys
from flask import jsonify, current_app


from dmutils.timing import logged_duration


def get_version_label(path):
    try:
        path = os.path.join(path, 'version_label')
        with open(path) as f:
            return f.read().strip()
    except IOError:
        return None


def get_disk_space_status(low_disk_percent_threshold=5):
    """Accepts a single parameter that indicates the minimum percentage of disk space which should be free for the
    instance to be considered healthy.

    Returns a tuple containing two items: a status (OK or LOW) indicating whether the disk space remaining on the
    instance is below the threshold and the integer percentage remaining disk space."""
    disk_stats = os.statvfs('/')

    disk_free_percent = int(math.ceil(((disk_stats.f_bfree * 1.0) / disk_stats.f_blocks) * 100))

    return 'OK' if disk_free_percent >= low_disk_percent_threshold else 'LOW', disk_free_percent


class StatusError(Exception):
    """A stub class to use when implementing additional checks for an app's _status endpoint. See API for example.
    When raising a StatusError, make sure that the message passed in uniquely identifies the additional check you are
    performing so that any errors can more easily be tied back to a specific dependency that has failed."""
    message = ''

    def __init__(self, message):
        super().__init__(message)
        self.message = message


def _perform_additional_checks(additional_checks, response_data, error_messages):
    for additional_check in additional_checks:
        try:
            with logged_duration(
                logger=current_app.logger,
                message=(
                    lambda log_context: logged_duration.default_message(log_context) + " ({check_function})"
                ),
                condition=(
                    lambda log_context: logged_duration.default_condition(log_context) or sys.exc_info()[0] is not None
                ),
            ) as log_context:
                log_context["check_function"] = str(additional_check)
                check_result = additional_check()
            response_data.update(check_result)
        except StatusError as e:
            error_messages.append(e.message)


def get_app_status(
    data_api_client=None,
    search_api_client=None,
    ignore_dependencies=False,
    additional_checks=None,
    additional_checks_extended=None,
):
    """Generates output for `_status` endpoints on apps

    :param current_app: The flask `current_app` global.
    :param data_api_client: The app's data_api_client, if used.
    :param search_api_client: The app's search_api_client, if used.
    :param ignore_dependencies: Minimal endpoint checks only (i.e. the app is routable and disk space is fine).
    :param additional_checks: A sequence of callables that return dicts of data to be injected into the final JSON
                              response or raise StatusErrors if they need to log an error that should fail the
                              check (this will cause the endpoint to return a 500). These will be called even if
                              ignore_dependencies=True and should be reserved for checks that the service requires to
                              operate. For example checks to backing services such as persistent datastores or
                              processes.
    :param additional_checks_extended: Similar to `additional_checks`, but only called when ignore_dependencies=False
    :return: A dictionary describing the current state of the app with, at least, a 'status' key with a value of 'ok'
             or 'error'.
    """
    error_messages = []
    response_data = {'status': 'ok'}

    with logged_duration(
        logger=current_app.logger,
        message=(
            lambda log_context: logged_duration.default_message(log_context) + " (get_disk_space_status)"
        ),
    ):
        disk_status = get_disk_space_status()
    response_data['disk'] = f'{disk_status[0]} ({disk_status[1]}% free)'
    if disk_status[0].lower() != 'ok':
        error_messages.append(f'Disk space low: {disk_status[1]}% remaining.')

    if additional_checks:
        _perform_additional_checks(additional_checks, response_data, error_messages)

    if not ignore_dependencies:
        response_data['version'] = current_app.config['VERSION']

        if data_api_client:
            data_api_status = data_api_client.get_status() or {'status': 'n/a'}
            response_data['api_status'] = data_api_status
            if data_api_status['status'].lower() != 'ok':
                error_messages.append('Error connecting to the Data API.')

        if search_api_client:
            search_api_status = search_api_client.get_status() or {'status': 'n/a'}
            response_data['search_api_status'] = search_api_status
            if search_api_status['status'].lower() != 'ok':
                error_messages.append('Error connecting to the Search API.')
        if additional_checks_extended:
            _perform_additional_checks(additional_checks_extended, response_data, error_messages)

    if error_messages:
        current_app.logger.error(
            "Request completed with error_messages = {error_messages}",
            extra={"error_messages": error_messages},
        )
        response_data['status'] = 'error'
        response_data['message'] = error_messages

    return jsonify(**response_data), 200 if not error_messages else 500
