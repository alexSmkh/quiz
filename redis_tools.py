import json
import os
from random import randint
from random import choice

from formatting_answer import get_format_answer

import redis


def create_player_score(redis_obj, player_id):
    redis_obj.set(f'{player_id}:win_record', 0)
    redis_obj.set(f'{player_id}:loss_record', 0)


def get_player_score(redis_obj, player_id):
    return (
        redis_obj.get(f'{player_id}:win_record'),
        redis_obj.get(f'{player_id}:loss_record')
    )


def add_game_point(redis_obj, key_for_player_score):
    redis_obj.incr(key_for_player_score)


def check_player_answer(redis_obj, player_answer, key_for_player_question_ids):
    last_player_question = get_last_player_question(
        redis_obj,
        key_for_player_question_ids
    )
    format_true_answer = get_format_answer(last_player_question['answer'])
    format_player_answer = get_format_answer(player_answer)
    return format_true_answer == format_player_answer


def get_last_player_question(redis_obj, key_for_player_question_ids):
    last_question_id = redis_obj.lindex(key_for_player_question_ids, -1)
    raw_question = redis_obj.get(f'question_{last_question_id}')
    question_and_answer = json.loads(raw_question, encoding='utf-8')
    return question_and_answer


def get_question_and_answer(redis_obj, key_for_player_question_ids):
    number_of_questions = int(redis_obj.get('number_of_questions'))

    if redis_obj.exists(key_for_player_question_ids):
        user_question_ids = redis_obj.lrange(key_for_player_question_ids, 0, -1)
        all_question_ids = set(range(1, number_of_questions))
        possible_question_ids = all_question_ids.difference(
            set(user_question_ids)
        )
        question_id = choice(list(possible_question_ids))
    else:
        question_id = randint(1, number_of_questions)

    redis_obj.rpush(key_for_player_question_ids, question_id)
    raw_question = redis_obj.get(f'question_{question_id}')
    question_and_answer = json.loads(raw_question, encoding='utf-8')
    return question_and_answer


def load_quiz_on_redis(redis_obj, quiz):
    number_of_questions = 0
    for qa_id, question_and_answer in quiz.items():
        qa_json = json.dumps(question_and_answer)
        redis_obj.set(qa_id, qa_json)
        number_of_questions += 1
    redis_obj.set(f'number_of_questions', number_of_questions)


def auth_on_redis():
    redis_obj = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=os.getenv('REDIS_PORT'),
        password=os.getenv('REDIS_PASSWORD'),
        decode_responses=True,
    )
    return redis_obj