from .graph_builder import Node
from typing import List

class GraphSearcher:
    def __init__(self):
        self.__graph : dict = None
        
        self.up_decay = 0.8
        self.down_decay = 0.6
        
        self.max_depth = 1
        self.min_depth = 4 #Assuming depth 4 is minimal

    @property
    def graph(self):
        return self.__graph
    
    @graph.setter
    def graph(self, input):
        if not isinstance(input, dict):
            raise TypeError("Input must be a dictionary")
        self.__graph = input
        
    def __traverse_up(self, user : str, item : str):  
        user : Node = self.__graph[user]
        item : Node = self.__graph[item]
            
        if user.depth < item.depth:
            pass
        
        if user.depth == self.max_depth:
            pass
        
        depth = user.depth
        
        target : Node = self.__graph[user.parent.name]
        while depth > self.max_depth: #Assumes 1 parent
            if target.name == item.name:
                return self.up_decay ** abs(user.depth - item.depth)
            depth = target.depth
            target : Node = target.parent
        
        return None
            
    def __traverse_down(self, user : str, item : str):
        user : Node = self.__graph[user]
        item : Node = self.__graph[item]
        
        if user.depth > item.depth:
            pass
        
        if user.depth == self.min_depth: 
            pass
        
        target_list : List[Node] = user.children
                
        while target_list:
            current_node = target_list.pop(0) 

            if current_node.name == item.name and current_node.depth <= self.min_depth:
                return self.down_decay ** abs(user.depth - item.depth)

            if current_node.children:
                target_list.extend(current_node.children)
                
        return None 
    
    def rank(self, user : str, item : str):
        result = self.__traverse_up(user, item)
        
        if not result:
            result = self.__traverse_down(user, item)
            
        return result
                
                
            



