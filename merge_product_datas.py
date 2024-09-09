import concurrent.futures
import csv
import json
import os


def get_product_data(args) -> list[dict]:
    [i, file_path] = args
    if i%100 == 0:
        print(f"{os.path.dirname(file_path)} - {i//100}")

    with open(file_path, "r", encoding="utf-8") as f:
        product_data = json.loads(f.read())

    if os.path.dirname(file_path).endswith("s"):
        return product_data
    else:
        return [product_data]


def merge_product_data(sub_dir):
    dir_path = f"./data/{sub_dir}"
    file_paths = [f"{dir_path}/{file_name}" for file_name in os.listdir(dir_path)]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = []
        for ret in list(executor.map(get_product_data, enumerate(file_paths))):
            result.extend(ret)

    json_dir = f"./json_data"
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    with open(f"{json_dir}/{sub_dir}.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(result, indent=4, ensure_ascii=False))
    
    csv_dir = f"./csv_data"
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)

    with open(f"{csv_dir}/{sub_dir}.csv", "w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=result[0].keys())
        writer.writeheader()
        writer.writerows(result)


def merge_product_datas():
    sub_dirs = [sub_dir for sub_dir in os.listdir("./data") if sub_dir != "merged"]
    with concurrent.futures.ProcessPoolExecutor(len(sub_dirs)) as executor:
        result = list(executor.map(merge_product_data, sub_dirs))

if __name__ == "__main__":
    merge_product_datas()
