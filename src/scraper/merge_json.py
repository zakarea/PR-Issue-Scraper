
import json
import pathlib

def merge_issues(json_files, merged_json_file):
    issues_count = 0
    issues = []
    for json_file in json_files:
        print('read file ' + str(json_file))
        with open(str(json_file)) as f:
            data = json.load(f)
            # print(data[0])
            issues.extend(data)

    issues_count = len(issues)

    file = open(str(merged_json_file), 'w+')
    file.write(json.dumps(issues, indent=4))

    return issues_count


if __name__ == "__main__":

    print("---------------------------------------------------")
    print()

    data_dir = "../../../data"
    root = pathlib.Path(__file__).parent.resolve()
    fileName = "android_linked_closed_issues_2011_2021.md"
    dataPath = root / data_dir / fileName
    json_files_name = [
        root / data_dir / "android_closed_issues_2011-01-01_2012-01-01.md",
        root / data_dir / "android_closed_issues_2012-01-01_2013-01-01.md",
        root / data_dir / "android_closed_issues_2013-01-01_2014-01-01.md",
        root / data_dir / "android_closed_issues_2014-01-01_2015-01-01.md",
        root / data_dir / "android_closed_issues_2015-01-01_2016-01-01.md",
        root / data_dir / "android_closed_issues_2016-01-01_2017-01-01.md",
        root / data_dir / "android_closed_issues_2017-01-01_2018-01-01.md",
        root / data_dir / "android_closed_issues_2018-01-01_2019-01-01.md",
        root / data_dir / "android_closed_issues_2019-01-01_2020-01-01.md",
        root / data_dir / "android_closed_issues_2020-01-01_2021-01-01.md"]

    print("Issues # >> " + str(merge_issues(json_files_name, dataPath)))

    print(">> " + fileName + " is created")
    print()
