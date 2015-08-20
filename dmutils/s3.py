import os
import boto
import boto.exception
import datetime
import mimetypes

from boto.exception import S3ResponseError  # noqa


class S3(object):
    def __init__(self, bucket_name=None, host='s3-eu-west-1.amazonaws.com'):
        conn = boto.connect_s3(host=host)

        self.bucket_name = bucket_name
        self.bucket = conn.get_bucket(bucket_name)

    def save(self, path, file, acl='public-read', move_prefix=None):
        path = path.lstrip('/')

        self._move_existing(path, move_prefix)

        key = self.bucket.new_key(path)
        key.set_contents_from_file(
            file,
            headers={'Content-Type': self._get_mimetype(key.name)}
        )
        key.set_acl(acl)
        return key

    def get_signed_url(self, path, expires_in=30):
        """Create a signed S3 document URL

        :param path: S3 object path within the bucket
        :param expires_in: how long the generated URL is valid
                           for, in seconds

        :return: signed URL or ``None`` if object was not found

        """

        key = self.bucket.get_key(path)
        if key:
            return key.generate_url(expires_in)

    def list(self, prefix='', delimiter=''):
        """
        return a list of file keys (ordered by last_modified date) from an s3 bucket

        Prefix & Delimiter: http://docs.aws.amazon.com/AmazonS3/latest/dev/ListingKeysHierarchy.html
        :param prefix:      filter by files whose names begin with the prefix
        :param delimiter:   filter out files whose names contain the delimiter
        :return: list
        """
        # http://boto.readthedocs.org/en/latest/ref/s3.html#boto.s3.bucket.Bucket.list
        list_of_keys = self.bucket.list(prefix, delimiter)
        return [
            self._format_key(key)
            for key in sorted(list_of_keys, key=lambda key: key.last_modified)
            if not (key.size == 0 and key.name[-1] == '/')
        ]

    def _format_key(self, key):
        """
        transform a boto s3 Key object into a (simpler) dict

        :param key: http://boto.readthedocs.org/en/latest/ref/s3.html#boto.s3.key.Key
        :return:    dict
        """
        filename, ext = os.path.splitext(os.path.basename(key.name))

        return {
            'path': key.name,
            'filename': filename,
            'ext': ext[1:],
            'last_modified': key.last_modified,
            'size': key.size
        }

    def _move_existing(self, existing_path, move_prefix=None):
        if move_prefix is None:
            move_prefix = default_move_prefix()

        if self.bucket.get_key(existing_path):
            path, name = os.path.split(existing_path)
            self.bucket.copy_key(
                os.path.join(path, '{}-{}'.format(move_prefix, name)),
                self.bucket_name,
                existing_path
            )

    def _get_mimetype(self, filename):
        mimetype, _ = mimetypes.guess_type(filename)
        return mimetype


def default_move_prefix():
    return datetime.datetime.utcnow().isoformat()
