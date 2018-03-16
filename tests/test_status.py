from collections import namedtuple

import mock
import pytest

from dmutils.status import get_disk_space_status


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
