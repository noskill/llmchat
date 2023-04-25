"""
Lunch ordering but with structured menu
"""


from enum import Enum
from typing import Dict, Any, List, Union
from prompt1 import *
from log import setupLogger

import itertools
import json
import logging
import os
import openai
import sys
from common import *


logger = logging.getLogger()
# Load your API key from an environment variable or secret management service
openai.api_key = os.getenv("OPENAI_API_KEY")


def sys_exit(*args, **kwargs):
    sys.exit(0)


class MyOrder:
    def __init__(self, menu: List[str]):
        self.items = []
        self.menu = menu

    def add_item(self, item):
        if item not in self.menu:
            return 'there was an error in python code adding "{0}": there is no such item in the menu, there are only these dishes {1}'.format(item, self.menu)
        self.items.append(item)
        return self.get_order()
        
    def remove_item(self, item):
        try:
            self.items.remove(item)
        except ValueError as e:
            return 'there is no "{0}" in the order, currently order = {1} please try again'.format(item, self.items)
        return self.get_order()
    
    def __str__(self):
        return str(self.items)
    
    def get_order(self, *args, **kwargs):
        return str(self.items)


def main():
    def exit(*args, **kwargs):
        # save order to a file
        with open('order.txt','w') as f:
            f.write('\n'.join(order.items))
        sys_exit()
    
    setupLogger()

    ch = OpenAIChat(temperature=0, model_name='gpt-3.5-turbo')
    
    menu = open('indian_menu.json', 'rt').read().strip()
    json_menu = json.loads(menu)

    dishes_list = flat_list = list(itertools.chain(*[v.keys() for v in json_menu.values()]))
    order = MyOrder(dishes_list)
    
    tools = [
        Tool(
            name="stop",
            func=exit,
            description="""let know that order is complete and dialogue is ended
            Assistant:{{ "action": "stop" "action_input": "" }}
            TOOL RESPONSE: ok, dialogue is over
            """
        ),
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
    # create guide prompt
    resp = ch(Message(MessageType.USER, TEMPLATE_GUIDE.format(menu=menu))).content
    
    ch = ChatWithHistory(ch)
    ch.add_history(Message(MessageType.SYSTEM, PREFIX.format(menu=menu, guide=resp)))
    ch.add_history(Message(MessageType.USER, "NEVER provide TOOL RESPONSE!!!\
                           Wait for an actual response!!!"))
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
        ai_resp = ch(current_msg)
        ch.history[-2].setContent(str(ch.history[-2]).split("----------")[0])
        parsed = parse.parse(ai_resp.content)
        action = parsed['action']
        if 'Answer' == action:
            out = parsed['action_input']
        else:
            tool = tools[parsed['action']]
            result = tool(parsed["action_input"])
            logger.info(f'agent called {tool.name}({parsed["action_input"]}), got: {result}')
            if result is None:
                result = ''
            stack.append(Message(MessageType.SYSTEM, TEMPLATE_TOOL_RESPONSE.format(observation=result)))


if __name__ == '__main__':
    main()
