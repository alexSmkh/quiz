from os import getenv

from redis_tools import auth_on_redis
from redis_tools import get_question_and_answer
from redis_tools import get_last_player_question
from redis_tools import check_player_answer
from redis_tools import create_player_score
from redis_tools import add_game_point
from redis_tools import get_player_score

from dotenv import load_dotenv
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext import ConversationHandler, RegexHandler


NEW_QUESTION_REQUEST, SOLUTION_ATTEMPT, GIVE_UP = range(3)


def start(bot, update):
    custom_keyboard = [['Новый вопрос', 'Сдаться'],
                       ['Мой счет']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    create_player_score(redis_obj, f'player_tg_{update.message.chat_id}')
    username = update.message.from_user.first_name
    update.message.reply_text(
        text=f'{username}, привет! Я бот для викторин!\nНажми "Новый вопрос", чтобы начать игру.',
        reply_markup=reply_markup
    )
    return NEW_QUESTION_REQUEST


def handle_new_question_request(bot, update):
    key_for_player_question_ids = f'player_tg_{update.message.chat_id}:question_ids'
    question_and_answer = get_question_and_answer(
        redis_obj,
        key_for_player_question_ids
    )
    update.message.reply_text(question_and_answer['question'])
    return SOLUTION_ATTEMPT


def handle_solution_attempt(bot, update):
    key_for_player_question_ids = f'player_tg_{update.message.chat_id}:question_ids'
    result = check_player_answer(
        redis_obj,
        update.message.text,
        key_for_player_question_ids
    )
    if result:
        update.message.reply_text(
            'Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос"'
        )
        add_game_point(
            redis_obj,
            f'player_tg_{update.message.chat_id}:win_record'
        )
        return NEW_QUESTION_REQUEST
    update.message.reply_text('Неправильно... Попробуешь еще раз?')
    add_game_point(
        redis_obj,
        f'player_tg_{update.message.chat_id}:loss_record'
    )
    return SOLUTION_ATTEMPT


def handle_give_up(bot, update):
    key_for_player_question_ids = f'player_tg_{update.message.chat_id}:question_ids'
    last_player_question = get_last_player_question(
        redis_obj,
        key_for_player_question_ids
    )
    update.message.reply_text(f'Ответ:\n{last_player_question["answer"]}.')
    add_game_point(
        redis_obj,
        f'player_tg_{update.message.chat_id}:loss_record'
    )
    new_question_and_answer = get_question_and_answer(
        redis_obj,
        key_for_player_question_ids
    )
    update.message.reply_text(
        f'Новый вопрос:\n{new_question_and_answer["question"]}'
    )
    return SOLUTION_ATTEMPT


def handle_player_score(bot, update):
    win_record, loss_record = get_player_score(
        redis_obj,
        f'player_tg_{update.message.chat_id}'
    )
    update.message.reply_text(
        f'Ваш счет\nПравильные ответы: {win_record}\nНеправильные ответы: {loss_record}'
    )
    return SOLUTION_ATTEMPT


def cancel(bot, update):
    username = update.message.from_user.first_name
    update.message.reply_text(
        f'{username}, надеюсь, когда-нибудь мы сыграем вновь!')
    return ConversationHandler.END


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
                RegexHandler('^Мой счет$', handle_player_score),
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
