import json
import pathlib
from typing import List
import re
from python_graphql_client import GraphqlClient
import os
import time
from collections import OrderedDict
import datetime
from datetime import datetime as dt


repos = {} #or using dict()
issues_data = []


def extract_reops(file):
    f = open(file)
    data = json.load(f)
    for i in range(len(data)):
        issue_no = data[i]["issu_no"]
        issue_url = data[i]["url"]
        repo_name = get_repo_name(issue_url)

        if repo_name in repos:
            repos[repo_name].append(issue_no)
        else:
            repos[repo_name] = [issue_no]
    print(repos)
    print("------------------------------------------")
    print("Repos # is", len(repos))
    print("------------------------------------------")



def get_repo_name(url):
    # github_pre = "https://github.com/todotxt/todo.txt-android/issues/103"
    pattern = "https://github.com/(.*?)/issues"
    substring = re.search(pattern, url).group(1)
    return substring


def search_duplicate_issues(file):
    f = open(file)
    data = json.load(f)
    for i in range(len(data)):
        issue_url = data[i]["url"]
        repo_name = get_repo_name(issue_url)
        # print(repo_name)
        for issue_no in repos.get(repo_name):
            # print(issue_no)
            for k in range(len(data[i]["comments"]["nodes"])):
                pattern1 = "duplicate of #" + str(issue_no)
                pattern2 = "duplicate of issue #" + str(issue_no)
                text = data[i]["comments"]["nodes"][k]
                search1 = str(text).find(pattern1)
                search2 = str(text).find(pattern2)
                if search1 != -1 or search2 != -1:
                    print("------------------------------------------")
                    print(repo_name)
                    print(issue_no)
                    print(data[i]["issu_no"])
                    print("------------------------------------------")



if __name__ == "__main__":
    # init time execution
    start_time = time.time()
    print("---------------------------------------------------")
    print()

    # extract repos and issues_no
    data_dir = "../../../data"
    root = pathlib.Path(__file__).parent.resolve()
    fileName = "android_linked_closed_issues_2011_2021.md"
    dataPath = root / data_dir / fileName
    extract_reops(dataPath)

    # match duplicate issues
    fileName = "android_duplicate_issues.json"
    dataPath = root / data_dir / fileName
    search_duplicate_issues(dataPath)

    print()

    print("---------------------------------------------------")
    print("--- Execution Time: %s seconds ---" % (time.time() - start_time))
    print("---------------------------------------------------")