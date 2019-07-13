import re
import os

from dotenv import load_dotenv

from redis_tools import auth_on_redis, load_quiz_on_redis


def load_files():
    for filename in os.listdir('./questions/'):
        with open(f'./questions/{filename}', 'r', encoding='KOI8-R') as reader:
            file = reader.read()
        yield file


def read_next_file(generator):
    try:
        return next(generator)
    except StopIteration:
        return None


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
    questions_and_answers = {}
    question_and_answer_id = 1
    question_pattern = 'Вопрос \d+:'
    answer_pattern = 'Ответ:'
    question = None
    answer = None

    while True:
        text = read_next_file(file_generator)
        if text is None:
            break
        paragraphs = text.split('\n\n')

        for paragraph in paragraphs:
            if question is None:
                question = find_search_text(question_pattern, paragraph)

            if answer is None:
                answer = find_search_text(answer_pattern, paragraph)

            if question and answer:
                questions_and_answers[f'question_{question_and_answer_id}'] = dict(
                    question=question,
                    answer=answer
                )
                question_and_answer_id += 1
                question = None
                answer = None

    return questions_and_answers


if __name__ == '__main__':
    load_dotenv()
    redis_obj = auth_on_redis()
    quiz = get_dictionary_for_quiz()
    load_quiz_on_redis(redis_obj, quiz)

