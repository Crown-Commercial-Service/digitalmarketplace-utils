import datetime
import sys

import boto3
from moto import mock_s3
import pytest
from freezegun import freeze_time
from six import BytesIO
from six.moves.urllib.parse import parse_qs, urlparse

from dmutils.s3 import S3, get_file_size, default_region
from dmutils.formats import DATETIME_FORMAT


@pytest.yield_fixture
def s3_mock(request, os_environ):
    # we don't want any real aws credentials this environment might have used in the tests
    os_environ.update({
        "AWS_ACCESS_KEY_ID": "AKIAIABCDABCDABCDABC",
        "AWS_SECRET_ACCESS_KEY": "foobarfoobarfoobarfoobarfoobarfoobarfoob",
    })

    m = mock_s3()
    m.start()
    yield m
    m.stop()


@pytest.yield_fixture
def empty_bucket(request, s3_mock):
    s3_res = boto3.resource("s3", region_name=default_region)
    bucket = s3_res.Bucket("dear-liza")
    bucket.create()
    yield bucket


@pytest.yield_fixture
def bucket_with_file(request, empty_bucket):
    bucket = empty_bucket
    obj = empty_bucket.Object("with/straw.dear.pdf")
    obj.put(
        Body=b"123412341234",
        Metadata={
            "timestamp": datetime.datetime(2005, 4, 3, 2, 1).strftime(DATETIME_FORMAT),
        },
        ContentType="application/pdf",
        ContentDisposition='attachment; filename="blahs_on_blahs.pdf"',
    )
    yield bucket


@pytest.yield_fixture(params=(
    # tuples of (timestamp, expected_returned_timestamp)
    (" 6th May 2011, 17:03", "2011-05-06T17:03:00.000000Z",),  # arbitrarily formatted timestamp
    (None, "2018-01-25T00:00:00.000000Z",),  # timestamp metadata not set, so should return last_modified of object
))
def bucket_with_weird_file(request, empty_bucket):
    with freeze_time('2018-01-25'):
        timestamp, expected_returned_timestamp = request.param
        metadata = {}
        if timestamp is not None:
            metadata["timestamp"] = timestamp

        obj = empty_bucket.Object(".!!!.dear.pdf")

        # note how none of these file properties match each other

        obj.put(
            Body=(u"\u00a3" * 13).encode("utf-8"),
            Metadata=metadata,
            ContentType="image/jpeg",
            ContentDisposition='attachment; filename="blahs_on_blahs.png"',
        )
        yield {"expected_returned_timestamp": expected_returned_timestamp}


@pytest.yield_fixture
def bucket_with_multiple_files(request, empty_bucket):
    with freeze_time('2014-09-30'):
        bucket = empty_bucket
        for i in range(5):
            empty_bucket.Object("with/A{}/paper.dear.odt".format(i)).put(
                Body=b"abcdefgh" * (i + 1),
                Metadata={
                    "timestamp": datetime.datetime(2014, 10, ((i * 11) % 28) + 1).strftime(DATETIME_FORMAT),
                } if i != 3 else {},
            )
        # a "directory" which shouldn't show up in listings
        empty_bucket.Object("with/").put(Body=b"")
        yield bucket


@pytest.mark.usefixtures("s3_mock")
class TestS3Uploader(object):
    def test_bucket_name(self, empty_bucket):
        assert S3("dear-liza").bucket_name == "dear-liza"

    def test_path_exists(self, bucket_with_file):
        assert S3('dear-liza').path_exists('with/straw.dear.pdf') is True

    def test_path_exists_nonexistent_path(self, bucket_with_file):
        assert S3('dear-liza').path_exists('with/pencil/sharpener.png') is False

    def test_get_signed_url(self, bucket_with_file):
        signed_url = S3('dear-liza').get_signed_url('with/straw.dear.pdf')
        parsed_signed_url = urlparse(signed_url)
        # to an extent the url format should be opaque and up to amazon so we might have to rethink these assertions if
        # anything changes
        assert "dear-liza" in parsed_signed_url.hostname
        assert parsed_signed_url.path == "/with/straw.dear.pdf"
        parsed_qs = parse_qs(parsed_signed_url.query)
        assert parsed_qs["AWSAccessKeyId"] == ["AKIAIABCDABCDABCDABC"]
        assert parsed_qs["Signature"]

    @freeze_time('2015-10-10')
    def test_get_signed_url_with_expires_at(self, bucket_with_file):
        signed_url = S3('dear-liza').get_signed_url('with/straw.dear.pdf', expires_in=10)
        parsed_signed_url = urlparse(signed_url)

        parsed_qs = parse_qs(parsed_signed_url.query)
        assert parsed_qs["Expires"] == ["1444435210"]

    def test_get_key(self, bucket_with_file):
        assert S3('dear-liza').get_key('with/straw.dear.pdf') == {
            "path": "with/straw.dear.pdf",
            "filename": "straw.dear",
            "ext": "pdf",
            "size": 12,
            "last_modified": "2005-04-03T02:01:00.000000Z",
        }

    def test_get_key_weird_file(self, bucket_with_weird_file):
        assert S3('dear-liza').get_key('.!!!.dear.pdf') == {
            "ext": "pdf",
            "filename": ".!!!.dear",
            "last_modified": bucket_with_weird_file["expected_returned_timestamp"],
            "path": ".!!!.dear.pdf",
            "size": 26,
        }

    def test_get_nonexistent_key(self, bucket_with_file):
        assert S3('dear-liza').get_key('with/sarcasm.dear.pdf') is None

    def test_delete_key(self, bucket_with_file):
        S3('dear-liza').delete_key('with/straw.dear.pdf')

        assert not list(bucket_with_file.objects.all())

    def test_list_files(self, bucket_with_multiple_files):
        # we want ordering to be irrelevant here, so normalizing...
        def sortkey(f):
            return f["path"]
        assert sorted(S3("dear-liza").list(), key=sortkey) == sorted((
            {
                "path": "with/A0/paper.dear.odt",
                "filename": "paper.dear",
                "ext": "odt",
                "size": 8,
            },
            {
                "path": "with/A1/paper.dear.odt",
                "filename": "paper.dear",
                "ext": "odt",
                "size": 16,
            },
            {
                "path": "with/A2/paper.dear.odt",
                "filename": "paper.dear",
                "ext": "odt",
                "size": 24,
            },
            {
                "path": "with/A3/paper.dear.odt",
                "filename": "paper.dear",
                "ext": "odt",
                "size": 32,
            },
            {
                "path": "with/A4/paper.dear.odt",
                "filename": "paper.dear",
                "ext": "odt",
                "size": 40,
            },
        ), key=sortkey)

    def test_list_files_order_by_last_modified(self, bucket_with_multiple_files):
        assert S3("dear-liza").list(load_timestamps=True) == [
            {
                "path": "with/A3/paper.dear.odt",
                "filename": "paper.dear",
                "ext": "odt",
                "size": 32,
                "last_modified": "2014-09-30T00:00:00.000000Z",
            },
            {
                "path": "with/A0/paper.dear.odt",
                "filename": "paper.dear",
                "ext": "odt",
                "size": 8,
                "last_modified": "2014-10-01T00:00:00.000000Z",
            },
            {
                "path": "with/A1/paper.dear.odt",
                "filename": "paper.dear",
                "ext": "odt",
                "size": 16,
                "last_modified": "2014-10-12T00:00:00.000000Z",
            },
            {
                "path": "with/A4/paper.dear.odt",
                "filename": "paper.dear",
                "ext": "odt",
                "size": 40,
                "last_modified": "2014-10-17T00:00:00.000000Z",
            },
            {
                "path": "with/A2/paper.dear.odt",
                "filename": "paper.dear",
                "ext": "odt",
                "size": 24,
                "last_modified": "2014-10-23T00:00:00.000000Z",
            },
        ]

    @pytest.mark.parametrize("path,expected_path,expected_ct,expected_filename,expected_ext", (
        (
            "/with/epoxy.dear.jpeg",
            "with/epoxy.dear.jpeg",
            "image/jpeg",
            "epoxy.dear",
            "jpeg",
        ),
        (
            "with/epoxy.dear.pdf",
            "with/epoxy.dear.pdf",
            "application/pdf",
            "epoxy.dear",
            "pdf",
        ),
        (
            u"with/\u00a3.dear.odt",
            u"with/\u00a3.dear.odt",
            "application/vnd.oasis.opendocument.text",
            u"\u00a3.dear",
            "odt",
        ),
    ))
    @pytest.mark.parametrize("timestamp,expected_timestamp", (
        (None, "2016-10-02T00:00:00.000000Z",),  # the frozen "now" time
        (datetime.datetime(2015, 4, 3, 2, 1), "2015-04-03T02:01:00.000000Z",),
    ))
    @pytest.mark.parametrize("download_filename,expected_cd", (
        (None, None,),
        ("blah.jpg", 'attachment; filename="blah.jpg"',),
        (u"liza\u2019s.jpg", 'attachment; filename="lizas.jpg"',),
    ))
    @freeze_time('2016-10-02')
    def test_save_file(
        self, empty_bucket, path, expected_path, expected_ct, expected_filename, expected_ext, timestamp,
        expected_timestamp, download_filename, expected_cd
    ):
        returned_key_dict = S3("dear-liza").save(
            path,
            file_=BytesIO(b"one two three"),
            timestamp=timestamp,
            download_filename=download_filename,
        )

        assert returned_key_dict == {
            "path": expected_path,
            "filename": expected_filename,
            "ext": expected_ext,
            "last_modified": expected_timestamp,
            "size": 13,
        }

        summary_list = list(empty_bucket.objects.all())
        assert len(summary_list) == 1
        assert summary_list[0].key == expected_path
        obj0 = summary_list[0].Object()
        assert obj0.metadata == {
            "timestamp": expected_timestamp,
        }
        assert obj0.content_disposition == expected_cd
        assert obj0.get()["Body"].read() == b"one two three"
        if sys.version_info < (3, 0):
            # moto currently has a py3 bug which makes this fail - the fix not yet upstream - perhaps next time you come
            # across this message try updating moto to the latest version and see if this works
            assert obj0.content_type == expected_ct

    @freeze_time('2014-10-20')
    def test_save_existing_file(self, bucket_with_file):
        returned_key_dict = S3("dear-liza").save(
            "with/straw.dear.pdf",
            file_=BytesIO(b"significantly longer contents than before"),
            download_filename="significantly_different.pdf",
        )

        assert returned_key_dict == {
            "path": "with/straw.dear.pdf",
            "filename": "straw.dear",
            "ext": "pdf",
            "last_modified": "2014-10-20T00:00:00.000000Z",
            "size": 41,
        }

        summary_list = list(bucket_with_file.objects.all())
        assert len(summary_list) == 1
        assert summary_list[0].key == "with/straw.dear.pdf"
        obj0 = summary_list[0].Object()
        assert obj0.metadata == {
            "timestamp": "2014-10-20T00:00:00.000000Z",
        }
        assert obj0.content_disposition == 'attachment; filename="significantly_different.pdf"'
        assert obj0.get()["Body"].read() == b"significantly longer contents than before"
        if sys.version_info < (3, 0):
            # moto currently has a py3 bug which makes this fail - the fix not yet upstream - perhaps next time you come
            # across this message try updating moto to the latest version and see if this works
            assert obj0.content_type == "application/pdf"


def test_get_file_size_binary_file():
    test_file = BytesIO(b"*" * 5399999)
    # put fd somewhere interesting
    test_file.seek(234)

    assert get_file_size(test_file) == 5399999
    assert test_file.tell() == 234


@pytest.mark.skipif(sys.version_info < (3, 0), reason="Only relevant to Py3")
def test_get_file_size_text_file():
    from io import TextIOWrapper
    test_inner_file = BytesIO()
    test_file = TextIOWrapper(test_inner_file, encoding="utf-8")
    test_file.write(u"\u0001F3A9 " * 123)
    test_file.seek(0)
    # read 9 *unicode chars* to advance fd to somewhere interesting
    test_file.read(9)

    previous_pos = test_file.tell()

    assert get_file_size(test_file) == 738
    assert test_file.tell() == previous_pos
