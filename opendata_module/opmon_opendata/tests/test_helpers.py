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
import gzip
import json
import io
import pytest

from datetime import date, datetime
from opmon_opendata.api import helpers


SETTINGS = {
    'opendata': {}
}


@pytest.fixture
def postgres(mocker):
    return mocker.Mock()


@pytest.mark.parametrize(
    "column_types, data_cursor, expected_output",
    [
        # Test case: Multiple results
        (
            [('foo', 'integer'), ('bar', 'character varying'), ('baz', 'date')],
            [('1', 'aaa', date(2025, 1, 1)), ('2', 'bbb', date(2025, 2, 2))],
            [{'foo': '1', 'bar': 'aaa', 'baz': '2025-01-01'},
             {'foo': '2', 'bar': 'bbb', 'baz': '2025-02-02'}]
        ),
        # Test case: No results
        (
            [('foo', 'integer')],
            [],
            []
        )
    ]
)
def test_generate_ndjson_stream_creates_correct_json(postgres, column_types, data_cursor, expected_output):
    postgres.get_column_names_and_types.return_value = column_types
    postgres.get_data_cursor.return_value = data_cursor
    gzipped_file_stream = helpers.generate_ndjson_stream(postgres, datetime.now(), [], [], [], SETTINGS)
    decompressed_data = decompress_gzip(gzipped_file_stream)
    assert json.loads(decompressed_data) == expected_output

def decompress_gzip(gzipped_file_stream):
    compressed_data = b"".join(gzipped_file_stream)
    with gzip.GzipFile(fileobj=io.BytesIO(compressed_data), mode="rb") as f:
        decompressed_data = f.read().decode()
        return decompressed_data
