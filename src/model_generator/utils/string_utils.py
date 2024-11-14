#!/usr/bin/env python3
"""
Author: Nyimbi Odero
Copyright: Nyimbi Odero, 2024
License: MIT

string_utils.py: A comprehensive library for string manipulation and text processing.

This module provides a rich set of utilities for manipulating and formatting text data,
with particular focus on supporting code generation, documentation processing, and
general text formatting tasks.

Key Features:
    1. Text Formatting and Cleaning
        - Docstring cleaning and normalization
        - Text wrapping with custom indentation
        - Line ending normalization
        - Comment stripping
        - Special character removal
        - Text truncation

    2. Text Extraction and Parsing
        - Block extraction between markers
        - Text segment extraction
        - Pattern-based extraction
        - Comment removal

    3. Text Layout and Presentation
        - Table formatting with headers
        - Custom text indentation
        - Paragraph preservation
        - Width-aware text wrapping

    4. File and Path Processing
        - Filename sanitization
        - Natural sorting support
        - Path string handling

    5. Language Processing
        - Word pluralization
        - Text normalization
        - String pattern matching

Core Functions:
    - clean_docstring(): Normalize and clean documentation strings
    - wrap_text(): Intelligent text wrapping with indentation support
    - normalize_line_endings(): Standardize line endings
    - indent_text(): Apply consistent indentation
    - extract_blocks(): Extract text between markers
    - strip_comments(): Remove comments while preserving structure
    - format_table(): Create formatted text tables
    - pluralize(): Convert words to plural form
    - remove_special_chars(): Clean special characters
    - truncate(): Smart text truncation
    - extract_between(): Extract text between delimiters
    - sanitize_filename(): Clean filenames
    - natural_sort_key(): Natural sorting support

Usage Examples:
    >>> from model_generator.utils.string_utils import clean_docstring, wrap_text
    >>> clean_docstring("  Hello   World  ")
    'Hello World'
    >>> wrap_text("Long text example", width=20)
    'Long text example'

Dependencies:
    - re: Regular expression operations
    - textwrap: Text wrapping and filling
    - typing: Type hints and annotations

Note:
    This module is designed to be both comprehensive and efficient, providing
    a complete toolkit for string manipulation tasks commonly encountered in
    code generation and text processing applications.
"""

import re
import textwrap
from typing import List, Optional, Tuple


def clean_docstring(text: str) -> str:
    """
    Clean and normalize a docstring.

    Args:
        text (str): Input docstring

    Returns:
        str: Cleaned docstring

    Examples:
        >>> clean_docstring('   Hello    world   ')
        'Hello world'
        >>> clean_docstring('First line\\n   Second line\\n\\n\\nThird line')
        'First line\\nSecond line\\n\\nThird line'
    """
    if not text:
        return ""

    # Split into lines and remove leading/trailing whitespace
    lines = [line.strip() for line in text.split('\n')]

    # Remove empty lines from start and end
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()

    # Normalize empty lines in the middle (max one empty line)
    result = []
    prev_empty = False
    for line in lines:
        if line:
            result.append(line)
            prev_empty = False
        elif not prev_empty:
            result.append(line)
            prev_empty = True

    return '\n'.join(result)


def wrap_text(text: str, width: int = 80, initial_indent: str = "", subsequent_indent: str = "") -> str:
    """
    Wrap text to specified width while preserving paragraphs.

    Args:
        text (str): Text to wrap
        width (int): Maximum line width
        initial_indent (str): Indentation for first line
        subsequent_indent (str): Indentation for subsequent lines

    Returns:
        str: Wrapped text

    Examples:
        >>> print(wrap_text("Short line.", width=20))
        Short line.
        >>> text = "This is a very long line that should be wrapped to multiple lines."
        >>> print(wrap_text(text, width=20, subsequent_indent="  "))
        This is a very long
          line that should
          be wrapped to
          multiple lines.
    """
    if not text:
        return ""

    # Split into paragraphs
    paragraphs = text.split('\n\n')

    # Wrap each paragraph
    wrapped_paragraphs = []
    for i, para in enumerate(paragraphs):
        if i == 0:
            wrapped = textwrap.fill(para.strip(), width=width,
                                  initial_indent=initial_indent,
                                  subsequent_indent=subsequent_indent)
        else:
            wrapped = textwrap.fill(para.strip(), width=width,
                                  initial_indent=subsequent_indent,
                                  subsequent_indent=subsequent_indent)
        wrapped_paragraphs.append(wrapped)

    return '\n\n'.join(wrapped_paragraphs)


def normalize_line_endings(text: str) -> str:
    """
    Normalize line endings to \\n.

    Args:
        text (str): Input text

    Returns:
        str: Text with normalized line endings
    """
    if not text:
        return ""

    # Replace all types of line endings with \n
    return re.sub(r'\r\n|\r|\n', '\n', text)


def indent_text(text: str, indent: str = "    ") -> str:
    """
    Indent each line of text.

    Args:
        text (str): Text to indent
        indent (str): Indentation string

    Returns:
        str: Indented text
    """
    if not text:
        return ""

    lines = text.split('\n')
    return '\n'.join(indent + line if line else line for line in lines)


def extract_blocks(text: str, start_marker: str, end_marker: str) -> List[Tuple[str, int, int]]:
    """
    Extract blocks of text between markers.

    Args:
        text (str): Input text
        start_marker (str): Start marker
        end_marker (str): End marker

    Returns:
        List[Tuple[str, int, int]]: List of (block_text, start_pos, end_pos)
    """
    if not text or not start_marker or not end_marker:
        return []

    blocks = []
    pos = 0

    while True:
        # Find start marker
        start = text.find(start_marker, pos)
        if start == -1:
            break

        # Find matching end marker
        end = text.find(end_marker, start + len(start_marker))
        if end == -1:
            break

        # Extract block
        block_start = start + len(start_marker)
        block = text[block_start:end]
        blocks.append((block, block_start, end))

        pos = end + len(end_marker)

    return blocks


def strip_comments(text: str) -> str:
    """
    Strip Python comments from text while preserving line numbers.

    Args:
        text (str): Input text

    Returns:
        str: Text with comments removed
    """
    if not text:
        return ""

    lines = []
    for line in text.split('\n'):
        # Handle inline comments
        if '#' in line:
            # Keep everything before the comment
            line = line[:line.index('#')].rstrip()
        lines.append(line)

    return '\n'.join(lines)


def format_table(rows: List[List[str]], headers: Optional[List[str]] = None) -> str:
    """
    Format a text table with aligned columns.

    Args:
        rows (List[List[str]]): Table data
        headers (Optional[List[str]]): Column headers

    Returns:
        str: Formatted table

    Example:
        >>> data = [['apple', '5', '0.99'], ['banana', '8', '1.25']]
        >>> headers = ['Fruit', 'Count', 'Price']
        >>> print(format_table(data, headers))
        Fruit  | Count | Price
        -------|-------|-------
        apple  | 5     | 0.99
        banana | 8     | 1.25
    """
    if not rows:
        return ""

    # Calculate column widths
    all_rows = [headers] + rows if headers else rows
    col_widths = []
    for col in zip(*all_rows):
        col_widths.append(max(len(str(x)) for x in col))

    # Format lines
    lines = []

    # Add headers
    if headers:
        header_line = " | ".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
        lines.append(header_line)
        separator = "-" * len(header_line)
        lines.append(separator)

    # Add data rows
    for row in rows:
        line = " | ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths))
        lines.append(line)

    return '\n'.join(lines)



def pluralize(word: str) -> str:
    """
    Convert a word to its plural form using basic English rules.

    Args:
        word (str): Singular word

    Returns:
        str: Plural form of the word

    Examples:
        >>> pluralize('cat')
        'cats'
        >>> pluralize('city')
        'cities'
    """
    if not word:
        return ""

    # Common irregular plurals
    irregulars = {
        'child': 'children',
        'goose': 'geese',
        'man': 'men',
        'woman': 'women',
        'tooth': 'teeth',
        'foot': 'feet',
        'mouse': 'mice',
        'person': 'people',
        'criterion': 'criteria',
        'ox': 'oxen',
        'die': 'dice',
        'penny': 'pence',
        'sheep': 'sheep',
        'deer': 'deer',
        'fish': 'fish',
        'series': 'series',
        'species': 'species',
        'phenomenon': 'phenomena',
        'radius': 'radii',
        'nucleus': 'nuclei',
        'cactus': 'cacti',
        'analysis': 'analyses',
        'basis': 'bases',
        'crisis': 'crises',
        'hypothesis': 'hypotheses',
        'parenthesis': 'parentheses',
        'thesis': 'theses',
        'axis': 'axes',
        'matrix': 'matrices',
        'index': 'indices',
        'appendix': 'appendices',
        'curriculum': 'curricula'
    }

    if word.lower() in irregulars:
        return irregulars[word.lower()]

    # Regular rules
    if word.endswith(('s', 'sh', 'ch', 'x', 'z')):
        return word + 'es'
    elif word.endswith('y'):
        if word[-2] not in 'aeiou':
            return word[:-1] + 'ies'
        return word + 's'
    elif word.endswith('f'):
        return word[:-1] + 'ves'
    elif word.endswith('fe'):
        return word[:-2] + 'ves'
    else:
        return word + 's'

def remove_special_chars(text: str, allow_chars: str = "") -> str:
    """
    Remove special characters from text.

    Args:
        text (str): Input text
        allow_chars (str): Characters to preserve

    Returns:
        str: Cleaned text

    Examples:
        >>> remove_special_chars('Hello! @World#')
        'Hello World'
        >>> remove_special_chars('Hello! @World#', allow_chars='!')
        'Hello! World'
    """
    if not text:
        return ""

    pattern = f'[^a-zA-Z0-9\\s{re.escape(allow_chars)}]'
    return re.sub(pattern, '', text)

def truncate(text: str, length: int, suffix: str = "...") -> str:
    """
    Truncate text to specified length.

    Args:
        text (str): Input text
        length (int): Maximum length
        suffix (str): Suffix to add to truncated text

    Returns:
        str: Truncated text

    Examples:
        >>> truncate('Long text example', 8)
        'Long...'
        >>> truncate('Short', 10)
        'Short'
    """
    if not text or len(text) <= length:
        return text

    return text[:length - len(suffix)] + suffix

def extract_between(text: str, start: str, end: str, inclusive: bool = False) -> List[str]:
    """
    Extract all text segments between start and end markers.

    Args:
        text (str): Input text
        start (str): Start marker
        end (str): End marker
        inclusive (bool): Include markers in result

    Returns:
        List[str]: Extracted segments

    Examples:
        >>> extract_between('Hello [world] and [python]', '[', ']')
        ['world', 'python']
        >>> extract_between('Hello [world]', '[', ']', inclusive=True)
        ['[world]']
    """
    if not text or not start or not end:
        return []

    pattern = f'{re.escape(start)}(.*?){re.escape(end)}'
    matches = re.findall(pattern, text)

    if inclusive:
        return [f'{start}{m}{end}' for m in matches]
    return matches

def sanitize_filename(filename: str, replace_char: str = "_") -> str:
    """
    Sanitize a filename by removing invalid characters.

    Args:
        filename (str): Input filename
        replace_char (str): Character to replace invalid chars with

    Returns:
        str: Sanitized filename

    Examples:
        >>> sanitize_filename('file*name?.txt')
        'file_name_.txt'
    """
    if not filename:
        return ""

    # Invalid characters in most filesystems
    invalid_chars = r'[<>:"/\\|?*]'
    return re.sub(invalid_chars, replace_char, filename)

def natural_sort_key(text: str) -> List[Union[int, str]]:
    """
    Create key for natural sorting of strings with numbers.

    Args:
        text (str): Input text

    Returns:
        List[Union[int, str]]: Sort key

    Examples:
        >>> sorted(['file2.txt', 'file10.txt', 'file1.txt'], key=natural_sort_key)
        ['file1.txt', 'file2.txt', 'file10.txt']
    """
    if not text:
        return []

    def convert(text):
        return int(text) if text.isdigit() else text.lower()

    return [convert(c) for c in re.split('([0-9]+)', text)]
