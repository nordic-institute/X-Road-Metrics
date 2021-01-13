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
