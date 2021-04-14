import datetime

import pytest
from opmon_analyzer.train_or_update_historic_averages_models import get_first_model_train_time


def test_get_first_model_train_time(mocker):
    settings = {
        'analyzer': {
            'training-period': {
                'length': 3,
                'unit': 'MONTHS'
            }
        }
    }

    training_period = settings['analyzer']['training-period']

    t1 = datetime.datetime(2021, 4, 13, 12, 0, 0)
    assert get_first_model_train_time(settings, t1, mocker.Mock()) == datetime.datetime(2021, 1, 13, 12, 0, 0)

    training_period['unit'] = 'WEEKS'
    training_period['length'] = 51
    assert get_first_model_train_time(settings, t1, mocker.Mock()) == datetime.datetime(2020, 4, 21, 12, 0, 0)

    training_period['unit'] = 'DAYS'
    training_period['length'] = 32
    assert get_first_model_train_time(settings, t1, mocker.Mock()) == datetime.datetime(2021, 3, 12, 12, 0)

    training_period['unit'] = 'POTATOES'
    with pytest.raises(ValueError) as error:
        get_first_model_train_time(settings, t1, mocker.Mock())
    assert str(error.value) == "Invalid unit for training-period."
