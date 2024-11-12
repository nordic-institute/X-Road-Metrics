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

class Translator:
    def __init__(self, template):
        """
        Initializes the translator.
        :param template: Dictionary with the translations.
        key = translation key, value = translation.
        """
        self.vocabulary = dict()
        for k in template:
            self.vocabulary[k] = template[k]
            self.label_not_found = '???'

    def get_translation(self, keyword):
        """
        Tries to translate a given keyword by a specified template.
        If no translation is found, it returns "???".
        :param keyword: Keyword to be translated.
        :return: Returns a translation if it exists and it returns "???" if no translation can be found.
        """
        if keyword in self.vocabulary:
            return self.vocabulary[keyword]
        else:
            return self.label_not_found
