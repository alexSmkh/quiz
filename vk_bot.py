import random
from os import getenv

from redis_tools import auth_on_redis
from redis_tools import get_question_and_answer
from redis_tools import get_last_player_question
from redis_tools import check_player_answer

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from dotenv import load_dotenv


def build_keyboard(event, vk, message):
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.DEFAULT)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.DEFAULT)

    keyboard.add_line()
    keyboard.add_button('Счет', color=VkKeyboardColor.DEFAULT)
    vk.messages.send(
        peer_id=event.user_id,
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard(),
        message=message
    )


def start_chating(event, vk):
    username = vk.users.get(user_id=event.user_id)[0]['first_name']
    build_keyboard(
        event,
        vk,
        f'{username}, привет! Я бот для викторин. Нажми "Новый вопрос, чтобы начать игру.'
    )


def handle_new_question_request(event, vk):
    key_for_player_question_ids = f'vk:player_{event.user_id}:question_ids'
    question_and_answer = get_question_and_answer(
        redis_obj,
        key_for_player_question_ids
    )
    vk.messages.send(
        user_id=event.user_id,
        message=question_and_answer['question'],
        random_id=random.randint(1, 1000)
    )


def handle_give_up(event, vk):
    key_for_player_question_ids = f'vk:player_{event.user_id}:question_ids'
    last_player_question = get_last_player_question(
        redis_obj,
        key_for_player_question_ids
    )
    vk.messages.send(
        user_id=event.user_id,
        message=f'Ответ:\n{last_player_question["answer"]}',
        random_id=random.randint(1, 1000)
    )
    new_question = get_question_and_answer(
        redis_obj,
        key_for_player_question_ids
    )
    vk.messages.send(
        user_id=event.user_id,
        message=f'Новый вопрос:\n{new_question["question"]}',
        random_id=random.randint(1, 1000)
    )


def handle_solution_attempt(event, vk):
    key_for_player_question_ids = f'vk:player_{event.user_id}:question_ids'
    result = check_player_answer(
        redis_obj,
        event.text,
        key_for_player_question_ids
    )
    if result:
        message = 'Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос"'
    else:
        message = 'Неправильно... Попробуешь еще раз?'
    vk.messages.send(
        user_id=event.user_id,
        message=message,
        random_id=random.randint(1, 1000)
    )


def main():
    load_dotenv()
    global redis_obj
    redis_obj = auth_on_redis()
    vk_session = vk_api.VkApi(token=getenv('VK_TOKEN'))
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == 'Новый вопрос':
                handle_new_question_request(event, vk)
            elif event.text == 'Сдаться':
                handle_give_up(event, vk)
            elif event.text == 'Начать':
                start_chating(event, vk)
            else:
                handle_solution_attempt(event, vk)


if __name__ == '__main__':
    main()