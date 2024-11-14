import sqlalchemy.types as types

# For writing a list of code to a file
def write_file(filename, list_of_strings):
    with open(filename, "w") as f:
        s = "\n".join(list_of_strings)
        f.write(s)
        # f.writelines(list_of_strings)

# This implements a lower case string
class LowerCaseString(types.TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, dialect):
        return value.lower()


class UpperCaseString(types.TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, dialect):
        return value.upper()


class TitleCaseString(types.TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, dialect):
        return value.title()


def snake_to_pascal(string):
    # split the string by underscores
    words = string.split('_')

    # capitalize the first letter of each word and join them
    return ''.join(word.capitalize() for word in words)

def snake_to_words(string):
    # split the string by underscores
    words = string.split('_')

    # capitalize the first letter of each word and join them
    return ' '.join(word.capitalize() for word in words)

def snake_to_camel(string):
    # split the string by underscores
    words = string.split('_')
    # capitalize the first letter of each word except the first one
    return words[0] + ''.join(word.capitalize() for word in words[1:])


def snake_to_label(snake_str):
    components = snake_str.split('_')
    return ' '.join(word.capitalize() for word in components)


def camel_to_pascal(string):
    # capitalize the first letter of the string
    pascal = string.capitalize()

    # replace each instance of an uppercase letter with an underscore followed by the lowercase version of the same letter
    return pascal.replace('_', '')


def camel_to_snake(name):
    # create an empty string to hold the snake case name
    snake_case_name = ''
    # iterate over each character in the name
    for i, char in enumerate(name):
        # if the character is uppercase and not the first character
        if char.isupper() and i > 0:
            # add an underscore before the uppercase character
            snake_case_name += '_'
        # add the lowercase version of the character to the snake case name
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

