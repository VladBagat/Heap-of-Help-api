import json
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Node:
    name: str
    parent: Optional['Node'] = None
    children: List['Node'] = field(default_factory=list)
    depth: int = 1

class GraphBuilder:
    def __init__(self):
        with open("tags.json") as f:
            data = json.load(f)
            self.__node_dict = {}
            
            # Build top-level categories
            for category in data["computerScienceHierarchy"]:
                parent_name = category["name"]
                parent_node = Node(name=parent_name, depth=1)
                self.__node_dict[parent_name] = parent_node
                
                # Add subfields as child nodes
                self.__add_children(parent_node, category["subfields"], depth=2)

    def __add_children(self, parent_node, subfields, depth):
        for subfield in subfields:
            child_name = subfield["name"]
            child_node = Node(name=child_name, parent=parent_node, depth=depth)
            self.__node_dict[child_name] = child_node
            parent_node.children.append(child_node)
            
            if subfield["subfields"]:
                self.__add_children(child_node, subfield["subfields"], depth + 1)
    
    @property 
    def graph(self):
        return self.__node_dict




