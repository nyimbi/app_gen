"""
Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""


import sqlalchemy.types as types

# For writing a list of code to a file
def write_file(filename, list_of_strings):
    """
    Writes a list of strings to a file, with each string on a new line.

    :param filename: The name of the file to write to.
    :param list_of_strings: A list of strings to be written to the file.
    """
    try:
        with open(filename, "w") as f:
            s = "\n".join(list_of_strings)
            f.write(s)
    except IOError as e:
        print(f"An error occurred while writing to the file: {e}")

# This implements a lower case string
class LowerCaseString(types.TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return value.lower()


class UpperCaseString(types.TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return value.upper()


class TitleCaseString(types.TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return value.title()


def snake_to_pascal(string):
    """
    Converts a snake_case string to PascalCase.
    
    :param string: The snake_case string to be converted.
    :return: The converted PascalCase string.
    """
    words = string.split('_')
    return ''.join(word.capitalize() for word in words)


def snake_to_words_or_label(string, separator=" "):
    """
    Converts a snake_case string to a space-separated or other separator format.

    :param string: The snake_case string to be converted.
    :param separator: The separator to use between words (default is space).
    :return: The converted string with words separated by the chosen separator.
    """
    words = string.split('_')
    return separator.join(word.capitalize() for word in words)


def snake_to_words(string):
    """
    Converts a snake_case string to space-separated words.

    :param string: The snake_case string to be converted.
    :return: The converted string with space-separated words.
    """
    return snake_to_words_or_label(string, separator=" ")


def snake_to_label(string):
    """
    Converts a snake_case string to a label format (space-separated words with capitalized first letters).

    :param string: The snake_case string to be converted.
    :return: The converted label string.
    """
    return snake_to_words_or_label(string, separator=" ")


def snake_to_camel(string):
    """
    Converts a snake_case string to camelCase.

    :param string: The snake_case string to be converted.
    :return: The converted camelCase string.
    """
    words = string.split('_')
    return words[0] + ''.join(word.capitalize() for word in words[1:])


def camel_to_pascal(string):
    """
    Converts a camelCase string to PascalCase.

    :param string: The camelCase string to be converted.
    :return: The converted PascalCase string.
    """
    return string[0].upper() + string[1:]


def camel_to_snake(name):
    """
    Converts a camelCase or PascalCase string to snake_case.

    :param name: The camelCase or PascalCase string to be converted.
    :return: The converted snake_case string.
    """
    snake_case_name = ''
    for i, char in enumerate(name):
        if char.isupper() and i != 0:
            snake_case_name += '_'
        snake_case_name += char.lower()
    return snake_case_name
