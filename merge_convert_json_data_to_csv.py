import pathlib
import csv
import json
import pandas as pd



def convert_json_to_csv(json_files, csv_file):
    # create csv file

    csv_file_table = open(str(csv_file), "w+")
    csv_table = csv.writer(csv_file_table)
    # Write CSV Header, If you dont need that, remove this line
    csv_table.writerow(["issue_url", "pull_url"])

    for json_file in json_files:
        print('read file ' + str(json_file))
        with open(str(json_file)) as f:
            json_data = json.load(f)
            for i in range(len(json_data)):
                # issue_url = json_data[i]["url"]
                # print(issue_url)
                if "timelineItems" in json_data[i]:
                    for j in range(len(json_data[i]["timelineItems"]["nodes"])):
                        csv_table.writerow([
                            json_data[i]["url"],
                            json_data[i]["timelineItems"]["nodes"][j]["pull_info"]["url"]
                        ])
    csv_file_table.close()


def remove_duplicate_rows(csv_file, csv_file_cleaned):
    # remove duplicate rows in csv
    with open(str(csv_file), 'r') as in_file, open(str(csv_file_cleaned), 'w') as out_file:
        seen = set()  # set for fast O(1) amortized lookup
        for line in in_file:
            if line in seen: continue  # skip duplicate

            seen.add(line)
            out_file.write(line)
    out_file.close()


if __name__ == "__main__":
    print("---------------------------------------------------")
    print()
    data_dir = "../../../data"
    root = pathlib.Path(__file__).parent.resolve()
    jsonFileName1 = "android_closed_issues_2011-01-01_2021-01-01_v4.json"
    jsonFileName2 = "issues_2011-01-01_2021-01-01_CROSS_REFERENCED_EVENT.json"
    jsonFileName3 = "android_closed_issues_2011-01-01_2021-01-01_java.json"
    csvFileName1 = "android_closed_issues_2011-01-01_2021-01-01_all.csv"
    csvFileName2 = "android_closed_issues_2011-01-01_2021-01-01_all_clean.csv"
    json_files_name = [
        root / data_dir / jsonFileName1,
        root / data_dir / jsonFileName2,
        root / data_dir / jsonFileName3]
    csvFileName = root / data_dir / csvFileName1
    csvFileCleanedName = root / data_dir / csvFileName2

    convert_json_to_csv(json_files_name, csvFileName)
    print(">> " + csvFileName1 + " is created")
    remove_duplicate_rows(csvFileName, csvFileCleanedName)
    print(">> " + csvFileName2 + " is created")
    print()