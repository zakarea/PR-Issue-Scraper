from python_graphql_client import GraphqlClient
import feedparser
import httpx
import json
import pathlib
import re
import os
import time
from collections import OrderedDict
import datetime
from datetime import datetime as dt

# import calendar


data_dir = "../../../data"
repos_dir = "../../../repos"
root = pathlib.Path(__file__).parent.resolve()
client = GraphqlClient(endpoint="https://api.github.com/graphql")
TOKEN = "2980cff9724515b7c161badcd0e9e0d9b180474d"
# 2980cff9724515b7c161badcd0e9e0d9b180474d
# c7944bbaa7e4bca773d401f26cbd3f621a8a1465
issues_data = []
progress = 0


def replace_chunk(content, marker, chunk):
    r = re.compile(
        r"<!\-\- {} starts \-\->.*<!\-\- {} ends \-\->".format(marker, marker),
        re.DOTALL,
    )
    chunk = "<!-- {} starts -->\n{}\n<!-- {} ends -->".format(marker, chunk, marker)
    return r.sub(chunk, content)


def make_query_count_issues(date):
    return """
{
  search(query: "Android created:<DATE is:closed type:issue is:issue linked:pr", type: ISSUE, first: 1) {
    issueCount
  }
}
""".replace("DATE", str(date))


# search(query: "Android created:DATE language:kotlin is:closed is:issue linked:pr sort:reactions", type: ISSUE, first: 20, after: AFTER) {
# [CROSS_REFERENCED_EVENT, UNMARKED_AS_DUPLICATE_EVENT, MENTIONED_EVENT, CLOSED_EVENT])
def make_query(date, after_cursor=None, name="", owner=""):
    return """
{
    rateLimit {
    limit
    cost
    remaining
    resetAt
  }
  search(query: "Android created:DATE language:Kotlin is:closed is:issue linked:pr sort:reactions", type: ISSUE, first: 20, after: AFTER) {

    issueCount
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Issue {
        issue_no: number
        url
        title
        bodyText
        issue_lables: labels(first: 10) {
          nodes {
            name
            description
          }
        }
        timelineItems(first: 10, itemTypes: [CROSS_REFERENCED_EVENT]) {
          ... on IssueTimelineItemsConnection {
            nodes {
              ... on CrossReferencedEvent @include(if: true) {
                pull_info: source {
                  ... on PullRequest {
                    pull_no: number
                    url
                    title
                    bodyText
                    pull_lables: labels(first: 10) {
                      nodes {
                        name
                        description
                      }
                    }
                    commits(first: 10) {
                      nodes {
                        commit {
                          commitUrl
                          # message
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
""".replace("AFTER", '"{}"'.format(after_cursor) if after_cursor else "null"). \
        replace("DATE", str(date))


def fetch_releases(oauth_token, started_date, total_count):
    releases = []
    has_next_page = True
    after_cursor = None

    while has_next_page:
        data = client.execute(
            query=make_query(started_date, after_cursor),
            headers={"Authorization": "Bearer {}".format(oauth_token)},
        )

        # print(data)

        if "data" in data and "search" in data["data"] and "pageInfo" in data["data"]["search"]:
            has_next_page = data["data"]["search"]["pageInfo"]["hasNextPage"]
            after_cursor = data["data"]["search"]["pageInfo"]["endCursor"]
            # print("  ", has_next_page, "   ", after_cursor)
            # print("  " , data["data"]["rateLimit"]["remaining"])

            # if (has_next_page == False):
            #     print("after_cursor = " + after_cursor)

        if "data" in data and "search" in data["data"] and "nodes" in data["data"]["search"]:
            data = remove_empty_elements(data)
            # data = remove_unlinked_issus(data)

        if "data" in data and "search" in data["data"] and "nodes" in data["data"]["search"]:

            issues_count_size = len(data["data"]["search"]["nodes"])
            global progress
            progress += issues_count_size
            printProgressBar(progress, total_count, prefix='Progress:', suffix='Complete', length=50)

            issues_data.extend(data["data"]["search"]["nodes"])

            # check Github limit
            if int(data["data"]["rateLimit"]["cost"]) > int(data["data"]["rateLimit"]["remaining"]):
                # wait_until = datetime(data["data"]["rateLimit"]["resetAt"])
                # current_time = datetime.datetime.today()
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


def remove_unlinked_issus(data):
    delete = False
    if "data" in data and "nodes" in data["data"]["search"]:
        for i in range(len(data["data"]["search"]["nodes"])):
            if "timelineItems" not in data["data"]["search"]["nodes"][i]:
                del data["data"]["search"]["nodes"][i]
                delete = True
                break

        if delete:
            if i < len(data["data"]["search"]["nodes"]):
                return remove_unlinked_issus(data)
        if i < len(data["data"]["search"]["nodes"]) - 1:
            return remove_unlinked_issus(data)
        else:
            return data
    else:
        # print(data)
        data.clear()
        return data


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


def printProgressBar(iteration, total=1, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd=''):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    if total == 0:
        total = 1
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)

    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)

    # Print New Line on Complete
    if iteration == total:
        print()


def calculate_issues_count(oauth_token, start_date, end_date):
    data = client.execute(
        query=make_query_count_issues(str(start_date)),
        headers={"Authorization": "Bearer {}".format(oauth_token)},
    )

    if "data" not in data:
        return 0

    start = int(data["data"]["search"]["issueCount"])

    data = client.execute(
        query=make_query_count_issues(str(end_date)),
        headers={"Authorization": "Bearer {}".format(oauth_token)},
    )
    end = int(data["data"]["search"]["issueCount"])

    return end - start


if __name__ == "__main__":
    start_time = time.time()
    print("---------------------------------------------------")
    print()

    start_date = datetime.date(2011, 1, 1)
    end_date = datetime.date(2021, 1, 1)  # datetime.date.today()
    str_start_date = str(start_date)
    str_end_date = str(end_date)
    issues_count = calculate_issues_count(TOKEN, start_date, end_date)

    print(issues_count)

    try:
        while start_date <= end_date:
            releases = fetch_releases(TOKEN, start_date, issues_count)
            # print(start_date)
            start_date += datetime.timedelta(days=1)
    except:
        print()
        print("Exception happened, execution stoped until one hour and will start one hour after " + str(dt.now()))
        time.sleep(60 * 60)

    fileName = "issues_" + str_start_date + "_" + str_end_date + "_Kotlin_CROSS_REFERENCED_EVENT.md"
    dataPath = root / data_dir / fileName
    file = open(dataPath, 'w+')
    file.write(json.dumps(issues_data, indent=4))
    issues_data.clear()
    print(">> " + fileName + " is created")
    print()

    print("---------------------------------------------------")
    print("--- Execution Time: %s seconds ---" % (time.time() - start_time))
    print("---------------------------------------------------")