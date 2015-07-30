import os
import datetime

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from .s3 import S3ResponseError


def filter_empty_files(files):
    """Remove any empty files from the list.

    :param files: a dictionary of file attachments
    :return: a dictionary of files with all empty files removed

    """
    return {
        key: contents for key, contents in files.items()
        if file_is_not_empty(contents)
    }


def validate_documents(files):
    """Validate document files for size and format

    :param files: a dictionary of file attachments

    :return: a dictionary of errors, where keys match
             the keys from the ``files`` argument and
             values are validator names used to look
             up the message in the question content
             files. If no errors were found an empty
             dictionary is returned.

    """
    errors = {}
    for field, contents in files.items():
        if not file_is_open_document_format(contents):
            errors[field] = 'file_is_open_document_format'
        elif not file_is_less_than_5mb(contents):
            errors[field] = 'file_is_less_than_5mb'

    return errors


def upload_document(uploader, documents_url, service, field, file_contents):
    """Upload the document to S3 bucket and return the document URL

    :param uploader: S3 uploader object
    :param documents_url: base assets URL used as root for creating the full
                          document URL.
    :param service: service object used to look up service and supplier id
                    for the generated document name
    :param field: name of the service field that the document URL is saved to,
                  used to generate the document name
    :param file_contents: attached file object

    :return: generated document URL or ``False`` if document upload
             failed

    """
    file_path = generate_file_name(
        service['supplierId'],
        service['id'],
        field,
        file_contents.filename
    )

    try:
        uploader.save(file_path, file_contents)
    except S3ResponseError:
        return False

    full_url = urlparse.urljoin(
        documents_url,
        file_path
    )

    return full_url


def file_is_not_empty(file_contents):
    not_empty = len(file_contents.read(1)) > 0
    file_contents.seek(0)
    return not_empty


def file_is_less_than_5mb(file_contents):
    size_limit = 5400000
    below_size_limit = len(file_contents.read(size_limit)) < size_limit
    file_contents.seek(0)

    return below_size_limit


def file_is_open_document_format(file_object):
    return get_extension(file_object.filename) in [
        ".pdf", ".pda", ".odt", ".ods", ".odp"
    ]


def generate_file_name(supplier_id, service_id, field, filename, suffix=None):
    if suffix is None:
        suffix = default_file_suffix()

    ID_TO_FILE_NAME_SUFFIX = {
        'serviceDefinitionDocumentURL': 'service-definition-document',
        'termsAndConditionsDocumentURL': 'terms-and-conditions',
        'sfiaRateDocumentURL': 'sfia-rate-card',
        'pricingDocumentURL': 'pricing-document',
    }

    return 'documents/{}/{}-{}-{}{}'.format(
        supplier_id,
        service_id,
        ID_TO_FILE_NAME_SUFFIX[field],
        suffix,
        get_extension(filename)
    )


def default_file_suffix():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d-%H%M")


def get_extension(filename):
    file_name, file_extension = os.path.splitext(filename)
    return file_extension.lower()
