# coding: utf-8
import datetime
import mock

import dmutils.dates as dates_package


class TestPublishingDates():
    def test_get_publishing_dates_formats_time(self):
        with mock.patch('dmutils.dates.datetime') as mock_date:
            mock_date.utcnow.return_value = datetime.datetime(2015, 5, 22, 20, 39, 39, 417900)
            brief = {
                'requirementsLength': '1 week',
            }
            assert dates_package.datetime.utcnow() == datetime.datetime(2015, 5, 22, 20, 39, 39, 417900)
            assert dates_package.get_publishing_dates(brief)['closing_time'] == '11:59 pm'

    def test_get_publishing_dates_for_one_week_briefs_are_correct_if_published_on_a_monday(self):
        with mock.patch('dmutils.dates.datetime') as mock_date:
            mock_date.utcnow.return_value = datetime.datetime(2016, 7, 4, 15, 21, 39, 417900)
            brief = {
                'requirementsLength': '1 week',
            }

            dates = dates_package.get_publishing_dates(brief)

            assert dates['questions_close'] == datetime.datetime(2016, 7, 6, 23, 59, 59)
            assert dates['answers_close'] == datetime.datetime(2016, 7, 8, 23, 59, 59)
            assert dates['closing_date'] == datetime.datetime(2016, 7, 11, 23, 59, 59)

    def test_get_publishing_dates_for_one_week_briefs_are_correct_if_published_on_a_tuesday(self):
        with mock.patch('dmutils.dates.datetime') as mock_date:
            mock_date.utcnow.return_value = datetime.datetime(2016, 7, 5, 15, 21, 39, 417900)
            brief = {
                'requirementsLength': '1 week',
            }

            dates = dates_package.get_publishing_dates(brief)

            assert dates['questions_close'] == datetime.datetime(2016, 7, 7, 23, 59, 59)
            assert dates['answers_close'] == datetime.datetime(2016, 7, 11, 23, 59, 59)
            assert dates['closing_date'] == datetime.datetime(2016, 7, 12, 23, 59, 59)

    def test_get_publishing_dates_for_one_week_briefs_are_correct_if_published_on_a_wednesday(self):
        with mock.patch('dmutils.dates.datetime') as mock_date:
            mock_date.utcnow.return_value = datetime.datetime(2016, 7, 6, 15, 21, 39, 417900)
            brief = {
                'requirementsLength': '1 week',
            }

            dates = dates_package.get_publishing_dates(brief)

            assert dates['questions_close'] == datetime.datetime(2016, 7, 8, 23, 59, 59)
            assert dates['answers_close'] == datetime.datetime(2016, 7, 12, 23, 59, 59)
            assert dates['closing_date'] == datetime.datetime(2016, 7, 13, 23, 59, 59)

    def test_get_publishing_dates_for_one_week_briefs_are_correct_if_published_on_a_thursday(self):
        with mock.patch('dmutils.dates.datetime') as mock_date:
            mock_date.utcnow.return_value = datetime.datetime(2016, 7, 7, 15, 21, 39, 417900)
            brief = {
                'requirementsLength': '1 week',
            }

            dates = dates_package.get_publishing_dates(brief)

            assert dates['questions_close'] == datetime.datetime(2016, 7, 11, 23, 59, 59)
            assert dates['answers_close'] == datetime.datetime(2016, 7, 13, 23, 59, 59)
            assert dates['closing_date'] == datetime.datetime(2016, 7, 14, 23, 59, 59)

    def test_get_publishing_dates_for_one_week_briefs_are_correct_if_published_on_a_friday(self):
        with mock.patch('dmutils.dates.datetime') as mock_date:
            mock_date.utcnow.return_value = datetime.datetime(2016, 7, 8, 15, 21, 39, 417900)
            brief = {
                'requirementsLength': '1 week',
                'lotSlug': 'digital-specialists'
            }

            dates = dates_package.get_publishing_dates(brief)

            assert dates['questions_close'] == datetime.datetime(2016, 7, 12, 23, 59, 59)
            assert dates['answers_close'] == datetime.datetime(2016, 7, 14, 23, 59, 59)
            assert dates['closing_date'] == datetime.datetime(2016, 7, 15, 23, 59, 59)

    def test_get_publishing_dates_for_one_week_briefs_are_correct_if_published_on_a_saturday(self):
        with mock.patch('dmutils.dates.datetime') as mock_date:
            mock_date.utcnow.return_value = datetime.datetime(2016, 7, 9, 15, 21, 39, 417900)
            brief = {
                'requirementsLength': '1 week',
            }

            dates = dates_package.get_publishing_dates(brief)

            assert dates['questions_close'] == datetime.datetime(2016, 7, 12, 23, 59, 59)
            assert dates['answers_close'] == datetime.datetime(2016, 7, 15, 23, 59, 59)
            assert dates['closing_date'] == datetime.datetime(2016, 7, 16, 23, 59, 59)

    def test_get_publishing_dates_for_one_week_briefs_are_correct_if_published_on_a_sunday(self):
        with mock.patch('dmutils.dates.datetime') as mock_date:
            mock_date.utcnow.return_value = datetime.datetime(2016, 7, 10, 15, 21, 39, 417900)
            brief = {
                'requirementsLength': '1 week',
            }

            dates = dates_package.get_publishing_dates(brief)

            assert dates['questions_close'] == datetime.datetime(2016, 7, 12, 23, 59, 59)
            assert dates['answers_close'] == datetime.datetime(2016, 7, 15, 23, 59, 59)
            assert dates['closing_date'] == datetime.datetime(2016, 7, 17, 23, 59, 59)

    def test_get_publishing_dates_for_two_week_briefs_are_correct_if_published_on_a_monday(self):
        with mock.patch('dmutils.dates.datetime') as mock_date:
            mock_date.utcnow.return_value = datetime.datetime(2016, 7, 4, 15, 21, 39, 417900)
            brief = {
                'requirementsLength': '2 weeks',
            }

            dates = dates_package.get_publishing_dates(brief)

            assert dates['questions_close'] == datetime.datetime(2016, 7, 11, 23, 59, 59)
            assert dates['answers_close'] == datetime.datetime(2016, 7, 15, 23, 59, 59)
            assert dates['closing_date'] == datetime.datetime(2016, 7, 18, 23, 59, 59)

    def test_get_publishing_dates_for_two_week_briefs_are_correct_if_published_on_a_tuesday(self):
        with mock.patch('dmutils.dates.datetime') as mock_date:
            mock_date.utcnow.return_value = datetime.datetime(2016, 7, 5, 15, 21, 39, 417900)
            brief = {
                'requirementsLength': '2 weeks',
            }

            dates = dates_package.get_publishing_dates(brief)

            assert dates['questions_close'] == datetime.datetime(2016, 7, 12, 23, 59, 59)
            assert dates['answers_close'] == datetime.datetime(2016, 7, 18, 23, 59, 59)
            assert dates['closing_date'] == datetime.datetime(2016, 7, 19, 23, 59, 59)

    def test_get_publishing_dates_for_two_week_briefs_are_correct_if_published_on_a_wednesday(self):
        with mock.patch('dmutils.dates.datetime') as mock_date:
            mock_date.utcnow.return_value = datetime.datetime(2016, 7, 6, 15, 21, 39, 417900)
            brief = {
                'requirementsLength': '2 weeks',
            }

            dates = dates_package.get_publishing_dates(brief)

            assert dates['questions_close'] == datetime.datetime(2016, 7, 13, 23, 59, 59)
            assert dates['answers_close'] == datetime.datetime(2016, 7, 19, 23, 59, 59)
            assert dates['closing_date'] == datetime.datetime(2016, 7, 20, 23, 59, 59)

    def test_get_publishing_dates_for_two_week_briefs_are_correct_if_published_on_a_thursday(self):
        with mock.patch('dmutils.dates.datetime') as mock_date:
            mock_date.utcnow.return_value = datetime.datetime(2016, 7, 7, 15, 21, 39, 417900)
            brief = {
                'requirementsLength': '2 weeks',
            }

            dates = dates_package.get_publishing_dates(brief)

            assert dates['questions_close'] == datetime.datetime(2016, 7, 14, 23, 59, 59)
            assert dates['answers_close'] == datetime.datetime(2016, 7, 20, 23, 59, 59)
            assert dates['closing_date'] == datetime.datetime(2016, 7, 21, 23, 59, 59)

    def test_get_publishing_dates_for_two_week_briefs_are_correct_if_published_on_a_friday(self):
        with mock.patch('dmutils.dates.datetime') as mock_date:
            mock_date.utcnow.return_value = datetime.datetime(2016, 7, 8, 15, 21, 39, 417900)
            brief = {
                'requirementsLength': '2 weeks',
            }

            dates = dates_package.get_publishing_dates(brief)

            assert dates['questions_close'] == datetime.datetime(2016, 7, 15, 23, 59, 59)
            assert dates['answers_close'] == datetime.datetime(2016, 7, 21, 23, 59, 59)
            assert dates['closing_date'] == datetime.datetime(2016, 7, 22, 23, 59, 59)

    def test_get_publishing_dates_for_two_week_briefs_are_correct_if_published_on_a_saturday(self):
        with mock.patch('dmutils.dates.datetime') as mock_date:
            mock_date.utcnow.return_value = datetime.datetime(2016, 7, 9, 15, 21, 39, 417900)
            brief = {
                'requirementsLength': '2 weeks',
            }

            dates = dates_package.get_publishing_dates(brief)

            assert dates['questions_close'] == datetime.datetime(2016, 7, 15, 23, 59, 59)
            assert dates['answers_close'] == datetime.datetime(2016, 7, 22, 23, 59, 59)
            assert dates['closing_date'] == datetime.datetime(2016, 7, 23, 23, 59, 59)

    def test_get_publishing_dates_for_two_week_briefs_are_correct_if_published_on_a_sunday(self):
        with mock.patch('dmutils.dates.datetime') as mock_date:
            mock_date.utcnow.return_value = datetime.datetime(2016, 7, 10, 15, 21, 39, 417900)
            brief = {
                'requirementsLength': '2 weeks',
            }

            dates = dates_package.get_publishing_dates(brief)

            assert dates['questions_close'] == datetime.datetime(2016, 7, 15, 23, 59, 59)
            assert dates['answers_close'] == datetime.datetime(2016, 7, 22, 23, 59, 59)
            assert dates['closing_date'] == datetime.datetime(2016, 7, 24, 23, 59, 59)

    def test_get_publishing_dates_returns_correct_dates_if_brief_is_published_with_no_requirementLength(self):
        brief = {
            'publishedAt': u'2016-01-04T12:00:00.00000Z',
        }

        dates = dates_package.get_publishing_dates(brief)

        assert dates['questions_close'] == datetime.datetime(2016, 1, 11, 23, 59, 59)
        assert dates['answers_close'] == datetime.datetime(2016, 1, 15, 23, 59, 59)
        assert dates['closing_date'] == datetime.datetime(2016, 1, 18, 23, 59, 59)

    def test_get_publishing_dates_returns_correct_dates_if_brief_is_published_with_1_week_requirementsLength(self):
        brief = {
            'publishedAt': u'2016-01-04T12:00:00.00000Z',
            'requirementsLength': '1 week'
        }

        dates = dates_package.get_publishing_dates(brief)

        assert dates['questions_close'] == datetime.datetime(2016, 1, 6, 23, 59, 59)
        assert dates['answers_close'] == datetime.datetime(2016, 1, 8, 23, 59, 59)
        assert dates['closing_date'] == datetime.datetime(2016, 1, 11, 23, 59, 59)

    def test_get_publishing_dates_returns_correct_dates_if_brief_is_published_with_2_week_requirementsLength(self):
        brief = {
            'publishedAt': u'2016-01-04T12:00:00.00000Z',
            'requirementsLength': '2 weeks'
        }

        dates = dates_package.get_publishing_dates(brief)

        assert dates['questions_close'] == datetime.datetime(2016, 1, 11, 23, 59, 59)
        assert dates['answers_close'] == datetime.datetime(2016, 1, 15, 23, 59, 59)
        assert dates['closing_date'] == datetime.datetime(2016, 1, 18, 23, 59, 59)

    def test_get_publishing_dates_returns_correct_dates_if_published_at_key_is_a_date_object(self):
        brief = {
            'publishedAt': datetime.datetime(2016, 1, 4, 12, 0, 0),
        }

        dates = dates_package.get_publishing_dates(brief)

        assert dates['questions_close'] == datetime.datetime(2016, 1, 11, 23, 59, 59)
        assert dates['answers_close'] == datetime.datetime(2016, 1, 15, 23, 59, 59)
        assert dates['closing_date'] == datetime.datetime(2016, 1, 18, 23, 59, 59)


def test_update_framework_with_formatted_dates():
    framework = {
        'clarificationsCloseAtUTC': '2000-01-01T12:00:00.000000Z',
        'clarificationsPublishAtUTC': '2000-01-02T12:00:00.000000Z',
        'applicationsCloseAtUTC': '2000-01-03T17:00:00.000000Z',
        'intentionToAwardAtUTC': '2000-01-04T12:00:00.000000Z',
        'frameworkLiveAtUTC': '2000-01-05T12:00:00.000000Z',
    }

    dates_package.update_framework_with_formatted_dates(framework)

    assert framework == {
        'clarificationsCloseAtUTC': '2000-01-01T12:00:00.000000Z',
        'clarificationsPublishAtUTC': '2000-01-02T12:00:00.000000Z',
        'applicationsCloseAtUTC': '2000-01-03T17:00:00.000000Z',
        'intentionToAwardAtUTC': '2000-01-04T12:00:00.000000Z',
        'frameworkLiveAtUTC': '2000-01-05T12:00:00.000000Z',
        'clarificationsCloseAt': '12pm GMT, Saturday 1 January 2000',
        'clarificationsPublishAt': '12pm GMT, Sunday 2 January 2000',
        'applicationsCloseAt': '5pm GMT, Monday 3 January 2000',
        'intentionToAwardAt': 'Tuesday 4 January 2000',
        'frameworkLiveAt': 'Wednesday 5 January 2000',
    }
