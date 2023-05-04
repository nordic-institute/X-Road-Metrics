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
