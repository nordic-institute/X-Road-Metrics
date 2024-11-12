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

import string


def format_letter(character):
    """
    Replaces special characters from a single character with "-".
    NB: If the string is empty, it returns empty string.
    :param character: A single character.
    :return: Return "-" for everything else except [a-zA-Z-._0-9]
    """
    valid_set = set(string.ascii_lowercase + string.digits + '_.-')

    if character.lower() in valid_set or character == "":
        return character
    else:
        return '-'


def format_string(input_string):
    """
    Replaces all the special characters from a given string with "-".
    :param input_string: A single string.
    :return: Return "-" for everything else except [a-zA-Z-._0-9]
    """
    new_string = ""
    for letter in input_string:
        new_string += format_letter(letter)

    return new_string


def truncate(s):
    return s[:55] if s is not None else ""
