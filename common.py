from enum import Enum
from typing import Dict, Any, List, Union, Optional
from prompt1 import *


import json
import logging
import os
import openai
import sys


logger = logging.getLogger(__name__)


class AgentOutputParser:
        
    def parse(self, text: str) -> Any:
        cleaned_output = text.strip()
        cleaned_output = cleaned_output.replace('AI: ', '')
        cleaned_output = cleaned_output.replace("```", "").replace("```", "")
        cleaned_output = cleaned_output.strip()
        # chatgpt might forget about json when answering
        if '{' in cleaned_output:
            try:
                response = json.loads(cleaned_output)
            except json.decoder.JSONDecodeError as e:
                logger.exception("error parsing this text:\n" + cleaned_output)
                raise e
        else:
            return {"action": "Answer", "action_input": cleaned_output}
        return response


class Result:
    pass


class Ok(Result):
    def __init__(self, result: Any=None):
        self.result = result
        
    def __str__(self):
        return f'Result({self.result})'


class Error(Result):
    def __init__(self, err_msg: str, e: Optional[Exception]=None):
        self.error_string = err_msg
        self.exception = e
        
    def __str__(self):
        return f'Error({self.error_string}, {self.exception})'


class MessageType(Enum):
    ASSISTANT = "assistant"
    SYSTEM = "system"
    USER = "user"
    
    def to_dict(self, content: str) -> Dict[str, str]:
        return {"role": self.value, "content": content}


class Message:
    def __init__(self, message_type: MessageType, content: str):
        self.type = message_type
        self.content = content
        
    def setContent(self, content) -> None:
        self.content = content
        
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.type.value, "content": self.content}
    
    def __str__(self):
        return self.content
    
    def __repr__(self):
        return f"Message({self.type}, {self.content})"


class IChat:
    def __call__(self, *message: Message) -> Message:
        raise NotImplementedError("__call__ is not implemented in " + str(self))


class OpenAIChat(IChat):
    def __init__(self, model_name, temperature):
        self.model_name = model_name
        self.temperature = temperature
        
    def __call__(self, *message: Message) -> Message:
        # convert messages to dicts
        msgs = [m.to_dict() for m in message]
        logger.debug("passing to chatgpt: %s", msgs)
        response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=msgs,
                temperature=self.temperature)
        text = response['choices'][0]['message']['content']
        logger.debug('chatgpt response %s', text)
        return Message(MessageType.ASSISTANT, text)


class ChatWithHistory(IChat):
    def __init__(self, chatbot: OpenAIChat):
        self.chatbot = chatbot
        self.history = []
        
    def add_history(self, msg: Message):
        self.history.append(msg)

    def __call__(self, *message: Message) -> Message:
        self.history.extend(message)
        reply = self.chatbot(*self.history)
        self.history.append(reply)
        return reply


class Tool:
    def __init__(self, name: str, func: callable, description: str):
        self.name = name
        self.func = func
        self.description = description
        
    def __call__(self, message: str) -> Union[str, None]:
        """Runs the tool's callback function"""
        return self.func(message)
