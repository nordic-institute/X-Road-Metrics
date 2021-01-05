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
