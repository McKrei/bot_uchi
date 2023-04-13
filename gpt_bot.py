import re
import random
import time
from multiprocessing import Process

import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from config import TOKEN, API_KEY, settings
import openai


bot = telebot.TeleBot(TOKEN)
openai.api_key = API_KEY

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton('О проекте'))


def get_images(text):
    image_resp = openai.Image.create(prompt=text, n=1, size="256x256")
    return image_resp['data']


class Users:
    with open('users.txt', 'r') as f:
        users = list(map(int, re.findall(r'\d+', f.read())))

    @staticmethod
    def add(user_id):
        print(Users.users, user_id)
        if user_id not in Users.users:
            Users.users.append(user_id)
            with open('users.txt', 'a') as f:
                f.write(f'{user_id}\n')
        print(Users.users)

def get_answer(question):
    """
    Получает ответ на вопрос с помощью модели GPT-3.5.
    :param question: Вопрос, на который нужно ответить.
    :return: Строка с ответом на вопрос.
    """

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=[
            {"role": "user", "content": question},
            {"role": "system", "content": "Ответь в стиле жириновского с юмором и провокацией", "name": "example_assistant"},

            # {"role": "system", "content": f"Ты {random.choice(settings)} жириновский"},
        ]
    )
    return completion.choices[0].message.content.strip()


def get_anecdote():
    """
    Получает анекдот с помощью модели GPT-3.5.
    :return: Строка с анекдотом.
    """
    theme_lst = ['программиста', 'политику', 'математика', 'медицину']
    print('Получаю анекдот')
    anecdote = get_answer(f'Расскажи анекдот про {random.choice(theme_lst)}')
    for user in Users.users:
        bot.send_message(user, anecdote)

@bot.message_handler(regexp='Картинка: ')
def send_image(message):
    """
    Отправляет картинку пользователю.
    """
    bot.send_message(message.chat.id, 'Ща нарисую... ', reply_markup=keyboard)
    text = 'Draw with crayons like a 10 year old politician Zhirinovsky and ' + message.text.replace('Картинка: ', '')
    imgs = get_images(text)
    for img in imgs:
        bot.send_photo(message.chat.id, img['url'], reply_markup=keyboard)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """
    Отправляет приветственное сообщение пользователю при запуске бота.
    """
    Users.add(message.chat.id)
    text = 'Привет! Я умею отвечать на вопросы. Напиши мне свой вопрос, и я постараюсь ответить на него.\n'
    bot.send_message(message.chat.id, text, reply_markup=keyboard)


@bot.message_handler(regexp='О проекте')
def send_about(message):
    """
    Отправляет информацию о проекте пользователю.
    """
    text = 'Этот бот создан с использованием модели GPT-3.5 от OpenAI. '\
           'Бот умеет отвечать на различные вопросы и предоставлять информацию по запросу.\n'
    bot.send_message(message.chat.id, text, reply_markup=keyboard)


@bot.message_handler(content_types=['text'])
def process_user_message(message):
    """
    Обрабатывает вопросы от пользователя и отправляет ответ.
    """
    question = message.text
    bot.send_message(message.chat.id, 'Погоди, дай подумать!', reply_markup=keyboard)
    answer = get_answer(question)
    bot.send_message(message.chat.id, answer, reply_markup=keyboard)


def runbot():
    """
    Запускает бота.
    """
    bot.infinity_polling()

def send_message_users():
    """
    Проверяет, не пришло ли сообщение с анекдотом.
    """
    while True:
        get_anecdote()
        time.sleep(60 * 60)


def main(param_proc_list):
    param_proc_dict = {i: par for i, par in enumerate(param_proc_list)}
    proc_dict = {i: Process(**param) for i, param in param_proc_dict.items()}
    while True:
        for id, proc in proc_dict.items():
            if not proc.is_alive():
                proc_dict[id] = Process(**param_proc_dict[id])
                proc_dict[id].start()
        time.sleep(60)



if __name__ == "__main__":
    main(param_proc_list=[{'target': runbot}, {'target': send_message_users}])
