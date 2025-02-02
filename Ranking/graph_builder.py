import json
from dataclasses import dataclass, field
from typing import Optional, List
from importlib import import_module

from utils import tag_encoder

@dataclass
class Node:
    name: int
    parent: Optional['Node'] = None
    children: List['Node'] = field(default_factory=list)
    depth: int = 1
    def __repr__(self):
        def _repr(node, indent=0):
            spacing = " " * indent
            result = f"{spacing}Node({node.name}, d={node.depth}"
            if node.parent:
                result += f", p={node.parent.name}"
            result += ")"
            for child in node.children:
                result += "\n" + _repr(child, indent + 2)
            return result
        return _repr(self)

class GraphBuilder:
    def __init__(self):
        with open("tags.json") as f:
            data = json.load(f)
            self.__node_dict = {}
            
            # Build top-level categories
            for category in data["computerScienceHierarchy"]:
                parent_name = tag_encoder(category["name"])
                parent_node = Node(name=parent_name, depth=1)
                self.__node_dict[parent_name] = parent_node
                
                # Add subfields as child nodes
                self.__add_children(parent_node, category["subfields"], depth=2)

    def __add_children(self, parent_node, subfields, depth):
        for subfield in subfields:
            child_name = tag_encoder(subfield["name"])
            child_node = Node(name=child_name, parent=parent_node, depth=depth)
            self.__node_dict[child_name] = child_node
            parent_node.children.append(child_node)
            
            if subfield["subfields"]:
                self.__add_children(child_node, subfield["subfields"], depth + 1)
    
    @property 
    def graph(self):
        return self.__node_dict

