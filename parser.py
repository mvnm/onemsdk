from html.parser import HTMLParser
from typing import Union, TypeVar

from exceptions import MalformedHTMLException, ONEmSDKException
from model.node import Node
from model.tag import get_tag_cls, Tag


class Stack:
    def __init__(self):
        self.items = []

    def is_empty(self):
        return self.items == []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        return self.items.pop()

    def peek(self):
        return self.items[len(self.items) - 1]

    def size(self):
        return len(self.items)


StackT = TypeVar('StackT', bound=Stack)


class Parser(HTMLParser):
    def __init__(self):
        super(Parser, self).__init__()
        self.node: Union[Node, None] = None
        self.stack: StackT[Node] = Stack()

    def handle_starttag(self, tag, attrs):
        if self.node:
            raise Exception('Only one root tag permitted')

        tag_obj = Node(tag=tag, attrs=dict(attrs))

        if not self.stack.is_empty():
            last_tag_obj: Node = self.stack.peek()
            last_tag_obj.add_child(tag_obj)

        self.stack.push(tag_obj)

    def handle_endtag(self, tag):
        last_tag_obj: Node = self.stack.pop()

        if last_tag_obj.tag != tag:
            raise MalformedHTMLException(
                f'<{last_tag_obj.tag}> is the last opened tag, '
                f'but </{tag}> was received.'
            )

        if self.stack.is_empty():
            self.node = last_tag_obj

    def handle_startendtag(self, tag, attrs):
        tag_obj = Node(tag=tag, attrs=dict(attrs))
        last_tag_obj: Node = self.stack.peek()
        last_tag_obj.add_child(tag_obj)

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return
        data_bits = data.split()
        data = ' '.join(data_bits)
        last_tag_obj: Node = self.stack.peek()
        last_tag_obj.add_child(data)


def build_node(html: str) -> Node:
    parser = Parser()
    parser.feed(html)
    if not parser.stack.is_empty():
        raise MalformedHTMLException()
    return parser.node


def get_root_tag(node: Node) -> Tag:
    tag_cls = get_tag_cls(node.tag)

    if tag_cls.is_root():
        return tag_cls.from_node(node)

    raise ONEmSDKException(f'Invalid root node <{node.tag}>')


def parse_html(filename: str) -> Tag:
    with open(filename, mode='r') as f:
        html = f.read()
        node = build_node(html)
        root_tag = get_root_tag(node)
        return root_tag
