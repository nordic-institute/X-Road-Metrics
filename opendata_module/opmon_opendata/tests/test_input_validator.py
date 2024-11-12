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

from opmon_opendata.api.input_validator import OpenDataInputValidator


@pytest.fixture
def input_validator(mocker):
    postgres = mocker.Mock()
    postgres.get_column_names_and_types = lambda: [('foo', 'integer'), ('bar', 'date')]
    return OpenDataInputValidator(postgres, mocker.Mock())


def test_empty_date(input_validator):
    with pytest.raises(Exception, match=r'Missing "date" field.'):
        input_validator.load_and_validate_date('', '')

    with pytest.raises(Exception, match=r'Missing "date" field.'):
        input_validator.load_and_validate_date(None, None)


def test_wrong_date_format(input_validator):
    with pytest.raises(Exception, match=r'Date .* is not in required format YYYY-MM-DD.'):
        input_validator.load_and_validate_date('01-02-2003', '')

    with pytest.raises(Exception, match=r'Date .* is not in required format YYYY-MM-DD.'):
        input_validator.load_and_validate_date('SELECT * FROM', '')


def test_too_recent_date(input_validator):
    with pytest.raises(Exception, match=r'The latest available date is'):
        input_validator.load_and_validate_date(datetime.datetime.now().strftime('%Y-%m-%d'), datetime.timedelta(100))


def test_loading_date(input_validator):
    expected_date = datetime.datetime(year=1993, month=5, day=17)
    assert expected_date == input_validator.load_and_validate_date('1993-05-17', datetime.timedelta(1))


def test_no_columns(input_validator):
    assert 0 == len(input_validator.load_and_validate_columns('[]'))


def test_non_existent_columns(input_validator):
    with pytest.raises(Exception, match=r'Column "a" does not exist.'):
        input_validator.load_and_validate_columns(["a", "b", "c"])


def test_wrong_columns_format(input_validator):
    with pytest.raises(Exception, match=r'Unable to parse columns as a list of field names.'):
        input_validator.load_and_validate_columns('SELECT * FROM')

        with pytest.raises(Exception, match=r'Unable to parse columns as a list of field names.'):
            input_validator.load_and_validate_columns('{"a", "b"}')


def test_loading_columns(input_validator):
    assert ["foo", "bar"] == input_validator.load_and_validate_columns('["foo", "bar"]')


def test_no_order(input_validator):
    assert 0 == len(input_validator.load_and_validate_order_clauses('[]'))


def test_wrong_order_format(input_validator):
    with pytest.raises(Exception, match=r'Unable to parse order clauses as a list of objects'):
        input_validator.load_and_validate_order_clauses('SELECT * FROM')


def test_wrong_inner_order_data_types(input_validator):
    with pytest.raises(Exception, match=r'Every constraint must be with the schema'):
        input_validator.load_and_validate_order_clauses('[["a", "b"], ["c", "d"]]')


def test_missing_order_attributes(input_validator):
    with pytest.raises(Exception, match=r'Order clause at index 0 is missing "order" key.'):
        input_validator.load_and_validate_order_clauses('[{"column": "foo"}, {"order": "asc"}]')

    with pytest.raises(Exception, match=r'Order clause at index 1 is missing "column" key.'):
        input_validator.load_and_validate_order_clauses(
            '[{"column": "foo", "order": "desc"}, {"order": "asc"}]'
        )


def test_non_existent_column_in_order_clause(input_validator):
    with pytest.raises(Exception, match=r'Column "mystery" in order clause at index 0 does not exist.'):
        input_validator.load_and_validate_order_clauses('[{"column": "mystery", "order": "asc"}]')


def test_non_existent_orders(input_validator):
    with pytest.raises(Exception, match=r'Can not order data in ascii order in order clause at index 1.'):
        input_validator.load_and_validate_order_clauses(
            '[{"column": "foo", "order": "asc"}, {"column": "foo", "order": "ascii"}]'
        )


def test_loading_orders(input_validator):
    assert [{'column': 'foo', 'order': 'asc'}] == input_validator.load_and_validate_order_clauses(
        '[{"column": "foo", "order": "asc"}]'
    )


def test_no_constraints(input_validator):
    assert [] == input_validator.load_and_validate_constraints('[]')


def test_wrong_constraints_format(input_validator):
    with pytest.raises(Exception, match=r'Unable to parse constraints as a list of objects'):
        input_validator.load_and_validate_constraints('SELECT * FROM')


def test_missing_constraints_attribute(input_validator):
    with pytest.raises(Exception, match=r'Constraint at index 0 is missing "column" key.'):
        input_validator.load_and_validate_constraints('[{"operator": null, "value": null}]')

    with pytest.raises(Exception, match=r'Constraint at index 0 is missing "operator" key.'):
        input_validator.load_and_validate_constraints('[{"column": null, "value": null}]')

    with pytest.raises(Exception, match=r'Constraint at index 0 is missing "value" key.'):
        input_validator.load_and_validate_constraints('[{"column": null, "operator": null}]')


def test_non_existent_constraints_columns(input_validator):
    with pytest.raises(Exception, match=r'Column "hack" in constraint at index 0 does not exist.'):
        input_validator.load_and_validate_constraints('[{"column": "hack", "operator": "<", "value": "5"}]')


def test_non_existent_constraints_operators(input_validator):
    with pytest.raises(Exception, match=r'Invalid operator "add" in constraint at index 0 for numeric data.'):
        input_validator.load_and_validate_constraints('[{"column": "foo", "operator": "add", "value": "5"}]')


def test_loading_constraints(input_validator):
    expected = [{"column": "foo", "operator": "<", "value": "1999-10-11"}]
    assert expected == input_validator.load_and_validate_constraints(
        '[{"column": "foo", "operator": "<", "value": "1999-10-11"}]'
    )
