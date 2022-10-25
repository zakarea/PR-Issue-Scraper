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
from collections import Counter
import csv


repos = set()
statistics = dict()

def extract_reops(file):
    f = open(file)
    data = json.load(f)
    k = 0
    statistics = {'': {'repoName': '', 'issueNo': 0, 'pullNo': 0, 'commentIssueNo': 0, 'lableIssueNo': 0, 'commentPullNo': 0, 'commitsPullNo': 0, 'lablePullNo': 0, 'bodyIssueEmptyNo': 0, 'bodyPullEmptyNo': 0}}
    for i in range(len(data)):
        repo_name = data[i]["issue_repository"]["nameWithOwner"]
        if repo_name not in statistics:
            statistics[repo_name] = {'repoName': repo_name, 'issueNo': 0, 'pullNo': 0, 'commentIssueNo': 0, 'lableIssueNo': 0, 'commentPullNo': 0, 'commitsPullNo': 0, 'lablePullNo': 0, 'bodyIssueEmptyNo': 0, 'bodyPullEmptyNo': 0}
        # No of issues in repo
        issue_no = statistics[repo_name]["issueNo"] + 1
        # No of comments in issue
        comment_issue_no = 0
        if "issue_comments" in data[i] and "edges" in data[i]["issue_comments"]:
            comment_issue_no = statistics[repo_name]["commentIssueNo"] + len(data[i]["issue_comments"]["edges"])
        # No of lable in issue
        lable_issue_no = 0
        if "issue_labels" in data[i] and "edges" in data[i]["issue_labels"]:
            lable_issue_no = statistics[repo_name]["lableIssueNo"] + len(data[i]["issue_labels"]["edges"])
        empty_issue_body = 0
        if data[i]["issue_body"] == "":
            empty_issue_body += 1

        # No of pulls in issue + No of commit in pull->issue
        pull_no = 0
        comment_pull_no = 0
        commits_pull_no = 0
        lable_pull_no = 0
        empty_pull_body = 0
        if "timelineItems" in data[i] and "nodes" in data[i]["timelineItems"]:
            pull_no = statistics[repo_name]["pullNo"] + len(data[i]["timelineItems"]["nodes"])
            for pull in data[i]["timelineItems"]["nodes"]:
                if "issue_comments" in pull["pull_info"] and "edges" in pull["pull_info"]["issue_comments"]:
                    comment_pull_no = statistics[repo_name]["commentPullNo"] + len(pull["pull_info"]["issue_comments"]["edges"])
                if "commits" in pull["pull_info"] and "nodes" in pull["pull_info"]["commits"]:
                    commits_pull_no = statistics[repo_name]["commitsPullNo"] + len(pull["pull_info"]["commits"]["nodes"])
                if "pull_lables" in pull["pull_info"] and "nodes" in pull["pull_info"]["pull_lables"]:
                    lable_pull_no = statistics[repo_name]["lablePullNo"] + len(pull["pull_info"]["pull_lables"]["nodes"])
                if pull["pull_info"]["pull_body"] == "":
                    empty_pull_body = statistics[repo_name]["bodyPullEmptyNo"] + 1

        statistics[repo_name] = {'repoName': repo_name, 'issueNo': issue_no, 'pullNo': pull_no, 'commentIssueNo': comment_issue_no, 'lableIssueNo': lable_issue_no, 'commentPullNo': comment_pull_no, 'commitsPullNo': commits_pull_no, 'lablePullNo': lable_pull_no, 'bodyIssueEmptyNo': empty_issue_body, 'bodyPullEmptyNo': empty_pull_body}

    del statistics['']
    # print(statistics)
    headers = ['repoName', 'issueNo', 'pullNo', 'commentIssueNo', 'lableIssueNo', 'commentPullNo', 'commitsPullNo', 'lablePullNo', 'bodyIssueEmptyNo', 'bodyPullEmptyNo']
    with open('test.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for value in statistics.values():
            print(value)
            # writer.write("%s, %s\n" % (value, statistics[value]))
            writer.writerow(value)
    # print(statistics)


def get_repo_name(url):
    # github_pre = "https://github.com/todotxt/todo.txt-android/issues/103"
    pattern = "https://github.com/(.*?)/issues"
    substring = re.search(pattern, url).group(1)
    return substring


if __name__ == "__main__":
    # init time execution
    start_time = time.time()
    print("---------------------------------------------------")
    print()

    # extract repos and issues_no
    data_dir = "../../../data"
    root = pathlib.Path(__file__).parent.resolve()
    fileName = "android_closed_issues_2011-01-01_2021-01-01_all_clean_issues.json"
    dataPath = root / data_dir / fileName
    extract_reops(dataPath)


    # fileName = "android_closed_issues_2011-01-01_2021-01-01_all_clean_issues_statistics.json"
    # dataPath = root / data_dir / fileName
    # file = open(dataPath, 'w+')
    # file.write(json.dumps(issues_data, indent=4))
    # issues_data.clear()
    # print(">> " + fileName + " is created")
    # print()

    print("---------------------------------------------------")
    print("--- Execution Time: %s seconds ---" % (time.time() - start_time))
    print("---------------------------------------------------")