import re
import os


def load_files():
    for filename in os.listdir(os.path.join(os.getcwd(), 'questions')):
        with open(os.path.join(
                os.getcwd(),
                os.path.join('questions', filename)
        ), 'r', encoding='KOI8-R') as reader:
            file = reader.read()
        yield file


def find_search_text(pattern, paragraph):
    len_of_newline_character = 1
    index_for_end_of_block_title = 1

    match = re.search(pattern, paragraph)
    if match:
        index_for_beginning_of_search_text = match.span()[
                                              index_for_end_of_block_title
                                             ] + len_of_newline_character
        raw_text_string = paragraph[index_for_beginning_of_search_text:]
        search_text = raw_text_string.replace('\n', ' ')
        return search_text


def get_dictionary_for_quiz():
    file_generator = load_files()
    question_pattern = r'Вопрос \d+:'
    answer_pattern = r'Ответ:'
    question = None
    answer = None

    for text in file_generator:
        paragraphs = text.split('\n\n')
        for paragraph in paragraphs:
            if question is None:
                question = find_search_text(question_pattern, paragraph)
            if answer is None:
                answer = find_search_text(answer_pattern, paragraph)
            if question and answer:
                yield question, answer

                question = None
                answer = None
