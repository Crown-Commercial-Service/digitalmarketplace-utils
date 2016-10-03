# coding: utf-8
import unittest

import mock
import pytest
from freezegun import freeze_time

from .helpers import mock_file
from dmutils.s3 import S3ResponseError

from dmutils.documents import (
    generate_file_name, get_extension,
    file_is_not_empty, file_is_empty, filter_empty_files,
    file_is_less_than_5mb,
    file_is_open_document_format,
    validate_documents,
    upload_document, upload_service_documents,
    get_signed_url, get_agreement_document_path, get_document_path,
    sanitise_supplier_name, file_is_pdf, file_is_zip, file_is_image,
    file_is_csv, generate_timestamped_document_upload_path)


class TestGenerateFilename(unittest.TestCase):
    def test_filename_format(self):
        self.assertEquals(
            'slug/documents/2/1-pricing-document-123.pdf',
            generate_file_name(
                'slug', 'documents', 2, 1,
                'pricingDocumentURL', 'test.pdf',
                suffix='123'
            ))

    def test_default_suffix_is_datetime(self):
        with freeze_time('2015-01-02 03:04:05'):
            self.assertEquals(
                'slug/documents/2/1-pricing-document-2015-01-02-0304.pdf',
                generate_file_name(
                    'slug', 'documents', 2, 1,
                    'pricingDocumentURL', 'test.pdf',
                ))


class TestValidateDocuments(unittest.TestCase):
    def test_get_extension(self):
        assert get_extension('what.jpg') == '.jpg'
        assert get_extension('what the.jpg') == '.jpg'
        assert get_extension('what.the.jpg') == '.jpg'
        assert get_extension('what.the..jpg') == '.jpg'
        assert get_extension('what.the.🐈.jpg') == '.jpg'
        assert get_extension('what.the.🐈jpg') == '.🐈jpg'
        assert get_extension('ಠ▃ಠ.jpg') == '.jpg'

    def test_file_is_not_empty(self):
        non_empty_file = mock_file('file1', 1)
        assert file_is_not_empty(non_empty_file)
        assert not file_is_empty(non_empty_file)

    def test_file_is_empty(self):
        empty_file = mock_file('file1', 0)
        assert not file_is_not_empty(empty_file)
        assert file_is_empty(empty_file)

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

    def test_file_is_pdf(self):
        self.assertTrue(file_is_pdf(mock_file('file.pdf', 1)))
        self.assertFalse(file_is_pdf(mock_file('file.doc', 1)))

    def test_file_is_csv(self):
        self.assertTrue(file_is_csv(mock_file('file.csv', 1)))
        self.assertFalse(file_is_csv(mock_file('file.sit', 1)))

    def test_file_is_zip(self):
        self.assertTrue(file_is_zip(mock_file('file.zip', 1)))
        self.assertFalse(file_is_zip(mock_file('file.sit', 1)))

    def test_file_is_image(self):
        self.assertTrue(file_is_image(mock_file('file.jpg', 1)))
        self.assertTrue(file_is_image(mock_file('file.jpeg', 1)))
        self.assertTrue(file_is_image(mock_file('file.png', 1)))
        self.assertFalse(file_is_image(mock_file('file.pdf', 1)))

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
        uploader = mock.Mock(bucket_short_name="documents")
        with freeze_time('2015-01-02 04:05:00'):
            self.assertEquals(
                upload_document(
                    uploader,
                    'http://assets',
                    {'id': "123", 'supplierId': 5, 'frameworkSlug': 'g-cloud-6'},
                    "pricingDocumentURL",
                    mock_file('file.pdf', 1)
                ),
                'http://assets/g-cloud-6/documents/5/123-pricing-document-2015-01-02-0405.pdf'
            )

        uploader.save.assert_called_once_with(
            'g-cloud-6/documents/5/123-pricing-document-2015-01-02-0405.pdf',
            mock.ANY,
            acl='public-read'
        )

    def test_document_private_upload(self):
        uploader = mock.Mock(bucket_short_name="documents")
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
                'http://assets/g-cloud-6/documents/5/123-pricing-document-2015-01-02-0405.pdf'
            )

        uploader.save.assert_called_once_with(
            'g-cloud-6/documents/5/123-pricing-document-2015-01-02-0405.pdf',
            mock.ANY,
            acl='private'
        )

    def test_document_upload_s3_error(self):
        uploader = mock.Mock(bucket_short_name="documents")
        uploader.save.side_effect = S3ResponseError(403, 'Forbidden')
        with freeze_time('2015-01-02 04:05:00'):
            self.assertFalse(upload_document(
                uploader,
                'http://assets',
                {'id': "123", 'supplierId': 5, 'frameworkSlug': 'g-cloud-6'},
                "pricingDocumentURL",
                mock_file('file.pdf', 1)
            ))

    def test_document_upload_with_other_bucket_short_name(self):
        uploader = mock.Mock(bucket_short_name="submissions")
        with freeze_time('2015-01-02 04:05:00'):
            self.assertEquals(
                upload_document(
                    uploader,
                    'http://assets',
                    {'id': "123", 'supplierId': 5, 'frameworkSlug': 'g-cloud-6'},
                    "pricingDocumentURL",
                    mock_file('file.pdf', 1)
                ),
                'http://assets/g-cloud-6/submissions/5/123-pricing-document-2015-01-02-0405.pdf'
            )

        uploader.save.assert_called_once_with(
            'g-cloud-6/submissions/5/123-pricing-document-2015-01-02-0405.pdf',
            mock.ANY,
            acl='public-read'
        )

    def test_document_upload_with_invalid_short_bucket_name(self):
        uploader = mock.Mock(bucket_short_name="invalid")
        with pytest.raises(AssertionError):
            self.assertEquals(
                upload_document(
                    uploader,
                    'http://assets',
                    {'id': "123", 'supplierId': 5, 'frameworkSlug': 'g-cloud-6'},
                    "pricingDocumentURL",
                    mock_file('file.pdf', 1)
                ),
                'http://assets/g-cloud-6/submissions/5/123-pricing-document-2015-01-02-0405.pdf'
            )

        assert not uploader.save.called


class TestUploadServiceDocuments(object):
    def setup(self):
        self.section = mock.Mock()
        self.section.get_question_ids.return_value = ['pricingDocumentURL']
        self.service = {
            'frameworkSlug': 'g-cloud-7',
            'supplierId': '12345',
            'id': '654321',
        }
        self.uploader = mock.Mock(bucket_short_name='documents')
        self.documents_url = 'http://localhost'

    def test_upload_service_documents(self):
        request_files = {'pricingDocumentURL': mock_file('q1.pdf', 100)}

        with freeze_time('2015-10-04 14:36:05'):
            files, errors = upload_service_documents(
                self.uploader, self.documents_url, self.service,
                request_files, self.section)

        self.uploader.save.assert_called_with(
            'g-cloud-7/documents/12345/654321-pricing-document-2015-10-04-1436.pdf', mock.ANY, acl='public-read')

        assert 'pricingDocumentURL' in files
        assert len(errors) == 0

    def test_upload_private_service_documents(self):
        request_files = {'pricingDocumentURL': mock_file('q1.pdf', 100)}

        with freeze_time('2015-10-04 14:36:05'):
            files, errors = upload_service_documents(
                self.uploader, self.documents_url, self.service,
                request_files, self.section,
                public=False)

        self.uploader.save.assert_called_with(
            'g-cloud-7/documents/12345/654321-pricing-document-2015-10-04-1436.pdf', mock.ANY, acl='private')

        assert 'pricingDocumentURL' in files
        assert len(errors) == 0

    def test_empty_files_are_filtered(self):
        request_files = {'pricingDocumentURL': mock_file('q1.pdf', 0)}

        files, errors = upload_service_documents(
            self.uploader, self.documents_url, self.service,
            request_files, self.section)

        assert len(files) == 0
        assert len(errors) == 0

    def test_only_files_in_section_are_uploaded(self):
        request_files = {'serviceDefinitionDocumentURL': mock_file('q1.pdf', 100)}

        files, errors = upload_service_documents(
            self.uploader, self.documents_url, self.service,
            request_files, self.section)

        assert len(files) == 0
        assert len(errors) == 0

    def test_upload_with_validation_errors(self):
        request_files = {'pricingDocumentURL': mock_file('q1.bad', 100)}

        files, errors = upload_service_documents(
            self.uploader, self.documents_url, self.service,
            request_files, self.section)

        assert files is None
        assert 'pricingDocumentURL' in errors


@pytest.mark.parametrize('base_url,expected', [
    ('http://other', 'http://other/foo?after'),
    (None, 'http://example/foo?after'),
    ('https://other', 'https://other/foo?after'),
    ('https://other:1234', 'https://other:1234/foo?after'),
    ('https://other/again', 'https://other/foo?after'),
])
def test_get_signed_url(base_url, expected):
    mock_bucket = mock.Mock()
    mock_bucket.get_signed_url.return_value = "http://example/foo?after"

    url = get_signed_url(mock_bucket, 'foo', base_url)

    assert url == expected


def test_get_agreement_document_path():
    assert get_agreement_document_path('g-cloud-7', 1234, 'foo.pdf') == \
        'g-cloud-7/agreements/1234/1234-foo.pdf'


def test_get_document_path():
    assert get_document_path('g-cloud-7', 1234, 'agreements', 'foo.pdf') == \
        'g-cloud-7/agreements/1234/1234-foo.pdf'


def test_generate_timestamped_document_upload_path():
    with freeze_time('2015-01-02 03:04:05'):
        assert generate_timestamped_document_upload_path('g-rain-12', '54321', 'agreeeeements', 'a-thing.pdf') == \
            'g-rain-12/agreeeeements/54321/2015-01-02T03:04:05-54321-a-thing.pdf'


def test_sanitise_supplier_name():
    assert sanitise_supplier_name(u'Kev\'s Butties') == 'Kevs_Butties'
    assert sanitise_supplier_name(u'   Supplier A   ') == 'Supplier_A'
    assert sanitise_supplier_name(u'Kev & Sons. | Ltd') == 'Kev_and_Sons_Ltd'
    assert sanitise_supplier_name(u'\ / : * ? \' " < > |') == '_'
    assert sanitise_supplier_name(u'kev@the*agency') == 'kevtheagency'
    assert sanitise_supplier_name(u"Ψ is a silly character") == "is_a_silly_character"
