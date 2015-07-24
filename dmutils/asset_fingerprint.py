import hashlib


def get_asset_fingerprint(asset_file_path):
    """
        Get a unique hash for an asset file, so that it doesn't stay cached
        when it changes

        Usage:
        get('app/static/stylesheets/application.css')
    """
    return hashlib.md5().update(
        get_asset_file_contents(asset_file_path)
    ).hexdigest()


def get_asset_file_contents(asset_file_path):
    with open(asset_file_path, 'rb') as asset_file:
        contents = asset_file.read()
    return contents
