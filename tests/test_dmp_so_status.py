from freezegun import freeze_time

from dmutils.dmp_so_status import are_new_frameworks_live


@freeze_time('2022-03-08')
def test_should_be_false_if_before_go_live_date():
    assert are_new_frameworks_live({}) is False


@freeze_time('2022-03-09 12:00:01')
def test_should_be_true_if_on_go_live_date():
    assert are_new_frameworks_live({}) is True


@freeze_time('2022-03-10')
def test_should_be_true_if_after_go_live_date():
    assert are_new_frameworks_live({}) is True


@freeze_time('2022-03-08')
def test_should_be_true_if_before_date_and_go_live_param():
    assert are_new_frameworks_live({'show_dmp_so_banner': 'true'}) is True


@freeze_time('2022-03-08')
def test_should_be_false_if_before_date_and_not_go_live_param():
    assert are_new_frameworks_live({'show_dmp_1.0_banner': 'true'}) is False


@freeze_time('2022-05-18 15:00:01')
def test_should_be_false_after_g13_closes():
    assert are_new_frameworks_live({'show_dmp_1.0_banner': 'true'}) is False
