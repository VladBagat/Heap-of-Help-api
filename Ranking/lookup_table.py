"""This script takes tags.json and creates a lookup table. This will further be used to encode/decode tags for efficient storage."""
import json


class LookupTableGenerator:
    def __init__(self):
        pass
    
    def generate_lookup_table(self):
        """Generates a lookup table for tags.json"""
        
        with open("./tags.json", "r") as f:
            tags = json.load(f)

        result = {}    

        def flatten_json(y):
            """Flattens a nested json object
            Taken from: https://www.geeksforgeeks.org/flattening-json-objects-in-python/"""
            out = {}
            def flatten(x, name=''):
                if type(x) is dict:
                    for a in x:
                        flatten(x[a], name + a + '_')
                elif type(x) is list:
                    i = 0
                    for a in x:
                        flatten(a, name + str(i) + '_')
                        i += 1
                else:
                    out[name[:-1]] = x
            flatten(y)
            return out   
                    
        for i, (key, value) in enumerate(flatten_json(tags['computerScienceHierarchy']).items()):
            result.update({value: i})

        with open("lookup.json", "w") as out_file:
            json.dump(result, out_file, indent=4)
            
    @staticmethod
    def convert_int_to_tag(tags):
        """Converts an integer to a tag"""
        with open("lookup.json", "r") as out_file:
            lookup_table = json.load(out_file)
        return [list(lookup_table.keys())[list(lookup_table.values()).index(tag)] for tag in tags]

