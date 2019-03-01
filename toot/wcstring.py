"""
Utilities for dealing with string containing wide characters.
"""

import re

from wcwidth import wcwidth, wcswidth


def _wc_hard_wrap(line, length):
    """
    Wrap text to length characters, breaking when target length is reached,
    taking into account character width.

    Used to wrap lines which cannot be wrapped on whitespace.
    """
    chars = []
    chars_len = 0
    for char in line:
        char_len = wcwidth(char)
        if chars_len + char_len > length:
            yield "".join(chars)
            chars = []
            chars_len = 0

        chars.append(char)
        chars_len += char_len

    if chars:
        yield "".join(chars)


def wc_wrap(text, length):
    """
    Wrap text to given length, breaking on whitespace and taking into account
    character width.

    Tries to preserve whitespace where possible. Trailing white space that would
    create a line break is removed in favor of preserving white space at the
    beginning of a line (ie, indents).
    """
    line_words = []
    line_len = 0

    words = re.split(r"(.+?(?:[ \t]+|$))", text)
    for word in words:
        if word == '':
            continue

        word_len = wcswidth(word)
        striped_line = "".join(line_words).rstrip()

        # Account for the fact that this line will hard wrap at least once,
        # and as such the next word may have a bit more space before it would
        # need to make another wrap.
        if wcswidth(striped_line) > length:
            line_len = line_len % length

        if line_words and line_len + word_len > length and line_len + wcswidth(word.rstrip()) > length:
            if wcswidth(striped_line) <= length:
                yield striped_line
            else:
                yield from _wc_hard_wrap(striped_line, length)

            line_words = []

        line_len = wcswidth("".join(line_words)) + word_len
        line_words.append(word)

    if line_words:
        line = "".join(line_words).rstrip()
        if line_len <= length:
            yield line
        else:
            yield from _wc_hard_wrap(line, length)


def trunc(text, length):
    """
    Truncates text to given length, taking into account wide characters.

    If truncated, the last char is replaced by an elipsis.
    """
    if length < 1:
        raise ValueError("length should be 1 or larger")

    # Remove whitespace first so no unneccesary truncation is done.
    text = text.strip()
    text_length = wcswidth(text)

    if text_length <= length:
        return text

    # We cannot just remove n characters from the end since we don't know how
    # wide these characters are and how it will affect text length.
    # Use wcwidth to determine how many characters need to be truncated.
    chars_to_truncate = 0
    trunc_length = 0
    for char in reversed(text):
        chars_to_truncate += 1
        trunc_length += wcwidth(char)
        if text_length - trunc_length <= length:
            break

    # Additional char to make room for elipsis
    n = chars_to_truncate + 1
    return text[:-n].strip() + '…'


def pad(text, length):
    """Pads text to given length, taking into account wide characters."""
    text_length = wcswidth(text)

    if text_length < length:
        return text + ' ' * (length - text_length)

    return text


def fit_text(text, length):
    """Makes text fit the given length by padding or truncating it."""
    text_length = wcswidth(text)

    if text_length > length:
        return trunc(text, length)

    if text_length < length:
        return pad(text, length)

    return text
