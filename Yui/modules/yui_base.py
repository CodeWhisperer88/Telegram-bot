# Copyright (c) 2021 Itz-fork

from asyncio import sleep
from random import choice
from heroku3 import from_key

from Yui.data.yui_msgs import Emergency_Msgs
from Yui.data.database import Yui_Database
from Yui.data.defaults import Defaults
from .openai_yui import Yui_OpenAI
from .arq_yui import Yui_ARQ
from config import Config


class Yui_Base():
    """
    Base of Yui Chat bot
    """
    def __init__(self) -> None:
        if Config.ON_HEROKU:
            heroku_c = from_key(Config.HEROKU_API)
            self.heroku_app = heroku_c.app(Config.HEROKU_APP_NAME)
        else:
            self.heroku_app = None
            self.yui_sql_db = Yui_Database()

    async def get_answer_from_yui(self, quiz, usr_id):
        ai_engine = await self.get_ai_engine()
        try:
            yui_oai = Yui_OpenAI(ai_engine)
            # Get old / new chat log
            c_log = await yui_oai.get_chat_log(usr_id)
            # Asks quistion from yui (OpenAI)
            answ = await yui_oai.ask_yui(quiz, c_log)
            # Save the chat log of the user
            await yui_oai.append_and_save_chat_log(quiz, answ, usr_id, c_log)
            return answ
        except:
            try:
                yui_luna = Yui_ARQ(Config.ARQ_API_URL, Config.ARQ_KEY)
                # Asks question from Yui (Luna chat bot)
                return await yui_luna.ask_yui(quiz, usr_id)
            except:
                return await self.emergency_pick()

    async def reply_to_user(self, message, answer):
        chat_id = message.chat.id
        await message._client.send_chat_action(chat_id, "typing")
        # Sleeping for 2 seconds to make the bot more real
        await sleep(2)
        await message.reply_text(answer, reply_to_message_id=message.message_id)
        await message._client.send_chat_action(chat_id, "cancel")
    
    async def set_ai_engine(self, engine):
        if self.heroku_app:
            conf = self.heroku_app.config()
            conf["ENGINE"] = str(engine)
        else:
            await self.yui_sql_db.set_engine(engine)
    
    async def get_ai_engine(self):
        if self.heroku_app:
            conf = self.heroku_app.config()
            return conf["ENGINE"]
        else:
            engine = await self.yui_sql_db.get_engine()
            if not engine:
                return Defaults().Engine
            else:
                return engine
    
    async def emergency_pick(self):
        return choice(Emergency_Msgs)