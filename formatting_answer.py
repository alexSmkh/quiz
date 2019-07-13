import re


def get_main_text(raw_answer):
    # remove brackets and words between them
    raw_answer = re.sub(r'\(.*?\)', ' ', raw_answer)

    # find the end of the answer
    match = re.search('[.!?]', raw_answer)
    if not match:
        return raw_answer
    return raw_answer[0:match.span()[0]]


def remove_extra_chars_and_spaces(raw_text):
    # remove chars
    text = re.sub('[,"\']', '', raw_text)

    # remove extra spaces
    return re.sub(' +', ' ', text)


def get_format_answer(answer):
    format_answer = get_main_text(answer)
    format_answer = remove_extra_chars_and_spaces(format_answer)
    return format_answer.lower()

