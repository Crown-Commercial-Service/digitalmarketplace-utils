from collections import namedtuple

import json
import mock
import pytest

from dmutils.status import get_disk_space_status, get_app_status, StatusError


def statvfs_fixture(total_blocks, free_blocks):
    statvfs = namedtuple('statvfs', 'f_blocks f_bfree')
    return statvfs(total_blocks, free_blocks)


@mock.patch('dmutils.status.os.statvfs')
@pytest.mark.parametrize('kwargs, total_blocks, free_blocks, expected_status',
                         (
                             ({}, 1024, 1024, ('OK', 100)),
                             ({}, 1024, 512, ('OK', 50)),
                             ({}, 1024, 102, ('OK', 10)),
                             ({}, 1024, 14, ('LOW', 2)),
                             ({}, 1024, 0, ('LOW', 0)),
                             ({'low_disk_percent_threshold': 10}, 1024, 64, ('LOW', 7)),
                             ({'low_disk_percent_threshold': 20}, 1024, 100, ('LOW', 10)),
                             ({'low_disk_percent_threshold': 75}, 1024, 512, ('LOW', 50)),
                         ))
def test_disk_space_status(disk_usage, kwargs, total_blocks, free_blocks, expected_status):
    disk_usage.return_value = statvfs_fixture(total_blocks, free_blocks)

    assert get_disk_space_status(**kwargs) == expected_status


def additional_check(key, value):
    m = mock.MagicMock()
    m.return_value = {key: value}
    return m


@pytest.mark.parametrize('disk_status, '
                         'data_api_status, '
                         'search_api_status, '
                         'ignore_dependencies, '
                         'additional_checks, '
                         'additional_checks_internal, '
                         'expected_json, '
                         'expected_http_status',
                         (
                             (  # Test case #1 - no api clients, ignore_deps = False, result: 200
                                 ('OK', 90),
                                 None,
                                 None,
                                 False,
                                 [],
                                 [],
                                 {'status': 'ok', 'version': 'release-0', 'disk': 'OK (90% free)'},
                                 200
                             ),
                             (  # Test case #2 - data api client OK, ignore_deps = False, result: 200
                                 ('OK', 90),
                                 'ok',
                                 None,
                                 False,
                                 [],
                                 [],
                                 {'api_status': {'status': 'ok'}, 'status': 'ok', 'version': 'release-0',
                                  'disk': 'OK (90% free)'},
                                 200
                             ),
                             (  # Test case #3 - search api client OK, ignore_deps = False, result: 200
                                 ('OK', 90),
                                 None,
                                 'ok',
                                 False,
                                 [],
                                 [],
                                 {'search_api_status': {'status': 'ok'}, 'status': 'ok',
                                  'version': 'release-0', 'disk': 'OK (90% free)'},
                                 200
                             ),
                             (  # Test case #4 - data+search api clients OK, ignore_deps = False, result: 200
                                 ('OK', 90),
                                 'ok',
                                 'ok',
                                 False,
                                 [],
                                 [],
                                 {'api_status': {'status': 'ok'}, 'search_api_status': {'status': 'ok'},
                                  'status': 'ok', 'version': 'release-0', 'disk': 'OK (90% free)'},
                                 200
                             ),
                             (  # Test case #5 - data+search api clients OK, ignore_deps = False, +2 checks, result: 200
                                 ('OK', 90),
                                 'ok',
                                 'ok',
                                 False,
                                 [additional_check('k', 'v'), additional_check('k2', 'v2')],
                                 [],
                                 {
                                     'api_status': {'status': 'ok'}, 'search_api_status': {'status': 'ok'},
                                     'status': 'ok', 'version': 'release-0', 'disk': 'OK (90% free)',
                                     'k': 'v', 'k2': 'v2'
                                 },
                                 200,
                             ),
                             (  # Test case #6 - data+search api clients OK, ignore_deps = True, +2 checks, result: 500
                                 ('OK', 90),
                                 'ok',
                                 'ok',
                                 True,
                                 [additional_check('k', 'v'), additional_check('k2', 'v2')],
                                 [],
                                 {'status': 'ok', 'disk': 'OK (90% free)'},
                                 200,
                             ),
                             (  # Test case #6 - data api client ERROR, search api OK, ignore_deps = False, result: 500
                                 ('OK', 90),
                                 'error',
                                 'ok',
                                 False,
                                 [],
                                 [],
                                 {'api_status': {'status': 'error'},
                                  'search_api_status': {'status': 'ok'},
                                  'status': 'error',
                                  'version': 'release-0',
                                  'disk': 'OK (90% free)',
                                  'message': ['Error connecting to the Data API.']},
                                 500,
                             ),
                             (  # Test case #7 - data+search api client ERROR, ignore_deps = False, result: 500
                                 ('OK', 90),
                                 'error',
                                 'error',
                                 False,
                                 [],
                                 [],
                                 {'api_status': {'status': 'error'},
                                  'search_api_status': {'status': 'error'},
                                  'status': 'error',
                                  'version': 'release-0',
                                  'disk': 'OK (90% free)',
                                  'message': ['Error connecting to the Data API.',
                                              'Error connecting to the Search API.']},
                                 500,
                             ),
                             (  # Test case #8 - data+search api client ERROR, ignore_deps = True, result: 200
                                 ('OK', 90),
                                 'error',
                                 'error',
                                 True,
                                 [],
                                 [],
                                 {'status': 'ok', 'disk': 'OK (90% free)'},
                                 200,
                             ),
                             (  # Test case #9 - api clients OK, disk LOW, ignore_deps = True, result: 500
                                 ('LOW', 1),
                                 'error',
                                 'error',
                                 True,
                                 [],
                                 [],
                                 {'status': 'error', 'disk': 'LOW (1% free)',
                                  'message': ['Disk space low: 1% remaining.']},
                                 500,
                             ),
                             (  # Test case #10 - data+search api clients OK, ignore_deps=False, +1,1 checks, result:200
                                 ('OK', 80),
                                 'ok',
                                 'ok',
                                 False,
                                 [additional_check('passout', 'checks')],
                                 [additional_check('Habeas', 'Corpus')],
                                 {
                                     'api_status': {'status': 'ok'}, 'search_api_status': {'status': 'ok'},
                                     'status': 'ok', 'version': 'release-0', 'disk': 'OK (80% free)',
                                     'passout': 'checks', 'Habeas': 'Corpus'
                                 },
                                 200,
                             ),
                             (  # Test case #11 - data+search api clients OK, ignore_deps=True, +1,2 checks, result:200
                                 ('OK', 88),
                                 'ok',
                                 'ok',
                                 True,
                                 [additional_check('spellingbee', 'conundrum')],
                                 [additional_check('limp', 'galleypage'), additional_check('gauging', 'symmetry')],
                                 {
                                     'status': 'ok', 'disk': 'OK (88% free)',
                                     'limp': 'galleypage', 'gauging': 'symmetry'
                                 },
                                 200,
                             ),
                             (  # Test case #12 - data+search api clients OK, ignore_deps=True, +1,2 checks (1 fails),
                                #                 result:500
                                 ('OK', 50),
                                 'ok',
                                 'ok',
                                 True,
                                 [additional_check('embarra', 'two ars')],
                                 [additional_check('unpar', 'one ar'), mock.Mock(side_effect=StatusError("double es"))],
                                 {
                                     'status': 'error', 'disk': 'OK (50% free)', 'message': ['double es'],
                                     'unpar': 'one ar',
                                 },
                                 500,
                             ),
                         ))
def test_get_app_status(app,
                        disk_status,
                        data_api_status,
                        search_api_status,
                        ignore_dependencies,
                        additional_checks,
                        additional_checks_internal,
                        expected_json,
                        expected_http_status):
    app.config['VERSION'] = 'release-0'
    data_api_client = None
    search_api_client = None

    if data_api_status:
        data_api_client = mock.MagicMock()
        data_api_client.get_status.return_value = {'status': data_api_status}

    if search_api_status:
        search_api_client = mock.MagicMock()
        search_api_client.get_status.return_value = {'status': search_api_status}

    with mock.patch('dmutils.status.get_disk_space_status') as disk_status_patch:
        disk_status_patch.return_value = disk_status

        with app.app_context(), app.test_request_context():
            response, status_code = get_app_status(data_api_client=data_api_client,
                                                   search_api_client=search_api_client,
                                                   ignore_dependencies=ignore_dependencies,
                                                   additional_checks=additional_checks,
                                                   additional_checks_internal=additional_checks_internal)

    assert json.loads(response.data) == expected_json
    assert status_code == expected_http_status

    # If we pass in the ignore-dependencies flag we want to make sure that the API clients and additional checks
    # aren't called so that the endpoint returns as quickly as possible with the lowest chance to error.
    expected_call_list = ([] if ignore_dependencies else [mock.call()])

    if data_api_status:
        assert data_api_client.get_status.call_args_list == expected_call_list

    if search_api_status:
        assert search_api_client.get_status.call_args_list == expected_call_list

    for check in additional_checks:
        assert check.call_args_list == expected_call_list
