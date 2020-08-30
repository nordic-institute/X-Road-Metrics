import json

def read_data_from_json(path):
    with open(path) as json_file:
        data = [json.loads(line.strip()) for line in json_file]

    return data