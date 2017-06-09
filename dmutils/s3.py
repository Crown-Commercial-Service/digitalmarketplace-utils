from __future__ import absolute_import
import os
import boto3
import datetime
import mimetypes
import logging
from dateutil.parser import parse as parse_time
from six import text_type

# a bit of a lie here - retains compatibility with consumers that were importing boto2's S3ResponseError from here. this
# is the exception boto3 raises in (mostly) the same situations.
from botocore.exceptions import ClientError as S3ResponseError

from .formats import DATETIME_FORMAT

logger = logging.getLogger(__name__)

FILE_SIZE_LIMIT = 5400000  # approximately 5Mb

default_region = "eu-west-1"


class S3(object):
    def __init__(self, bucket_name, region_name=default_region):
        self._resource = boto3.resource("s3", region_name=region_name)
        self._bucket = self._resource.Bucket(bucket_name)

    @property
    def bucket_name(self):
        return self._bucket.name

    def save(self, path, file_, acl='public-read', timestamp=None, download_filename=None,
             disposition_type='attachment'):
        """Save a file in an S3 bucket

        canned ACL list: https://docs.aws.amazon.com/AmazonS3/latest/dev/acl-overview.html#canned-acl

        :param path:              location in S3 bucket at which to save the file
        :param file_:             file object to be saved in S3
        :param acl:               S3 canned ACL
        :param timestamp:         Timestamp to set for this file rather than using utcnow
        :param download_filename: Suggested name for a browser to download, part of Content-Disposition header
        :param disposition_type:  Content-Disposition type - e.g. "attachment" or "inline"

        :return: S3 Key
        """
        path = self._normalize_path(path)
        timestamp = timestamp or datetime.datetime.utcnow()
        filesize = get_file_size(file_)

        obj = self._bucket.Object(path)
        extra_kwargs = {}
        if download_filename:
            extra_kwargs["ContentDisposition"] = u'{}; filename="{}"'.format(
                disposition_type,
                # boto/aws can't cope with unicode here, but wants the ultimate result as a `str` in py3, so doing this
                # to strip non-ascii chars..
                text_type(download_filename).encode("ascii", errors="ignore").decode(),
            )
        obj.put(
            ACL=acl,
            Body=file_,
            ContentType=self._get_mimetype(path),
            # using a custom "timestamp" field allows us to manually override it if necessary
            Metadata={"timestamp": timestamp.strftime(DATETIME_FORMAT)},
            **extra_kwargs
        )
        logger.info(
            "Uploaded file {filepath} of size {filesize} with acl {fileacl}",
            extra={
                "filepath": path,
                "filesize": filesize,
                "fileacl": acl,
            },
        )

        return self._format_key(obj)

    @staticmethod
    def _normalize_path(path):
        return path.lstrip('/')

    def path_exists(self, path):
        path = self._normalize_path(path)
        return self._get_key(path) is not None

    def get_signed_url(self, path, expires_in=30):
        """Create a signed S3 document URL

        :param path: S3 object path within the bucket
        :param expires_in: how long the generated URL is valid
                           for, in seconds

        :return: signed URL or ``None`` if object was not found

        """
        path = self._normalize_path(path)
        if self.path_exists(path):
            return self._resource.meta.client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self._bucket.name,
                    "Key": path,
                },
                ExpiresIn=expires_in,
            )

    def _get_key(self, path):
        path = self._normalize_path(path)
        try:
            obj = self._bucket.Object(path)
            obj.load()
        except S3ResponseError:
            return None
        return obj

    def get_key(self, path):
        path = self._normalize_path(path)
        obj = self._get_key(path)
        return obj and self._format_key(obj)

    def delete_key(self, path):
        path = self._normalize_path(path)
        self._bucket.Object(path).delete()

    def list(self, prefix='', delimiter='', load_timestamps=False):
        """
        return a list of file keys (ordered by last_modified date if load_timestamps is True) from an s3 bucket

        Prefix & Delimiter: http://docs.aws.amazon.com/AmazonS3/latest/dev/ListingKeysHierarchy.html
        :param prefix:          filter by files whose names begin with the prefix
        :param delimiter:       filter out files whose names contain the delimiter
        :param load_timestamps: by default custom timestamps are not loaded as they require an extra API call.
                                if you need to show the timestamp set this to True.
        :return: list
        """
        prefix = self._normalize_path(prefix)
        return sorted((
            self._format_key(obj_s, with_timestamp=load_timestamps)
            for obj_s in self._bucket.objects.filter(Prefix=prefix, Delimiter=delimiter)
            if not (obj_s.size == 0 and obj_s.key[-1] == '/')
        ), key=lambda obj_s: (obj_s.get("last_modified") or "", obj_s["path"],))

    def _format_key(self, obj, with_timestamp=True):
        """
        Transform a boto3 s3 Object or ObjectSummary object into a (simpler, implementation-abstracted) dict

        :param obj:            either a boto3 s3 Object or ObjectSummary
        :param with_timestamp: by default our custom timestamps are not loaded as they require an extra API call.
                               if you need to show the timestamp set this to True.
        :return:    dict
        """
        filename, ext = os.path.splitext(os.path.basename(obj.key))

        if with_timestamp and hasattr(obj, "Object"):
            # obj is presumably an ObjectSummary, but we'll need an Object if we want the timestamp, which should get
            # auto-fetched when the attribute is accessed
            obj = obj.Object()

        keydict = {
            'path': obj.key,
            'filename': filename,
            'ext': ext[1:],
            # ObjectSummary has .size, Object has .content_length
            'size': obj.size if hasattr(obj, "size") else obj.content_length,
        }
        if with_timestamp:
            keydict["last_modified"] = (
                obj.metadata.get("timestamp") and parse_time(obj.metadata["timestamp"]).strftime(DATETIME_FORMAT)
            )

        return keydict

    @staticmethod
    def _get_mimetype(filename):
        mimetype, _ = mimetypes.guess_type(filename)
        return mimetype


def get_file_size(file_):
    if hasattr(file_, "buffer"):
        # presumably a TextIO object - we want to deal with things on a byte-level though...
        file_ = file_.buffer

    original_pos = file_.tell()
    file_.seek(0, 2)
    size = file_.tell()
    file_.seek(original_pos)
    # see it's like nothing happened, right?

    return size
