#
# The MIT License 
# Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
# Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
#  
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to deal 
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions: 
#  
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software. 
#  
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN 
# THE SOFTWARE.
#

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
