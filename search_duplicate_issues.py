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
client = GraphqlClient(endpoint="https://api.github.com/graphql")
TOKEN = "2980cff9724515b7c161badcd0e9e0d9b180474d"
issues_data = []


# class Repo(object):
#     repo_name: str
#     issues_no: List[int]


# def filter_duplicate_issues(json_files, merged_json_file):
#     issues_count = 0
#     issues = []
#     for json_file in json_files:
#         print('read file ' + str(json_file))
#         with open(str(json_file)) as f:
#             data = json.load(f)
#             # print(data[0])
#             issues.extend(data)
#
#     issues_count = len(issues)
#
#     file = open(str(merged_json_file), 'w+')
#     file.write(json.dumps(issues, indent=4))
#
#     return issues_count


def make_query(repo, after_cursor=None):
    return """
{
    rateLimit {
    limit
    cost
    remaining
    resetAt
  }
  search(query: " '''duplicate of #''' in:comments is:issue repo:REPO", type: ISSUE, first: 100, after: AFTER) {

    issueCount
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Issue {
        issue_no: number
        issue_url: url
        issue_title: title
        issue_body: bodyText
        issue_lables: labels(first: 5) {
          nodes {
            name
            description
          }
        }
         issue_comments: comments(first: 20){
          nodes{
            bodyText
          }
        }
      }
    }
  }
}
""".replace("AFTER", '"{}"'.format(after_cursor) if after_cursor else "null"). \
        replace("REPO", str(repo))


def fetch_releases(oauth_token, repo):
    releases = []
    has_next_page = True
    after_cursor = None

    while has_next_page:
        data = client.execute(
            query=make_query(repo, after_cursor),
            headers={"Authorization": "Bearer {}".format(oauth_token)},
        )

        print(data)

        if "data" in data and "search" in data["data"] and "pageInfo" in data["data"]["search"]:
            has_next_page = data["data"]["search"]["pageInfo"]["hasNextPage"]
            after_cursor = data["data"]["search"]["pageInfo"]["endCursor"]

        if "data" in data and "search" in data["data"] and "nodes" in data["data"]["search"]:
            data = remove_empty_elements(data)

            issues_data.extend(data["data"]["search"]["nodes"])

            # check Github limit
            if int(data["data"]["rateLimit"]["cost"]) > int(data["data"]["rateLimit"]["remaining"]):
                print()
                print("Execution stoped until one hour and will start one hour after " + str(dt.now()))
                time.sleep(60 * 60)
        elif "errors" in data:
            if data["errors"][0]["type"] == "RATE_LIMITED":
                print()
                print("Execution stoped until one hour and will start one hour after " + str(dt.now()))
                time.sleep(60 * 60)
            else:
                print("ERROR :(")
                print(data)

    return releases


def remove_empty_elements(d):
    """recursively remove empty lists, empty dicts, or None elements from a dictionary"""

    def empty(x):
        return x is None or x == {} or x == []

    if not isinstance(d, (dict, list)):
        return d
    elif isinstance(d, list):
        return [v for v in (remove_empty_elements(v) for v in d) if not empty(v)]
    else:
        return {k: v for k, v in ((k, remove_empty_elements(v)) for k, v in d.items()) if not empty(v)}


def extract_reops(file):
    f = open(file)
    data = json.load(f)
    # for i in range(len(data)):
    for i in range(10):
        issue_no = data[i]["issue_no"]
        issue_url = data[i]["issue_url"]
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


if __name__ == "__main__":
    # init time execution
    start_time = time.time()
    print("---------------------- -----------------------------")
    print()

    # extract repos and issues_no
    data_dir = "../../../data"
    root = pathlib.Path(__file__).parent.resolve()
    fileName = "android_closed_issues_2011-01-01_2021-01-01_all_clean_issues.json"
    dataPath = root / data_dir / fileName
    extract_reops(dataPath)

    # fetch duplicate issues in repos

    try:
        for key in repos:
            releases = fetch_releases(TOKEN, key)
    except:
        print()
        print("Exception happened, execution stoped until one hour and will start one hour after " + str(dt.now()))
        time.sleep(60 * 60)

    fileName = "android_closed_issues_2011-01-01_2021-01-01_all_clean_issues_duplicated.json"
    dataPath = root / data_dir / fileName
    file = open(dataPath, 'w+')
    file.write(json.dumps(issues_data, indent=4))
    issues_data.clear()
    print(">> " + fileName + " is created")
    print()

    print("---------------------------------------------------")
    print("--- Execution Time: %s seconds ---" % (time.time() - start_time))
    print("---------------------------------------------------")