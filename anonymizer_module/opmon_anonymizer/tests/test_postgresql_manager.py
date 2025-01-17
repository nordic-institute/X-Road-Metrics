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

import unittest
from unittest.mock import call, patch, MagicMock
from opmon_anonymizer.iio.postgresql_manager import PostgreSqlManager


class TestPostgreSqlManager(unittest.TestCase):

    def setUp(self):
        self.mock_connect = patch('opmon_anonymizer.iio.postgresql_manager.pg.connect').start()
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connect.return_value.__enter__.return_value = self.mock_connection
        self.mock_connection.cursor.return_value = self.mock_cursor

        self.postgres_settings = {
            'table-name': 'test_table',
            'readonly-users': [],
            'host': 'localhost',
            'database-name': 'test_db'
        }
        self.logger = MagicMock()

    def test_table_gets_created_when_not_present(self):
        self.mock_cursor.execute.side_effect = lambda query, params=None: 'false' if query == """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE  table_schema = 'public'
                AND table_name = test_table
            );
        """ else None
        self.mock_cursor.fetchone.return_value = [False]

        table_schema = [('column1', 'VARCHAR'), ('column2', 'INTEGER')]
        index_columns = ['column1']

        PostgreSqlManager(self.postgres_settings, table_schema, index_columns, self.logger)

        self.mock_cursor.execute.assert_has_calls([
            call('CREATE TABLE test_table (id SERIAL PRIMARY KEY, column1 VARCHAR, column2 INTEGER);'),
            call('CREATE INDEX column1_idx ON test_table (column1);')
        ])

    def test_table_gets_altered_when_columns_not_present(self):
        query_exists = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE  table_schema = 'public'
                AND table_name = test_table
            );
        """
        query_columns = """
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'public'
            AND column_name <> 'id'
            AND table_name = test_table;
        """

        def execute_side_effect(query, params=None):
            if query == query_exists:
                return 'true'
            elif query == query_columns:
                return [['column1'], ['column3']]
            else:
                return None

        self.mock_cursor.execute.side_effect = execute_side_effect
        self.mock_cursor.fetchone.return_value = [True]
        self.mock_cursor.fetchall.return_value = [['column1'], ['column3']]

        table_schema = [('column1', 'VARCHAR'), ('column2', 'INTEGER'), ('column3', 'VARCHAR'), ('column4', 'VARCHAR')]
        index_columns = []

        PostgreSqlManager(self.postgres_settings, table_schema, index_columns, self.logger)

        self.mock_cursor.execute.assert_has_calls([
            call('ALTER TABLE test_table ADD column2 INTEGER;'),
            call('ALTER TABLE test_table ADD column4 VARCHAR;')
        ])

    def test_table_not_altered_when_no_missing_columns(self):
        query_exists = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE  table_schema = 'public'
                AND table_name = test_table
            );
        """
        query_columns = """
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'public'
            AND column_name <> 'id'
            AND table_name = test_table;
        """

        def execute_side_effect(query, params=None):
            if query == query_exists:
                return 'true'
            elif query == query_columns:
                return [['column1'], ['column2']]
            else:
                return None

        self.mock_cursor.execute.side_effect = execute_side_effect
        self.mock_cursor.fetchone.return_value = [True]
        self.mock_cursor.fetchall.return_value = [['column1'], ['column2']]

        table_schema = [('column1', 'VARCHAR'), ('column2', 'INTEGER')]
        index_columns = []

        PostgreSqlManager(self.postgres_settings, table_schema, index_columns, self.logger)

        assert call(['ALTER TABLE test_table ADD column1 INTEGER;',
                     'ALTER TABLE test_table ADD column2 VARCHAR;']) not in self.mock_cursor.mock_calls
