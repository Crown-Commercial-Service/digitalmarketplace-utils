# coding: utf-8
import mock
import pytest

from botocore.exceptions import ClientError
from freezegun import freeze_time

from dmutils.documents import (
    generate_file_name, get_extension,
    file_is_not_empty, file_is_empty, filter_empty_files,
    file_is_less_than_5mb,
    file_is_open_document_format,
    validate_documents,
    upload_document, upload_service_documents, upload_declaration_documents,
    get_signed_url, get_agreement_document_path, get_document_path,
    sanitise_supplier_name, file_is_pdf, file_is_zip, file_is_image,
    file_is_csv, generate_timestamped_document_upload_path,
    degenerate_document_path_and_return_doc_name, generate_download_filename)

from helpers import MockFile


class TestGenerateFilename:
    def test_filename_format(self):
        assert generate_file_name(
            'slug', 'documents', 2, 1,
            'pricingDocumentURL', 'test.pdf',
            suffix='123'
        ) == 'slug/documents/2/1-pricing-document-123.pdf'

    @pytest.mark.parametrize('question_name', ('modernSlaveryStatement', 'modernSlaveryStatementOptional'))
    def test_filename_format_with_null_service_id(self, question_name):
        assert generate_file_name(
            'slug', 'documents', 2, None,
            question_name, 'test.pdf',
            suffix='123'
        ) == 'slug/documents/2/modern-slavery-statement-123.pdf'

    def test_default_suffix_is_datetime(self):
        with freeze_time('2015-01-02 03:04:05'):
            assert generate_file_name(
                'slug', 'documents', 2, 1,
                'pricingDocumentURL', 'test.pdf',
            ) == 'slug/documents/2/1-pricing-document-2015-01-02-0304.pdf'


class TestValidateDocuments:
    def test_get_extension(self):
        assert get_extension('what.jpg') == '.jpg'
        assert get_extension('what the.jpg') == '.jpg'
        assert get_extension('what.the.jpg') == '.jpg'
        assert get_extension('what.the..jpg') == '.jpg'
        assert get_extension('what.the.🐈.jpg') == '.jpg'
        assert get_extension('what.the.🐈jpg') == '.🐈jpg'
        assert get_extension('ಠ▃ಠ.jpg') == '.jpg'

    def test_file_is_not_empty(self):
        non_empty_file = MockFile(b"*", 'file1')
        assert file_is_not_empty(non_empty_file)
        assert not file_is_empty(non_empty_file)

    def test_file_is_empty(self):
        empty_file = MockFile(b"", 'file1')
        assert not file_is_not_empty(empty_file)
        assert file_is_empty(empty_file)

    def test_filter_empty_files(self):
        file1 = MockFile(b"*", 'file1')
        file2 = MockFile(b"", 'file2')
        file3 = MockFile(b"*" * 10, 'file3')
        assert filter_empty_files({'f1': file1, 'f2': file2, 'f3': file3}) == {'f1': file1, 'f3': file3}

    def test_file_is_less_than_5mb(self):
        assert file_is_less_than_5mb(MockFile(b"*", 'file1'))
        assert not file_is_less_than_5mb(MockFile(b"*" * 5400001, 'file1'))

    def test_file_is_pdf(self):
        assert file_is_pdf(MockFile(open('tests/test_files/test_pdf.pdf', 'rb').read(), 'test_pdf.pdf')) is True
        assert file_is_pdf(MockFile(open('tests/test_files/test_image.jpg', 'rb').read(), 'test_pdf.pdf')) is False
        assert file_is_pdf(MockFile(open('tests/test_files/test_pdf.pdf', 'rb').read(), 'test_image.jpg')) is False
        assert file_is_pdf(MockFile(open('tests/test_files/test_image.jpg', 'rb').read(), 'test_image.jpg')) is False

    def test_file_is_zip(self):
        assert file_is_zip(MockFile(open('tests/test_files/test_zip.zip', 'rb').read(), 'test_zip.zip')) is True
        assert file_is_zip(MockFile(open('tests/test_files/test_image.jpg', 'rb').read(), 'test_image.zip')) is False
        assert file_is_zip(MockFile(open('tests/test_files/test_zip.zip', 'rb').read(), 'test_image.jpg')) is False
        assert file_is_zip(MockFile(open('tests/test_files/test_image.jpg', 'rb').read(), 'test_image.jpg')) is False

    @pytest.mark.parametrize('extension', ('.jpg', '.jpeg', '.png'))
    def test_file_is_image(self, extension):
        file_name = 'test_image{}'.format(extension)
        test_file_contents = open('tests/test_files/' + file_name, 'rb').read()

        assert file_is_image(MockFile(test_file_contents, file_name)) is True
        assert file_is_image(MockFile(test_file_contents, 'test_zip.zip')) is False
        assert file_is_image(MockFile(open('tests/test_files/test_zip.zip', 'rb').read(), file_name)) is False
        assert file_is_image(MockFile(open('tests/test_files/test_zip.zip', 'rb').read(), 'test_zip.zip')) is False

    @pytest.mark.parametrize('extension', ('pdf', 'odp', 'ods', 'odt'))
    def test_file_is_open_document_format(self, extension):
        file_name = 'test_{}.{}'.format(extension, extension)
        test_file_contents = open('tests/test_files/' + file_name, 'rb').read()
        invalid_file_contents = open('tests/test_files/test_image.jpg', 'rb').read()

        assert file_is_open_document_format(MockFile(test_file_contents, file_name)) is True
        assert file_is_open_document_format(MockFile(test_file_contents, 'test_file.doc')) is False
        assert file_is_open_document_format(MockFile(invalid_file_contents, file_name)) is False
        assert file_is_open_document_format(MockFile(invalid_file_contents, 'test_image.jpg')) is False

    def test_file_is_csv(self):
        """
        Our CSV checking is more lenient than other file checking it checks that a file is not of another file type
        we check for.
        """
        # Check a bytestring with valid extensions
        assert file_is_csv(MockFile(b"a,b,c,d\n1,2,3,4", 'file1.csv')) is True
        assert file_is_csv(MockFile(b"", 'file1.csv')) is True
        # Check a bytestring with invalid extensions
        assert file_is_csv(MockFile(b"a,b,c,d\n1,2,3,4", 'file1.tsv')) is False
        assert file_is_csv(MockFile(b"", 'file1.tsv')) is False
        # Check an image file with valid extension
        assert file_is_csv(MockFile(open('tests/test_files/test_image.jpg', 'rb').read(), 'file1.csv')) is False
        # Check an image file with invalid extension
        assert file_is_csv(MockFile(open('tests/test_files/test_image.jpg', 'rb').read(), 'file1.jpg')) is False

    def test_validate_documents(self):
        assert validate_documents(
            {'file1': MockFile(open('tests/test_files/test_pdf.pdf', 'rb').read(), 'test_pdf.pdf')}
        ) == {}

    def test_validate_documents_not_open_document_format(self):
        assert validate_documents({'file1': MockFile(b"*", 'file1.doc')}) == {'file1': 'file_is_open_document_format'}

    def test_validate_documents_not_less_than_5mb(self):
        big_pdf = MockFile(open('tests/test_files/test_pdf.pdf', 'rb').read() + b"*" * 5400001, 'test_pdf.pdf')

        assert validate_documents({'file1': big_pdf}) == {'file1': 'file_is_less_than_5mb'}

    def test_validate_documents_not_open_document_above_5mb(self):
        assert validate_documents({'file1': MockFile(b"*" * 5400001, 'file1.doc')}) == {
            'file1': 'file_is_open_document_format'
        }

    def test_validate_multiple_documents(self):
        big_pdf = MockFile(open('tests/test_files/test_pdf.pdf', 'rb').read() + b"*" * 5400001, 'test_pdf.pdf')
        pdf = MockFile(open('tests/test_files/test_pdf.pdf', 'rb').read(), 'test_pdf.pdf')

        assert validate_documents({
            'file1': big_pdf,
            'file2': pdf,
            'file3': MockFile(b"*", 'file1.doc'),
        }) == {
            'file1': 'file_is_less_than_5mb',
            'file3': 'file_is_open_document_format',
        }


class TestUploadDocument:
    def test_document_upload(self):
        uploader = mock.Mock()
        with freeze_time('2015-01-02 04:05:00'):
            assert upload_document(
                uploader,
                'documents',
                'http://assets',
                {'id': "123", 'supplierId': 5, 'frameworkSlug': 'g-cloud-6'},
                "pricingDocumentURL",
                MockFile(b"*", 'file.pdf')
            ) == 'http://assets/g-cloud-6/documents/5/123-pricing-document-2015-01-02-0405.pdf'

        uploader.save.assert_called_once_with(
            'g-cloud-6/documents/5/123-pricing-document-2015-01-02-0405.pdf',
            mock.ANY,
            acl='public-read'
        )

    def test_document_private_upload(self):
        uploader = mock.Mock()
        with freeze_time('2015-01-02 04:05:00'):
            assert upload_document(
                uploader,
                'documents',
                'http://assets',
                {'id': "123", 'supplierId': 5, 'frameworkSlug': 'g-cloud-6'},
                "pricingDocumentURL",
                MockFile(b"*", 'file.pdf'),
                public=False
            ) == 'http://assets/g-cloud-6/documents/5/123-pricing-document-2015-01-02-0405.pdf'

        uploader.save.assert_called_once_with(
            'g-cloud-6/documents/5/123-pricing-document-2015-01-02-0405.pdf',
            mock.ANY,
            acl='bucket-owner-full-control'
        )

    def test_document_upload_s3_error(self):
        uploader = mock.Mock()
        # using True as the mock "error_response" for this exception as we want to know if the function under test
        # wants to access a property of the exception rather than for it to continue in happy ignorance
        uploader.save.side_effect = ClientError(mock.MagicMock(), 'Forbidden')
        with freeze_time('2015-01-02 04:05:00'):
            assert not upload_document(
                uploader,
                'documents',
                'http://assets',
                {'id': "123", 'supplierId': 5, 'frameworkSlug': 'g-cloud-6'},
                "pricingDocumentURL",
                MockFile(b"*", 'file.pdf')
            )

    def test_document_upload_with_other_upload_type(self):
        uploader = mock.Mock()
        with freeze_time('2015-01-02 04:05:00'):
            assert upload_document(
                uploader,
                'submissions',
                'http://assets',
                {'id': "123", 'supplierId': 5, 'frameworkSlug': 'g-cloud-6'},
                "pricingDocumentURL",
                MockFile(b"*", 'file.pdf')
            ) == 'http://assets/g-cloud-6/submissions/5/123-pricing-document-2015-01-02-0405.pdf'

        uploader.save.assert_called_once_with(
            'g-cloud-6/submissions/5/123-pricing-document-2015-01-02-0405.pdf',
            mock.ANY,
            acl='public-read'
        )

    def test_document_upload_with_null_service_id(self):
        uploader = mock.Mock()
        with freeze_time('2015-01-02 04:05:00'):
            assert upload_document(
                uploader,
                'documents',
                'http://assets',
                {'supplierId': 5, 'frameworkSlug': 'g-cloud-11'},
                "modernSlaveryStatement",
                MockFile(b"*", 'file.pdf')
            ) == 'http://assets/g-cloud-11/documents/5/modern-slavery-statement-2015-01-02-0405.pdf'

        uploader.save.assert_called_once_with(
            'g-cloud-11/documents/5/modern-slavery-statement-2015-01-02-0405.pdf',
            mock.ANY,
            acl='public-read'
        )

    def test_document_upload_with_invalid_upload_type(self):
        uploader = mock.Mock()
        with pytest.raises(ValueError):
            assert upload_document(
                uploader,
                'invalid',
                'http://assets',
                {'id': "123", 'supplierId': 5, 'frameworkSlug': 'g-cloud-6'},
                "pricingDocumentURL",
                MockFile(b"*", 'file.pdf')
            ) == 'http://assets/g-cloud-6/submissions/5/123-pricing-document-2015-01-02-0405.pdf'

        assert not uploader.save.called


class TestUploadServiceDocuments:
    def setup(self):
        self.section = mock.Mock()
        self.section.get_question_ids.return_value = ['pricingDocumentURL']
        self.service = {
            'frameworkSlug': 'g-cloud-7',
            'supplierId': '12345',
            'id': '654321',
        }
        self.uploader = mock.Mock()
        self.documents_url = 'http://localhost'
        self.test_pdf = MockFile(open('tests/test_files/test_pdf.pdf', 'rb').read(), 'test_pdf.pdf')

    def test_upload_service_documents(self):
        request_files = {'pricingDocumentURL': self.test_pdf}

        with freeze_time('2015-10-04 14:36:05'):
            files, errors = upload_service_documents(
                self.uploader, 'documents', self.documents_url, self.service,
                request_files, self.section)

        self.uploader.save.assert_called_with(
            'g-cloud-7/documents/12345/654321-pricing-document-2015-10-04-1436.pdf', mock.ANY, acl='public-read')

        assert 'pricingDocumentURL' in files
        assert len(errors) == 0

    def test_upload_private_service_documents(self):
        request_files = {'pricingDocumentURL': self.test_pdf}

        with freeze_time('2015-10-04 14:36:05'):
            files, errors = upload_service_documents(
                self.uploader, 'documents', self.documents_url, self.service,
                request_files, self.section,
                public=False)

        self.uploader.save.assert_called_with(
            'g-cloud-7/documents/12345/654321-pricing-document-2015-10-04-1436.pdf',
            mock.ANY,
            acl='bucket-owner-full-control'
        )

        assert 'pricingDocumentURL' in files
        assert len(errors) == 0

    def test_empty_files_are_filtered(self):
        request_files = {'pricingDocumentURL': MockFile(b"", 'q1.pdf')}

        files, errors = upload_service_documents(
            self.uploader, 'documents', self.documents_url, self.service,
            request_files, self.section)

        assert len(files) == 0
        assert len(errors) == 0

    def test_only_files_in_section_are_uploaded(self):
        request_files = {'serviceDefinitionDocumentURL': MockFile(b"*" * 100, 'q1.pdf')}

        files, errors = upload_service_documents(
            self.uploader, 'documents', self.documents_url, self.service,
            request_files, self.section)

        assert len(files) == 0
        assert len(errors) == 0

    def test_upload_with_validation_errors(self):
        request_files = {'pricingDocumentURL': MockFile(b"*" * 100, 'q1.bad')}

        files, errors = upload_service_documents(
            self.uploader, 'documents', self.documents_url, self.service,
            request_files, self.section)

        assert files is None
        assert 'pricingDocumentURL' in errors


class TestUploadDeclarationDocuments:
    def setup(self):
        self.section = mock.Mock()
        self.section.get_question_ids.return_value = ['modernSlaveryStatement']
        self.uploader = mock.Mock()
        self.documents_url = 'http://localhost'
        self.test_pdf = MockFile(open('tests/test_files/test_pdf.pdf', 'rb').read(), 'test_pdf.pdf')

    def test_upload_declaration_documents(self):
        request_files = {'modernSlaveryStatement': self.test_pdf}

        with freeze_time('2015-10-04 14:36:05'):
            files, errors = upload_declaration_documents(
                self.uploader, 'documents', self.documents_url,
                request_files, self.section,
                'g-cloud-11', 12345
            )

        self.uploader.save.assert_called_with(
            'g-cloud-11/documents/12345/modern-slavery-statement-2015-10-04-1436.pdf', mock.ANY, acl='public-read')

        assert 'modernSlaveryStatement' in files
        assert len(errors) == 0

    def test_upload_private_declaration_documents(self):
        request_files = {'modernSlaveryStatement': self.test_pdf}

        with freeze_time('2015-10-04 14:36:05'):
            files, errors = upload_declaration_documents(
                self.uploader, 'documents', self.documents_url,
                request_files, self.section,
                'g-cloud-11', 12345,
                public=False)

        self.uploader.save.assert_called_with(
            'g-cloud-11/documents/12345/modern-slavery-statement-2015-10-04-1436.pdf',
            mock.ANY,
            acl='bucket-owner-full-control'
        )

        assert 'modernSlaveryStatement' in files
        assert len(errors) == 0

    def test_empty_files_are_filtered(self):
        request_files = {'modernSlaveryStatement': MockFile(b"", 'q1.pdf')}

        files, errors = upload_declaration_documents(
            self.uploader, 'documents', self.documents_url,
            request_files, self.section,
            'g-cloud-11', 12345
        )

        assert len(files) == 0
        assert len(errors) == 0

    def test_only_files_in_section_are_uploaded(self):
        request_files = {'serviceDefinitionDocumentURL': MockFile(b"*" * 100, 'q1.pdf')}

        files, errors = upload_declaration_documents(
            self.uploader, 'documents', self.documents_url,
            request_files, self.section,
            'g-cloud-11', 12345
        )

        assert len(files) == 0
        assert len(errors) == 0

    def test_upload_with_validation_errors(self):
        request_files = {'modernSlaveryStatement': MockFile(b"*" * 100, 'q1.bad')}

        files, errors = upload_declaration_documents(
            self.uploader, 'documents', self.documents_url,
            request_files, self.section,
            'g-cloud-11', 12345
        )

        assert files is None
        assert 'modernSlaveryStatement' in errors


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
            'g-rain-12/agreeeeements/54321/54321-a-thing-2015-01-02-030405.pdf'


def test_degenerate_document_path_and_return_doc_name():
    assert (
        degenerate_document_path_and_return_doc_name(
            "g-cloud-8/agreements/5478/5478-signed-framework-agreement-12-10-2016-101234.pdf"
        ) == "signed-framework-agreement-12-10-2016-101234.pdf"
    )
    assert (
        degenerate_document_path_and_return_doc_name(
            "g-cloud-7/agreements/1234/1234-countersigned-framework-agreement.jpg"
        ) == "countersigned-framework-agreement.jpg"
    )


def test_sanitise_supplier_name():
    assert sanitise_supplier_name(u'Kev\'s Butties') == 'Kevs_Butties'
    assert sanitise_supplier_name(u'   Supplier A   ') == 'Supplier_A'
    assert sanitise_supplier_name(u'Kev & Sons. | Ltd') == 'Kev_and_Sons_Ltd'
    assert sanitise_supplier_name(u'\ / : * ? \' " < > |') == '_' # noqa
    assert sanitise_supplier_name(u'kev@the*agency') == 'kevtheagency'
    assert sanitise_supplier_name(u"Ψ is a silly character") == "is_a_silly_character"


def test_generate_download_filename():
    assert generate_download_filename(584425, 'result-letter.pdf', 'ICNT_Consulting_Ltd') == 'ICNT_Consulting_Ltd-584425-result-letter.pdf'   # noqa
