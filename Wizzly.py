import json
import re
import sys
from io import StringIO
import requests
import telebot
from telebot.types import InputMediaVideo, InputMediaPhoto

from decouple import config

TOKEN = config('TOKEN')
KEY_ONE_API = config('KEY_ONE_API')
KEY_IRATEAM = config('KEY_IRATEAM')

class BotHandler:
    def __init__(self, api_token):
        self.bot = telebot.TeleBot(api_token)

    def commands_handel(self, message):
        if message.text == '/start':
            self.bot.reply_to(message, 'Hi, I am Wizzly')
        elif message.text.startswith('/wiz'):
            try:
                output = StringIO()
                sys.stdout = output
                eval(message.text.split()[1])
                sys.stdout = sys.__stdout__
                self.bot.send_message(message.chat.id, output.getvalue(), reply_to_message_id=message.message_id)
            except Exception as e:
                self.bot.send_message(message.chat.id, f"<b>Error:</b> {str(e)}", parse_mode="html",
                                      reply_to_message_id=message.message_id)

    def chat(self, message):
        text = message.text.split(' ', 1)[-1]
        url = f'https://one-api.ir/chatgpt/?token={KEY_ONE_API}&action=gpt3.5-turbo&q={text}'
        response = requests.get(url).json()
        output = response['result'][0]
        self.bot.reply_to(message, output)

    def chat_reply(self, message):
        try:
            text = message.text
            url = (f'https://gpt.irateam.ir/api/web.php?apikey={KEY_IRATEAM}&type=freegpt6&question={text}'
                   f'&user_id={message.from_user.id}')
            response = requests.get(url).json()
            output = response['results']['answer']
            self.bot.reply_to(message, output, parse_mode="Markdown")
        except Exception as e:
            self.bot.send_message(message.chat.id, f"<b>Error occurred:</b> {str(e)}", parse_mode="html",
                                  reply_to_message_id=message.message_id)

    def say_hello(self, message):
        chat_id = message.chat.id
        message_id = message.message_id
        if message.text == "سلام":
            self.bot.reply_to(message, "سلام عزیزم")
        elif message.text == "بای":
            self.bot.reply_to(message, "خدافظی😞")
        elif message.text == "ربات":
            self.bot.reply_to(message, "بله؟!")
        elif message.text.lower() == "up":
            show = json.dumps(message.json, indent=4, ensure_ascii=False)
            show = re.sub(r':\s+(.+),?', r': \1', show)
            self.bot.send_message(chat_id=chat_id, text=show, reply_to_message_id=message_id)
        elif message.text.startswith(('dn ', 'دانلود ')):
            sm = self.bot.reply_to(message, "<b>لطفا کمی صبر کنید... ⏳</b>", parse_mode="html")
            try:
                insta = requests.get(f"https://one-api.ir/instagram/?token={KEY_ONE_API}&action=getall&link="
                                     f"{message.text.split()[1]}&userinfo=true").json()
                medias = insta['result']['medias']
                str_ch = insta['result']['caption'].replace("u0040", "@")

                if medias and len(medias) <= 1:
                    media = medias[0]['media']
                    if media:
                        self.bot.send_video(chat_id, media, reply_to_message_id=message_id)
                        self.bot.send_message(chat_id, str_ch, None, reply_to_message_id=message_id)
                    else:
                        self.bot.send_message(chat_id, "پیامی برای ارسال وجود ندارد.", reply_to_message_id=message_id)
                else:
                    media_list = []

                    for media_item in medias:
                        media_type = media_item['type']
                        media_link = media_item['media']

                        if media_type in ['video', 'photo']:
                            media_dict = {'type': media_type, 'link': media_link}
                            media_list.append(media_dict)

                    if media_list:
                        media_objects = [InputMediaVideo(media_item['link'])
                                         if media_item['type'] == 'video'
                                         else InputMediaPhoto(media_item['link'])
                                         for media_item in media_list]
                        self.bot.send_media_group(chat_id, media_objects, reply_to_message_id=message_id)
                        self.bot.send_message(chat_id, str_ch, None, reply_to_message_id=message_id)
                    else:
                        self.bot.send_message(chat_id, "پیامی برای ارسال وجود ندارد.", reply_to_message_id=message_id)

            except Exception as e:
                self.bot.send_message(message.chat.id, f"<b>Error occurred:</b> {str(e)}", parse_mode="html",
                                      reply_to_message_id=message.message_id)

            self.bot.delete_message(chat_id, sm.message_id)

    def handle_commands(self):
        @self.bot.message_handler(commands=['start', 'wiz'])
        def send_start(message):
            self.commands_handel(message)

        @self.bot.message_handler(func=lambda message: True)
        def say_hello(message):
            if message.text.startswith(('ویزلی', 'chat')):
                self.chat(message)
            elif message.reply_to_message and message.reply_to_message.from_user.id == self.bot.get_me().id:
                self.chat_reply(message)
            else:
                self.say_hello(message)

    def start_bot(self):
        self.handle_commands()
        self.bot.infinity_polling(skip_pending=True, restart_on_change=True)


API_TOKEN = TOKEN
bot_handler = BotHandler(API_TOKEN)
bot_handler.start_bot()
