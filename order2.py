from enum import Enum
from typing import Dict, Any, List, Union
from prompt1 import *
from log import setupLogger

import json
import logging
import os
import openai


logger = logging.getLogger()
# Load your API key from an environment variable or secret management service
openai.api_key = os.getenv("OPENAI_API_KEY")



class AgentOutputParser:
        
    def parse(self, text: str) -> Any:
        cleaned_output = text.strip()
        cleaned_output = cleaned_output.replace('AI: ', '')
        cleaned_output = cleaned_output.replace("```", "").replace("```", "")
        cleaned_output = cleaned_output.strip()
        # chatgpt might forget about json when answering
        if '{' in cleaned_output:
            response = json.loads(cleaned_output)
        else:
            return {"action": "Answer", "action_input": cleaned_output}
        return response
    

class MyOrder:
    def __init__(self):
        self.items = []
    
    def add_item(self, item):
        self.items.append(item)
        return self.get_order()
        
    def remove_item(self, item):
        self.items.remove(item)
        return self.get_order()
    
    def __str__(self):
        return str(self.items)
    
    def get_order(self, *args, **kwargs):
        return ', '.join(self.items)


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
        
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.type.value, "content": self.content}



class OpenAIChat:
    def __init__(self, model_name, temperature):
        self.model_name = model_name
        self.temperature = temperature
        
    def __call__(self, messages: List[Message]) -> Message:
        # convert messages to dicts
        msgs = [m.to_dict() for m in messages]
        logger.debug("passing to chatgpt: %s", msgs)
        response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=msgs,
                temperature=self.temperature)
        text = response['choices'][0]['message']['content']
        logger.info('chatgpt response %s', text)
        return Message(MessageType.ASSISTANT, text)


class ChatHistory:
    def __init__(self, chatbot: OpenAIChat):
        self.chatbot = chatbot
        self.history = []
        
    def add_history(self, msg: Message):
        self.history.append(msg)

    def send_message(self, message: Message) -> Message:
        self.history.append(message)
        reply = self.chatbot(self.history)
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


def main():
    setupLogger()
    order = MyOrder()
    tools = [
        Tool(
            name="add_item",
            func=order.add_item,
            description="""adds dish to the order, return list of all dishes in the order
            Assistant:{{ "action": "add_item" "action_input": "tea" }}
            TOOL RESPONSE: tea
            """
        ),
        Tool(
            name="remove_item",
            func=order.remove_item,
            description="""remove a dish from the order, return list of all dishes in the order
            Assistant:{{ "action": "remove_item" "action_input": "tea" }}
            TOOL RESPONSE: ""
            """
        )]
    tools = {t.name: t for t in tools}
    ch = OpenAIChat(temperature=0, model_name='gpt-3.5-turbo')
    
    menu = "salads: olivier, greek salad. soups: tomato soup, chicken noodle soup(spicy). main courses: barbecue \
chicken, pesto pasta. drinks: tea, orange juice. deserts: creme brulee."
    ch = ChatHistory(ch)
    ch.add_history(Message(MessageType.SYSTEM, PREFIX.format(menu=menu)))
    parse = AgentOutputParser()
    
    out = "Please enter the message:"
    stack = []
    while True:
        if stack:
            current_msg = stack.pop()
        else:
            s = input(out + '\n')
            if s == 'Exit':
                return
            stack.append(Message(MessageType.USER, SUFFIX.format(input=s)))
            continue
        ai_resp = ch.send_message(current_msg)
        parsed = parse.parse(ai_resp.content)
        action = parsed['action']
        if 'Answer' == action:
            out = parsed['action_input']
        else:
            tool = tools[parsed['action']]
            result = tool(parsed["action_input"])
            if result is None:
                result = ''
            stack.append(Message(MessageType.SYSTEM, TEMPLATE_TOOL_RESPONSE.format(observation=result)))
        
if __name__ == '__main__':
    main()
