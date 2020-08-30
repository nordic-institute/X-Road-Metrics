import unittest
import datetime

from opendata_module.interface.api.input_validator import load_and_validate_date, load_and_validate_columns, load_and_validate_constraints,\
    load_and_validate_order_clauses


class TestDateValidation(unittest.TestCase):

    def test_empty(self):
        self.assertRaisesRegex(Exception, 'Missing "date" field.', load_and_validate_date, '')
        self.assertRaisesRegex(Exception, 'Missing "date" field.', load_and_validate_date, None)

    def test_wrong_format(self):
        self.assertRaisesRegex(Exception, 'Date must be in the format "YYYY-MM-DD".',
                               load_and_validate_date, '01-02-2003')
        self.assertRaisesRegex(Exception, 'Date must be in the format "YYYY-MM-DD".',
                               load_and_validate_date, 'SELECT * FROM')

    def test_too_recent(self):
        self.assertRaisesRegex(Exception, 'The latest available date is',
                               load_and_validate_date,
                               datetime.datetime.now().strftime('%Y-%m-%d'))

    def test_loading(self):
        expected_date = datetime.datetime(year=1993, month=5, day=17)

        self.assertEqual(expected_date, load_and_validate_date('1993-05-17'))


class TestColumnsValidation(unittest.TestCase):

    def test_no_columns(self):
        self.assertCountEqual([], load_and_validate_columns('[]'))

    def test_non_existent_columns(self):
        self.assertRaisesRegex(Exception, 'Column "a" does not exist.', load_and_validate_columns, '["a", "b", "c"]')

    def test_wrong_format(self):
        self.assertRaisesRegex(Exception, 'Unable to parse columns as a list of field names.',
                               load_and_validate_columns, 'SELECT * FROM')
        self.assertRaisesRegex(Exception, 'Unable to parse columns as a list of field names.',
                               load_and_validate_columns, '{"a", "b"}')

    def test_loading(self):
        self.assertCountEqual(["requestInDate", "clientMemberCode"],
                              load_and_validate_columns('["requestInDate", "clientMemberCode"]'))


class TestOrderValidation(unittest.TestCase):

    def test_no_order(self):
        self.assertCountEqual([], load_and_validate_order_clauses('[]'))

    def test_wrong_format(self):
        self.assertRaisesRegex(Exception, 'Unable to parse order clauses as a list of objects',
                               load_and_validate_order_clauses, 'SELECT * FROM')

    def test_wrong_inner_datatypes(self):
        self.assertRaisesRegex(Exception, 'Every constraint must be with the schema',
                               load_and_validate_order_clauses, '[["a", "b"], ["c", "d"]]')

    def test_missing_attribute(self):
        self.assertRaisesRegex(Exception, 'Order clause at index 0 is missing "order" key.',
                               load_and_validate_order_clauses, '[{"column": "requestInDate"}, {"order": "asc"}]')
        self.assertRaisesRegex(Exception, 'Order clause at index 1 is missing "column" key.',
                               load_and_validate_order_clauses,
                               '[{"column": "requestInDate", "order": "desc"}, {"order": "asc"}]')

    def test_non_existent_columns(self):
        self.assertRaisesRegex(Exception, 'Column "mystery" in order clause at index 0 does not exist.',
                               load_and_validate_order_clauses, '[{"column": "mystery", "order": "asc"}]')

    def test_non_existent_orders(self):
        self.assertRaisesRegex(Exception,
                               'Can not order data in ascii order in order clause at index 1.',
                               load_and_validate_order_clauses,
                               '[{"column": "requestInDate", "order": "asc"}, {"column": "requestInDate", "order": "ascii"}]', )

    def test_loading(self):
        self.assertCountEqual([{'column': 'requestInDate', 'order': 'asc'}],
                              load_and_validate_order_clauses('[{"column": "requestInDate", "order": "asc"}]'))


class TestConstraintsValidation(unittest.TestCase):

    def test_no_constraints(self):
        self.assertCountEqual([], load_and_validate_constraints('[]'))

    def test_wrong_format(self):
        self.assertRaisesRegex(Exception, 'Unable to parse constraints as a list of objects',
                               load_and_validate_constraints, 'SELECT * FROM')

    def test_missing_attribute(self):
        self.assertRaisesRegex(Exception,
                               'Constraint at index 0 is missing "column" key.',
                               load_and_validate_constraints, '[{"operator": null, "value": null}]')
        self.assertRaisesRegex(Exception,
                               'Constraint at index 0 is missing "operator" key.',
                               load_and_validate_constraints, '[{"column": null, "value": null}]')
        self.assertRaisesRegex(Exception,
                               'Constraint at index 0 is missing "value" key.',
                               load_and_validate_constraints, '[{"column": null, "operator": null}]')

    def test_non_existent_columns(self):
        self.assertRaisesRegex(Exception,
                               'Column "hack" in constraint at index 0 does not exist.',
                               load_and_validate_constraints, '[{"column": "hack", "operator": "<", "value": "5"}]')

    def test_non_existent_operators(self):
        self.assertRaisesRegex(Exception,
                               'Invalid operator "add" in constraint at index 0 for numeric data.',
                               load_and_validate_constraints,
                               '[{"column": "requestInDate", "operator": "add", "value": "5"}]')

    def test_loading(self):
        self.assertCountEqual([{"column": "requestInDate", "operator": "<", "value": "1999-10-11"}],
                              load_and_validate_constraints(
                                  '[{"column": "requestInDate", "operator": "<", "value": "1999-10-11"}]'))
