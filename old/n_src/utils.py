import sqlalchemy.types as types
import logging
import inflect
import math

# Set up logging configuration
logging.basicConfig(level=logging.ERROR)

def get_class_name(table_name, p):
    """
    Generate a class name from a table name.

    :param table_name: The name of the table
    :param p: The inflect engine
    :return: A capitalized, singular form of the table name
    """
    return ''.join([(p.singular_noun(part) or part).capitalize() for part in table_name.split('_')])

def is_association_table(table_name, inspector):
    """Improved detection of association tables.
    Check if a table is likely an association table.

    An association table typically has the following characteristics:
    0. The name ends in _assoc (our formal convention)
    1. Has at least two foreign keys
    2. May have additional columns for metadata (e.g., creation date, status)
    3. Usually has a relatively small number of columns compared to regular entity tables
    4. The name often follows a pattern like 'table1_table2' or 'table1_to_table2'

    Args:
            table_name (str): Name of the table to check
            inspector (sa.engine.reflection.Inspector): SQLAlchemy Inspector object

        Returns:
            bool: True if the table is likely an association table, False otherwise
    """
    if table_name.endswith("_assoc"):
        return True

    fks = inspector.get_foreign_keys(table_name)
    columns = inspector.get_columns(table_name)

    if len(fks) < 2:
        return False

    non_fk_columns = [col for col in columns if col['name'] not in
                      [c for fk in fks for c in fk['constrained_columns']]]

    # Allow for id, timestamps, and a couple of additional metadata columns
    allowed_extra = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    extra_columns = [col for col in non_fk_columns if col['name'] not in allowed_extra]

   # Check if the table name follows the pattern 'table1_table2' or 'table1_to_table2'
    name_parts = table_name.split('_')
    if len(name_parts) >= 2 and (name_parts[-1] in fks[0]['referred_table'] or name_parts[-1] in fks[1]['referred_table']):
        return True

    return len(extra_columns) <= 2

# def get_class_name(table_name, p):
#     """
#     Generate a class name from a table name.

#     :param table_name: The name of the table
#     :param p: The inflect engine
#     :return: A capitalized, singular form of the table name
#     """
#     singular = p.singular_noun(table_name)
#     return snake_to_pascal(table_name)
#     # return (singular or table_name).capitalize()


def write_file(filename: str, list_of_strings: list[str]) -> None:
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
        logging.error(f"An error occurred while writing to the file: {e}")


class LowerCaseString(types.TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, str):
            raise TypeError("Expected a string value")
        return value.lower()


class UpperCaseString(types.TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, str):
            raise TypeError("Expected a string value")
        return value.upper()


class TitleCaseString(types.TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, str):
            raise TypeError("Expected a string value")
        return value.title()


def capitalize_words(words: list[str]) -> str:
    """
    Capitalizes each word in a list and joins them into a single string.

    :param words: A list of words to be capitalized.
    :return: A string with each word capitalized and joined.
    """
    return ''.join(word.capitalize() for word in words)


def snake_to_pascal(string: str, p=None) -> str:
    """
    Converts a snake_case string to PascalCase.

    :param string: The snake_case string to be converted.
    :return: The converted PascalCase string.

    Example:
    >>> snake_to_pascal('example_string')
    'ExampleString'

    Edge Case:
    >>> snake_to_pascal('')
    ''
    """
    if not isinstance(string, str):
        raise ValueError("Input must be a string.")
    if not string:
        return ''
    return capitalize_words(string.split('_'))


def snake_to_words_or_label(string: str, separator=" ") -> str:
    """
    Converts a snake_case string to a space-separated or other separator format.

    :param string: The snake_case string to be converted.
    :param separator: The separator to use between words (default is space).
    :return: The converted string with words separated by the chosen separator.

    Example:
    >>> snake_to_words_or_label('example_string', separator=' ')
    'Example String'
    """
    if not isinstance(string, str):
        raise ValueError("Input must be a string.")
    if not string:
        return ''
    return separator.join(word.capitalize() for word in string.split('_'))


def snake_to_words(string: str) -> str:
    """
    Converts a snake_case string to space-separated words.

    :param string: The snake_case string to be converted.
    :return: The converted string with space-separated words.
    """
    return snake_to_words_or_label(string, separator=" ")


def snake_to_label(string: str) -> str:
    """
    Converts a snake_case string to a label format (space-separated words with capitalized first letters).

    :param string: The snake_case string to be converted.
    :return: The converted label string.
    """
    return snake_to_words_or_label(string, separator=" ")


def snake_to_camel(string: str) -> str:
    """
    Converts a snake_case string to camelCase.

    :param string: The snake_case string to be converted.
    :return: The converted camelCase string.

    Example:
    >>> snake_to_camel('example_string')
    'exampleString'
    """
    if not isinstance(string, str):
        raise ValueError("Input must be a string.")
    if not string:
        return ''
    words = string.split('_')
    return words[0] + ''.join(word.capitalize() for word in words[1:])


def camel_to_pascal(string: str) -> str:
    """
    Converts a camelCase string to PascalCase.

    :param string: The camelCase string to be converted.
    :return: The converted PascalCase string.

    Example:
    >>> camel_to_pascal('exampleString')
    'ExampleString'
    """
    if not isinstance(string, str):
        raise ValueError("Input must be a string.")
    if not string:
        return ''
    return string[0].upper() + string[1:]


def camel_to_snake(name: str) -> str:
    """
    Converts a camelCase or PascalCase string to snake_case.

    :param name: The camelCase or PascalCase string to be converted.
    :return: The converted snake_case string.

    Example:
    >>> camel_to_snake('ExampleString')
    'example_string'
    """
    if not isinstance(name, str):
        raise ValueError("Input must be a string.")
    if not name:
        return ''
    snake_case_name = ''
    for i, char in enumerate(name):
        if char.isupper() and i != 0:
            snake_case_name += '_'
        snake_case_name += char.lower()
    return snake_case_name


def pascal_to_camel(string):
    # convert the first letter of the string to lowercase
    camel = string[0].lower() + string[1:]

    # replace each instance of an uppercase letter with an underscore followed by the lowercase version of the same letter
    return camel.replace('_', '')


def pascal_to_snake(string):
    # insert an underscore before each uppercase letter and convert the entire string to lowercase
    return ''.join(['_' + letter.lower() if letter.isupper() else letter for letter in string]).lstrip('_')


def pascal_to_words(string):
    # Insert a space before each uppercase letter
    words = ''.join([' ' + letter if letter.isupper() else letter for letter in string]).strip()

    # Capitalize the first letter of each word
    return ' '.join(word.capitalize() for word in words.split())
