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


def search_text(pattern, paragraph):
    match = re.search(pattern, paragraph)
    if match:
        return paragraph[match.span()[1]:]


def get_dictionary_for_quiz():
    file_generator = load_files()
    question_pattern = r'(Вопрос \d+:\n)'
    answer_pattern = r'(Ответ:\n)'
    question = None
    answer = None

    for text in file_generator:
        paragraphs = text.split('\n\n')
        for paragraph in paragraphs:
            if question is None:
                question = search_text(question_pattern, paragraph)
            if answer is None:
                answer = search_text(answer_pattern, paragraph)
            if question and answer:
                yield question, answer

                question = None
                answer = None
