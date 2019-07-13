from os import getenv
from random import randint

from redis_tools import auth_on_redis
from redis_tools import get_question_and_answer
from redis_tools import get_last_player_question
from redis_tools import check_player_answer

from dotenv import load_dotenv
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext import ConversationHandler, RegexHandler
from telegram import Sticker


NEW_QUESTION_REQUEST, SOLUTION_ATTEMPT, GIVE_UP = range(3)


def start(bot, update):
    custom_keyboard = [['Новый вопрос', 'Сдаться'],
                       ['Мой счет']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    username = update.message.from_user.first_name
    update.message.reply_text(
        text=f'{username}, привет! Я бот для викторин!',
        reply_markup=reply_markup
    )
    return NEW_QUESTION_REQUEST


def handle_new_question_request(bot, update):
    key_for_player_question_ids = f'telegram:player_{update.message.chat_id}:question_ids'
    question_and_answer = get_question_and_answer(
        redis_obj,
        key_for_player_question_ids
    )
    update.message.reply_text(question_and_answer['question'])
    return SOLUTION_ATTEMPT


def handle_solution_attempt(bot, update):
    key_for_player_question_ids = f'telegram:player_{update.message.chat_id}:question_ids'
    result = check_player_answer(
        redis_obj,
        update.message.text,
        key_for_player_question_ids
    )
    if result:
        update.message.reply_text(
            'Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос"'
        )
        return NEW_QUESTION_REQUEST
    update.message.reply_text('Неправильно... Попробуешь еще раз?')
    return SOLUTION_ATTEMPT


def handle_give_up(bot, update):
    key_for_player_question_ids = f'telegram:player_{update.message.chat_id}:question_ids'
    last_player_question = get_last_player_question(
        redis_obj,
        key_for_player_question_ids
    )
    update.message.reply_text(f'Ответ:\n{last_player_question["answer"]}.')
    new_question_and_answer = get_question_and_answer(
        redis_obj,
        key_for_player_question_ids
    )
    update.message.reply_text(
        f'Новый вопрос:\n{new_question_and_answer["question"]}'
    )
    return SOLUTION_ATTEMPT


def cancel(bot, update):
    pass


def main():
    load_dotenv()
    global redis_obj
    redis_obj = auth_on_redis()
    updater = Updater(getenv('TELEGRAM_TOKEN'))
    dispatcher = updater.dispatcher

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NEW_QUESTION_REQUEST: [
                RegexHandler('^Новый вопрос$', handle_new_question_request),
            ],
            SOLUTION_ATTEMPT: [
                RegexHandler('^Сдаться$', handle_give_up),
                MessageHandler(Filters.text, handle_solution_attempt),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(conversation_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
