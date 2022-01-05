from freezegun import freeze_time

from dmutils.framework_notification import dos6_live


@freeze_time('2022-01-04')
def test_should_be_false_if_before_go_live_date():
    assert dos6_live({}) is False


@freeze_time('2022-01-14')
def test_should_be_true_if_on_go_live_date():
    assert dos6_live({}) is True


@freeze_time('2022-01-15')
def test_should_be_true_if_after_go_live_date():
    assert dos6_live({}) is True


@freeze_time('2022-01-04')
def test_should_be_true_if_before_date_and_go_live_param():
    assert dos6_live({'show_dos6_live': 'true'}) is True


@freeze_time('2022-01-04')
def test_should_be_false_if_before_date_and_not_go_live_param():
    assert dos6_live({'show_gcloud13_live': 'true'}) is False
