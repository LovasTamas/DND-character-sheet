import os
import json

def filter_phb_recursive(obj):
    if isinstance(obj, list):
        return [
            filter_phb_recursive(item)
            for item in obj
            if not isinstance(item, dict)
            or item.get("source") in (None, "XPHB")
        ]

    elif isinstance(obj, dict):
        return {
            key: filter_phb_recursive(value)
            for key, value in obj.items()
        }

    return obj

def save_filtered_object(obj, path_to_original_file: str):
    try:
        splitted_end_of_new_path = path_to_original_file.split("\\")[5:]
    except Exception as e:
        splitted_end_of_new_path = ""
    end_of_new_path = "\\".join(splitted_end_of_new_path)
    new_path = os.path.join(os.getcwd(), "own-implementation", "my_data", end_of_new_path)
    if not os.path.exists(os.path.dirname(new_path)):
        os.makedirs(os.path.dirname(new_path))
    with open(new_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)

cwd = os.getcwd()
path = cwd+"\\own-implementation\\data"
error = False
for r, dir_name, file_names in os.walk(path):
    for file_name in file_names:
        file_path = os.path.join(r, file_name)
        with open(file_path, "r", encoding="utf-8") as opened_file:
            try:
                loaded_json = json.load(opened_file)
            except Exception as e:
                print(f"Got error {e} while loading file {file_path}")
                error = True
                break
        filtered_entries = filter_phb_recursive(loaded_json)
        save_filtered_object(filtered_entries, file_path)
    if error:
        pass

print(os.listdir(path))


class FilterSpells:
    def __init__(self):
        pass

    def filter_json(json_file: json):
        pass