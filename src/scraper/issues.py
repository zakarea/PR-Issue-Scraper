from python_graphql_client import GraphqlClient
import feedparser
import httpx
import json
import pathlib
import re
import os
import time
from collections import OrderedDict


data_dir = "../../../data"
repos_dir = "../../../repos"
version = 21
root = pathlib.Path(__file__).parent.resolve()
print(root)
client = GraphqlClient(endpoint="https://api.github.com/graphql")

TOKEN = "c7944bbaa7e4bca773d401f26cbd3f621a8a1465"
issues_data = []


def replace_chunk(content, marker, chunk):
    r = re.compile(
        r"<!\-\- {} starts \-\->.*<!\-\- {} ends \-\->".format(marker, marker),
        re.DOTALL,
    )
    chunk = "<!-- {} starts -->\n{}\n<!-- {} ends -->".format(marker, chunk, marker)
    return r.sub(chunk, content)


def make_query(after_cursor=None, name="", owner=""):
    return """
{
  rateLimit {
    limit
    cost
    remaining
    resetAt
  }
  repository(name: "NAME", owner: "OWNER") {
    issues(states: CLOSED, first: 100, after: AFTER) {
      totalCount
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        issu_no: number
        url
        title
        bodyText
        issue_lables: labels(first: 10) {
          nodes {
            name
            description
          }
        }
        timelineItems(first: 10, itemTypes: [CROSS_REFERENCED_EVENT, UNMARKED_AS_DUPLICATE_EVENT, MENTIONED_EVENT, CLOSED_EVENT]) {
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
                          message
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
""".replace("AFTER", '"{}"'.format(after_cursor) if after_cursor else "null")\
        .replace("NAME", name)\
        .replace("OWNER", owner)


def fetch_releases(oauth_token, name, owner, progress = 0):
    releases = []
    has_next_page = True
    after_cursor = None

    while has_next_page:
        data = client.execute(
            query=make_query(after_cursor, name, owner),
            headers={"Authorization": "Bearer {}".format(oauth_token)},
        )


        # print(data, flush=True)

        total_count = int(data["data"]["repository"]["issues"]["totalCount"])
        issues_count = len(data["data"]["repository"]["issues"]["nodes"])
        progress += issues_count
        printProgressBar(progress, total_count, prefix='Progress:', suffix='Complete', length=50)

        data = remove_empty_elements(data)
        data = remove_unlinked_issus(data)

        issues_data.extend(data["data"]["repository"]["issues"]["nodes"])

        has_next_page = data["data"]["repository"]["issues"]["pageInfo"]["hasNextPage"]
        after_cursor = data["data"]["repository"]["issues"]["pageInfo"]["endCursor"]



    return releases




def remove_unlinked_issus(data):
    delete = False
    for i in range(len(data["data"]["repository"]["issues"]["nodes"])):
        if "timelineItems" not in data["data"]["repository"]["issues"]["nodes"][i]:
            del data["data"]["repository"]["issues"]["nodes"][i]
            delete = True
            break

    if delete:
        if i < len(data["data"]["repository"]["issues"]["nodes"]):
            return remove_unlinked_issus(data)
    if i < len(data["data"]["repository"]["issues"]["nodes"]) -1:
        return remove_unlinked_issus(data)
    else:
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


def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = ''):
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
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)

    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)

    # Print New Line on Complete
    if iteration == total:
        print()

if __name__ == "__main__":
    start_time = time.time()
    print("---------------------------------------------------")
    print()

    with open(root / repos_dir / 'repos.json') as f:
        repos = json.load(f)
        for repo in repos:
            print("start processing " + repo["name"] + "/" + repo["owner"])

            releases = fetch_releases(TOKEN, repo["name"], repo["owner"])

            fileName = repo["name"] + "_" + repo["owner"] + ".md"
            dataPath = root / data_dir / fileName
            file = open(dataPath, 'w+')
            file.write(json.dumps(issues_data, indent=4))
            issues_data.clear()
            print(">> " + fileName + " is created")
            print()

    print("---------------------------------------------------")
    print("--- Execution Time: %s seconds ---" % (time.time() - start_time))
    print("---------------------------------------------------")


