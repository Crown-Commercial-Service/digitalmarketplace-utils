from unittest.mock import patch

import pytest

from dmutils.env_helpers import get_api_endpoint_from_stage, get_assets_endpoint_from_stage, get_web_url_from_stage


class TestGetAPIEndpointFromStage:

    @pytest.mark.parametrize("stage", ["local", "dev", "development"])
    def test_get_api_endpoint_for_dev_environments(self, stage):
        with patch.dict("os.environ", {}):
            assert get_api_endpoint_from_stage(stage) == "http://localhost:5000"

        with patch.dict("os.environ", {"DM_API_PORT": "9000"}):
            assert get_api_endpoint_from_stage(stage) == "http://localhost:9000"

    @pytest.mark.parametrize(
        'stage, expected_result',
        [
            ('preview', 'https://api.preview.marketplace.team'),
            ('staging', 'https://api.staging.marketplace.team'),
            ('production', 'https://api.digitalmarketplace.service.gov.uk'),
            ('nft', 'https://api.nft.marketplace.team')
        ]
    )
    def test_get_api_endpoint_for_non_dev_environments(self, stage, expected_result):
        assert get_api_endpoint_from_stage(stage) == expected_result

    @pytest.mark.parametrize("stage", ["local", "dev", "development"])
    def test_get_search_api_endpoint_for_dev_environments(self, stage):
        with patch.dict("os.environ", {}):
            assert get_api_endpoint_from_stage(stage, app="search-api") == "http://localhost:5009"

        with patch.dict("os.environ", {"DM_SEARCH_API_PORT": "9001"}):
            assert get_api_endpoint_from_stage(stage, app="search-api") == "http://localhost:9001"

    @pytest.mark.parametrize(
        'stage, expected_result',
        [
            ('preview', 'https://search-api.preview.marketplace.team'),
            ('staging', 'https://search-api.staging.marketplace.team'),
            ('production', 'https://search-api.digitalmarketplace.service.gov.uk'),
            ('nft', 'https://search-api.nft.marketplace.team')
        ]
    )
    def test_get_search_api_endpoint_for_non_dev_environments(self, stage, expected_result):
        assert get_api_endpoint_from_stage(stage, app='search-api') == expected_result

    @pytest.mark.parametrize('stage', ['local', 'dev', 'development'])
    def test_get_antivirus_api_endpoint_for_dev_environments(self, stage):
        assert get_api_endpoint_from_stage(stage, app='antivirus-api') == 'http://localhost:5008'

    @pytest.mark.parametrize(
        'stage, expected_result',
        [
            ('preview', 'https://antivirus-api.preview.marketplace.team'),
            ('staging', 'https://antivirus-api.staging.marketplace.team'),
            ('production', 'https://antivirus-api.digitalmarketplace.service.gov.uk'),
            ('nft', 'https://antivirus-api.nft.marketplace.team')
        ]
    )
    def test_get_antivirus_api_endpoint_for_non_dev_environments(self, stage, expected_result):
        assert get_api_endpoint_from_stage(stage, app='antivirus-api') == expected_result


class TestGetWebUrlFromStage:

    @pytest.mark.parametrize('stage', ['local', 'dev', 'development'])
    def test_get_web_url_for_dev_environments(self, stage):
        assert get_web_url_from_stage(stage) == 'http://localhost'

    @pytest.mark.parametrize(
        'stage, expected_result',
        [
            ('preview', 'https://www.preview.marketplace.team'),
            ('staging', 'https://www.staging.marketplace.team'),
            ('production', 'https://www.digitalmarketplace.service.gov.uk'),
            ('nft', 'https://www.nft.marketplace.team')
        ]
    )
    def test_get_api_endpoint_for_non_dev_environments(self, stage, expected_result):
        assert get_web_url_from_stage(stage) == expected_result


class TestGetAssetsEndpointFromStage:

    @pytest.mark.parametrize('stage', ['local', 'dev', 'development'])
    def test_get_assets_endpoint_raises_error_for_dev_environments(self, stage):
        with pytest.raises(NotImplementedError):
            get_assets_endpoint_from_stage(stage)

    @pytest.mark.parametrize(
        'stage, expected_result',
        [
            ('preview', 'https://assets.preview.marketplace.team'),
            ('staging', 'https://assets.staging.marketplace.team'),
            ('production', 'https://assets.digitalmarketplace.service.gov.uk'),
            ('nft', 'https://assets.nft.marketplace.team')
        ]
    )
    def test_get_assets_endpoint_for_non_dev_environments(self, stage, expected_result):
        assert get_assets_endpoint_from_stage(stage) == expected_result
