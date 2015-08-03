import unittest

import mock
from freezegun import freeze_time

from dmutils.s3 import S3ResponseError

from dmutils.documents import (
    generate_file_name,
    file_is_not_empty, filter_empty_files,
    file_is_less_than_5mb,
    file_is_open_document_format,
    validate_documents,
    upload_document
)


class TestGenerateFilename(unittest.TestCase):
    def test_filename_format(self):
        self.assertEquals(
            'slug/2/1-pricing-document-123.pdf',
            generate_file_name(
                'slug', 2, 1,
                'pricingDocumentURL', 'test.pdf',
                suffix='123'
            ))

    def test_default_suffix_is_datetime(self):
        with freeze_time('2015-01-02 03:04:05'):
            self.assertEquals(
                'slug/2/1-pricing-document-2015-01-02-0304.pdf',
                generate_file_name(
                    'slug', 2, 1,
                    'pricingDocumentURL', 'test.pdf',
                ))


class TestValidateDocuments(unittest.TestCase):
    def test_file_is_not_empty(self):
        self.assertTrue(file_is_not_empty(mock_file('file1', 1)))

    def test_file_is_empty(self):
        self.assertFalse(file_is_not_empty(mock_file('file1', 0)))

    def test_filter_empty_files(self):
        file1 = mock_file('file1', 1)
        file2 = mock_file('file2', 0)
        file3 = mock_file('file3', 10)
        self.assertEquals(
            filter_empty_files({'f1': file1, 'f2': file2, 'f3': file3}),
            {'f1': file1, 'f3': file3}
        )

    def test_file_is_less_than_5mb(self):
        self.assertTrue(file_is_less_than_5mb(mock_file('file1', 1)))

    def test_file_is_more_than_5mb(self):
        self.assertFalse(file_is_less_than_5mb(mock_file('file1', 5400001)))

    def test_file_is_open_document_format(self):
        self.assertTrue(file_is_open_document_format(mock_file('file1.pdf', 1)))

    def test_file_is_not_open_document_format(self):
        self.assertFalse(file_is_open_document_format(mock_file('file1.doc', 1)))

    def test_validate_documents(self):
        self.assertEqual(
            validate_documents({'file1': mock_file('file1.pdf', 1)}),
            {}
        )

    def test_validate_documents_not_open_document_format(self):
        self.assertEqual(
            validate_documents({'file1': mock_file('file1.doc', 1)}),
            {'file1': 'file_is_open_document_format'}
        )

    def test_validate_documents_not_less_than_5mb(self):
        self.assertEqual(
            validate_documents({'file1': mock_file('file1.pdf', 5400001)}),
            {'file1': 'file_is_less_than_5mb'}
        )

    def test_validate_documents_not_open_document_above_5mb(self):
        self.assertEqual(
            validate_documents({'file1': mock_file('file1.doc', 5400001)}),
            {'file1': 'file_is_open_document_format'}
        )

    def test_validate_multiple_documents(self):
        self.assertEqual(
            validate_documents({
                'file1': mock_file('file1.pdf', 5400001),
                'file2': mock_file('file1.pdf', 1),
                'file3': mock_file('file1.doc', 1),
            }),
            {
                'file1': 'file_is_less_than_5mb',
                'file3': 'file_is_open_document_format',
            }
        )


class TestUploadDocument(unittest.TestCase):
    def test_document_upload(self):
        uploader = mock.Mock()
        with freeze_time('2015-01-02 04:05:00'):
            self.assertEquals(
                upload_document(
                    uploader,
                    'http://assets',
                    {'id': "123", 'supplierId': 5, 'frameworkSlug': 'g-cloud-6'},
                    "pricingDocumentURL",
                    mock_file('file.pdf', 1)
                ),
                'http://assets/g-cloud-6/5/123-pricing-document-2015-01-02-0405.pdf'
            )

        uploader.save.assert_called_once_with(
            'g-cloud-6/5/123-pricing-document-2015-01-02-0405.pdf',
            mock.ANY,
            acl='public-read'
        )

    def test_document_private_upload(self):
        uploader = mock.Mock()
        with freeze_time('2015-01-02 04:05:00'):
            self.assertEquals(
                upload_document(
                    uploader,
                    'http://assets',
                    {'id': "123", 'supplierId': 5, 'frameworkSlug': 'g-cloud-6'},
                    "pricingDocumentURL",
                    mock_file('file.pdf', 1),
                    public=False
                ),
                'http://assets/g-cloud-6/5/123-pricing-document-2015-01-02-0405.pdf'
            )

        uploader.save.assert_called_once_with(
            'g-cloud-6/5/123-pricing-document-2015-01-02-0405.pdf',
            mock.ANY,
            acl='private'
        )

    def test_document_upload_s3_error(self):
        uploader = mock.Mock()
        uploader.save.side_effect = S3ResponseError(403, 'Forbidden')
        with freeze_time('2015-01-02 04:05:00'):
            self.assertFalse(upload_document(
                uploader,
                'http://assets',
                {'id': "123", 'supplierId': 5, 'frameworkSlug': 'g-cloud-6'},
                "pricingDocumentURL",
                mock_file('file.pdf', 1)
            ))


def mock_file(filename, length, name=None):
    mock_file = mock.MagicMock()
    mock_file.read.return_value = '*' * length
    mock_file.filename = filename
    mock_file.name = name

    return mock_file
