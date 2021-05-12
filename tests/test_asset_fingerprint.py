# coding=utf-8
from unittest import mock

from dmutils.asset_fingerprint import AssetFingerprinter


@mock.patch(
    'dmutils.asset_fingerprint.AssetFingerprinter.get_asset_file_contents'
)
class TestAssetFingerprint(object):
    def test_url_format(self, get_file_content_mock):
        get_file_content_mock.return_value = """
            body {
                font-family: nta;
            }
        """
        asset_fingerprinter = AssetFingerprinter(
            asset_root='/suppliers/static/'
        )
        assert (
            asset_fingerprinter.get_url('application.css') ==
            '/suppliers/static/application.css?418e6f4a6cdf1142e45c072ed3e1c90a'  # noqa
        )
        assert (
            asset_fingerprinter.get_url('application-ie6.css') ==
            '/suppliers/static/application-ie6.css?418e6f4a6cdf1142e45c072ed3e1c90a'  # noqa
        )

    def test_building_file_path(self, get_file_content_mock):
        get_file_content_mock.return_value = """
            document.write('Hello world!');
        """
        fingerprinter = AssetFingerprinter()
        fingerprinter.get_url('javascripts/application.js')
        fingerprinter.get_asset_file_contents.assert_called_with(
            'app/static/javascripts/application.js'
        )

    def test_hashes_are_consistent(self, get_file_content_mock):
        get_file_content_mock.return_value = """
            body {
                font-family: nta;
            }
        """
        asset_fingerprinter = AssetFingerprinter()
        assert (
            asset_fingerprinter.get_asset_fingerprint('application.css') ==
            asset_fingerprinter.get_asset_fingerprint('same_contents.css')
        )

    def test_hashes_are_different_for_different_files(
        self, get_file_content_mock
    ):
        asset_fingerprinter = AssetFingerprinter()
        get_file_content_mock.return_value = """
            body {
                font-family: nta;
            }
        """
        css_hash = asset_fingerprinter.get_asset_fingerprint('application.css')
        get_file_content_mock.return_value = """
            document.write('Hello world!');
        """
        js_hash = asset_fingerprinter.get_asset_fingerprint('application.js')
        assert (
            js_hash != css_hash
        )

    def test_hash_gets_cached(self, get_file_content_mock):
        get_file_content_mock.return_value = """
            body {
                font-family: nta;
            }
        """
        fingerprinter = AssetFingerprinter()
        assert (
            fingerprinter.get_url('application.css') ==
            '/static/application.css?418e6f4a6cdf1142e45c072ed3e1c90a'
        )
        fingerprinter._cache[
            'application.css'
        ] = 'a1a1a1'
        assert (
            fingerprinter.get_url('application.css') ==
            'a1a1a1'
        )
        fingerprinter.get_asset_file_contents.assert_called_once_with(
            'app/static/application.css'
        )


class TestAssetFingerprintWithUnicode(object):
    def test_can_read_self(self):
        """This string must contain Ralph’s apostrophe. We then try to load this file with the asset fingerprinter."""
        AssetFingerprinter(filesystem_path='tests/').get_url('test_asset_fingerprint.py')
