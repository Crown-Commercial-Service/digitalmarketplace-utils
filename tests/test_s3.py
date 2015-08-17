import unittest
import os
import datetime

import mock
from dmutils.s3 import S3


class TestS3Uploader(unittest.TestCase):
    def setUp(self):
        self.s3_mock = mock.Mock()
        self._boto_patch = mock.patch(
            'dmutils.s3.boto.connect_s3',
            return_value=self.s3_mock
        )
        self._boto_patch.start()

    def tearDown(self):
        self._boto_patch.stop()

    def test_get_bucket(self):
        S3('test-bucket')
        self.s3_mock.get_bucket.assert_called_with('test-bucket')

    def test_get_signed_url(self):
        mock_bucket = FakeBucket(['documents/file.pdf'])
        self.s3_mock.get_bucket.return_value = mock_bucket

        S3('test-bucket').get_signed_url('documents/file.pdf')
        mock_bucket.s3_key_mock.generate_url.assert_called_with(30)

    def test_get_signed_url_with_expires_at(self):
        mock_bucket = FakeBucket(['documents/file.pdf'])
        self.s3_mock.get_bucket.return_value = mock_bucket

        S3('test-bucket').get_signed_url('documents/file.pdf', 10)
        mock_bucket.s3_key_mock.generate_url.assert_called_with(10)

    def test_list_files(self):
        mock_bucket = mock.Mock()
        self.s3_mock.get_bucket.return_value = mock_bucket

        fake_key = FakeKey('dir/file 1.odt')
        mock_bucket.list.return_value = [fake_key]
        expected = [fake_key.fake_format_key(filename='file 1', ext='odt')]

        self.assertEqual(S3('test-bucket').list(), expected)

    def test_list_files_removes_directories(self):
        mock_bucket = mock.Mock()
        self.s3_mock.get_bucket.return_value = mock_bucket

        fake_key_directory = FakeKey('dir/', size=0)
        fake_key_file = FakeKey('dir/file 1.odt')
        mock_bucket.list.return_value = [
            fake_key_directory,
            fake_key_file
        ]
        expected = [fake_key_file.fake_format_key(filename='file 1', ext='odt')]

        self.assertEqual(S3('test-bucket').list(), expected)

    def test_list_files_order_by_last_modified(self):
        mock_bucket = mock.Mock()
        self.s3_mock.get_bucket.return_value = mock_bucket

        fake_key_later = FakeKey('dir/file 1.odt')
        fake_key_earlier = FakeKey('dir/file 2.odt', last_modified='2014-08-17T14:00:00.000Z')
        mock_bucket.list.return_value = [
            fake_key_later,
            fake_key_earlier
        ]
        expected = [
            fake_key_earlier.fake_format_key(filename='file 2', ext='odt'),
            fake_key_later.fake_format_key(filename='file 1', ext='odt')
        ]

        self.assertEqual(S3('test-bucket').list(), expected)

    def test_save_file(self):
        mock_bucket = FakeBucket()
        self.s3_mock.get_bucket.return_value = mock_bucket

        S3('test-bucket').save('folder/test-file.pdf', mock.Mock())
        self.assertEqual(mock_bucket.keys, set(['folder/test-file.pdf']))

    def test_save_sets_content_type_and_acl(self):
        mock_bucket = FakeBucket()
        self.s3_mock.get_bucket.return_value = mock_bucket

        S3('test-bucket').save('folder/test-file.pdf', mock.Mock())
        self.assertEqual(mock_bucket.keys, set(['folder/test-file.pdf']))

        mock_bucket.s3_key_mock.set_contents_from_file.assert_called_with(
            mock.ANY, headers={'Content-Type': 'application/pdf'})
        mock_bucket.s3_key_mock.set_acl.assert_called_with('public-read')

    def test_save_strips_leading_slash(self):
        mock_bucket = FakeBucket()
        self.s3_mock.get_bucket.return_value = mock_bucket

        S3('test-bucket').save('/folder/test-file.pdf', mock.Mock())
        self.assertEqual(mock_bucket.keys, set(['folder/test-file.pdf']))

    def test_default_move_prefix_is_datetime(self):
        mock_bucket = FakeBucket(['folder/test-file.pdf'])
        self.s3_mock.get_bucket.return_value = mock_bucket
        now = datetime.datetime(2015, 1, 1, 1, 2, 3, 4)

        with mock.patch.object(datetime, 'datetime',
                               mock.Mock(wraps=datetime.datetime)) as patched:
            patched.utcnow.return_value = now
            S3('test-bucket').save(
                'folder/test-file.pdf', mock.Mock(),
            )

            self.assertEqual(mock_bucket.keys, set([
                'folder/test-file.pdf',
                'folder/2015-01-01T01:02:03.000004-test-file.pdf'
            ]))

    def test_save_existing_file(self):
        mock_bucket = FakeBucket(['folder/test-file.pdf'])
        self.s3_mock.get_bucket.return_value = mock_bucket

        S3('test-bucket').save(
            'folder/test-file.pdf', mock.Mock(),
            move_prefix='OLD'
        )

        self.assertEqual(mock_bucket.keys, set([
            'folder/test-file.pdf',
            'folder/OLD-test-file.pdf'
        ]))

    def test_move_existing_doesnt_delete_file(self):
        mock_bucket = FakeBucket(['folder/test-file.odt'])
        self.s3_mock.get_bucket.return_value = mock_bucket

        S3('test-bucket')._move_existing(
            existing_path='folder/test-file.odt',
            move_prefix='OLD'
        )

        self.assertEqual(mock_bucket.keys, set([
            'folder/test-file.odt',
            'folder/OLD-test-file.odt'
        ]))

    def test_content_type_detection(self):
        # File extensions allowed for G6 documents: pdf, odt, ods, odp
        test_type = S3('test-bucket')._get_mimetype('test-file.pdf')
        self.assertEqual(test_type,
                         'application/pdf')

        test_type = S3('test-bucket')._get_mimetype('test-file.odt')
        self.assertEqual(test_type,
                         'application/vnd.oasis.opendocument.text')

        test_type = S3('test-bucket')._get_mimetype('test-file.ods')
        self.assertEqual(test_type,
                         'application/vnd.oasis.opendocument.spreadsheet')

        test_type = S3('test-bucket')._get_mimetype('test-file.odp')
        self.assertEqual(test_type,
                         'application/vnd.oasis.opendocument.presentation')


class FakeBucket(object):
    def __init__(self, keys=None):
        self.keys = set(keys or [])
        self.s3_key_mock = mock.Mock()
        self.s3_key_mock.name = "test-file.pdf"

    def get_key(self, key):
        if key in self.keys:
            return self.s3_key_mock

    def delete_key(self, key):
        self.keys.remove(key)

    def new_key(self, key):
        self.keys.add(key)
        return self.s3_key_mock

    def copy_key(self, new_key, *args, **kwargs):
        self.keys.add(new_key)


class FakeKey(object):
    def __init__(self, name, last_modified=None, size=None):
        self.name = name
        self.last_modified = last_modified or '2015-08-17T14:00:00.000Z'
        self.size = size if size is not None else 1

    def fake_format_key(self, filename, ext):
        return {
            'path': self.name,
            'ext': ext,
            'filename': filename,
            'last_modified': self.last_modified,
            'size': self.size
        }
