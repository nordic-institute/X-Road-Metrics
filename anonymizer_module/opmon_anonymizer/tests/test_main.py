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

import pytest

import opmon_anonymizer.main as main


@pytest.mark.parametrize(
    'only_opendata, opendata_anonymizer_called, anonymizer_called', [
        ('--only_opendata', True, False),
        ('', False, True)
    ]
)
def test_main_anonymizers_called(mocker, only_opendata, opendata_anonymizer_called, anonymizer_called):
    mocker.patch('opmon_anonymizer.main.run_opendata_anonymizer')
    mocker.patch('opmon_anonymizer.main.run_anonymizer')
    mocker.patch('opmon_anonymizer.main.logger_manager.LoggerManager')
    mocker.patch('opmon_anonymizer.main.OpmonSettingsManager')

    sys_args = ['test_program_name', '--profile', 'TEST']
    if only_opendata:
        sys_args.append('--only_opendata')
    mocker.patch('sys.argv', sys_args)

    main.main()
    assert main.run_opendata_anonymizer.called == opendata_anonymizer_called
    assert main.run_anonymizer.called == anonymizer_called
