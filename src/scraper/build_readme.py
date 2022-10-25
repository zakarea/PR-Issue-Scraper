from python_graphql_client import GraphqlClient
import feedparser
import httpx
import json
import pathlib
import re
import os
import time
from collections import OrderedDict

dir = "../../../data"
version = 21
root = pathlib.Path(__file__).parent.resolve()
print(root)
client = GraphqlClient(endpoint="https://api.github.com/graphql")


TOKEN = "c7944bbaa7e4bca773d401f26cbd3f621a8a1465"

def replace_chunk(content, marker, chunk):
    r = re.compile(
        r"<!\-\- {} starts \-\->.*<!\-\- {} ends \-\->".format(marker, marker),
        re.DOTALL,
    )
    chunk = "<!-- {} starts -->\n{}\n<!-- {} ends -->".format(marker, chunk, marker)
    return r.sub(chunk, content)


def make_query(after_cursor=None):
    return """
query {
  repository(name: "scrapy", owner: "scrapy") {
    issues(states: CLOSED, first: 100, after:AFTER) {
      totalCount
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        issu_no: number
        issue_lables: labels(first: 10) {
          nodes {
            name
          }
        }
        timelineItems(first: 10, itemTypes: [CROSS_REFERENCED_EVENT, UNMARKED_AS_DUPLICATE_EVENT, MENTIONED_EVENT, CLOSED_EVENT]) {
          
          ... on IssueTimelineItemsConnection {
            nodes {
              ... on CrossReferencedEvent @include(if: true) {
                pull_info: source {
                  ... on PullRequest {
                    title
                    pull_no: number
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
""".replace(
        "AFTER", '"{}"'.format(after_cursor) if after_cursor else "null"
    )


def fetch_releases(oauth_token, version):
    repos = []
    releases = []
    repo_names = set()
    has_next_page = True
    after_cursor = None

    while has_next_page:
        data = client.execute(
            query=make_query(after_cursor),
            headers={"Authorization": "Bearer {}".format(oauth_token)},
        )




        data = remove_empty_elements(data)

        data = remove_unlinked_issus(data)
        data = remove_unlinked_issus(data)



        # issue_list = list(data["data"]["repository"]["issues"]["nodes"]).copy()
        # delet_issue = []
        #
        # i = 0
        # for issue in data["data"]["repository"]["issues"]["nodes"]:
        #     print(issue)
        #     # print(type(issue))
        #     # print(type(issue["timelineItems"]["nodes"]))
        #     if "timelineItems" not in issue:
        #         delet_issue.append(i)
        #     # else:
        #     #     for issue_info in issue["timelineItems"]["nodes"]:
        #     #         remove_unliked_issuess(issue_info)
        #             # if "pull_no" not in issue_info.items():
        #             #     delet_issue.append(i)
        #           #     break
        #
        #
        #     # elif "pull_no" not in [j for i in issue["timelineItems"]["nodes"] for j in i]:
        #     #     # print(type(issue["timelineItems"]["nodes"][0]))
        #     #     delet_issue.append(i)
        #     # else:
        #     #     if "pull_no" not in issue["timelineItems"]["nodes"]["pull_info"]:
        #     #         delet_issue.append(i)
        #     i += 1
        #
        # print(delet_issue)



        # print(len(data["data"]["repository"]["issues"]["nodes"]))
        # size = len(data["data"]["repository"]["issues"]["nodes"]) - 1
        # for i in range(size):
        #     print(i)
        #     if "pull_no" not in data["data"]["repository"]["issues"]["nodes"][i]:
        #         del data["data"]["repository"]["issues"]["nodes"][i]
        #         print(len(data["data"]["repository"]["issues"]["nodes"]))
        #         size = len(data["data"]["repository"]["issues"]["nodes"]) - 1
        #         i -= 1
        #         print(i)
        #         print()





        version += 1
        print()
        # print(json.dumps(data, indent=4))
        # dataPath.open("a").write(json.dumps(data, indent=4))
        fileName = "data" + str(version) + ".md"
        dataPath = root / dir / fileName
        file = open(dataPath, 'w+')
        file.write(json.dumps(data, indent=4))
        print(fileName + " is created")
        # for repo in data["data"]["viewer"]["repositories"]["nodes"]:
        #     if repo["releases"]["totalCount"] and repo["name"] not in repo_names:
        #         repos.append(repo)
        #         repo_names.add(repo["name"])
        #         releases.append(
        #             {
        #                 "repo": repo["name"],
        #                 "release": repo["releases"]["nodes"][0]["name"]
        #                 .replace(repo["name"], "")
        #                 .strip(),
        #                 "published_at": repo["releases"]["nodes"][0][
        #                     "publishedAt"
        #                 ].split("T")[0],
        #                 "url": repo["releases"]["nodes"][0]["url"],
        #             }
        #         )
        has_next_page = data["data"]["repository"]["issues"]["pageInfo"][
            "hasNextPage"
        ]
        # print(has_next_page)
        # dir = data["data"]["viewer"]["repositories"]["pageInfo"][
        #     "hasNextPage"
        # ]
        after_cursor = data["data"]["repository"]["issues"]["pageInfo"]["endCursor"]
        # print(after_cursor)
    return releases


def fetch_tils():
    sql = "select title, url, created_utc from til order by created_utc desc limit 5"
    return httpx.get(
        "https://til.simonwillison.net/til.json",
        params={"sql": sql, "_shape": "array",},
    ).json()


def fetch_blog_entries():
    entries = feedparser.parse("https://simonwillison.net/atom/entries/")["entries"]
    return [
        {
            "title": entry["title"],
            "url": entry["link"].split("#")[0],
            "published": entry["published"].split("T")[0],
        }
        for entry in entries
    ]

def remove_unlinked_issus(data):

    for i in range(len(data["data"]["repository"]["issues"]["nodes"])):
        if "timelineItems" not in data["data"]["repository"]["issues"]["nodes"][i]:
            del data["data"]["repository"]["issues"]["nodes"][i]
            break

    if i < len(data["data"]["repository"]["issues"]["nodes"]) - 1:
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

if __name__ == "__main__":
    start_time = time.time()

    fileName = "data" + str(version) + ".md"
    readme = root / dir / fileName
    releases = fetch_releases(TOKEN, version)

    print("--- %s seconds ---" % (time.time() - start_time))


    # releases.sort(key=lambda r: r["published_at"], reverse=True)
    # md = "\n".join(
    #     [
    #         "* [{repo} {release}]({url}) - {published_at}".format(**release)
    #         for release in releases[:5]
    #     ]
    # )
    # readme_contents = readme.open().read()
    # rewritten = replace_chunk(readme_contents, "recent_releases", md)

    # tils = fetch_tils()
    # tils_md = "\n".join(
    #     [
    #         "* [{title}]({url}) - {created_at}".format(
    #             title=til["title"],
    #             url=til["url"],
    #             created_at=til["created_utc"].split("T")[0],
    #         )
    #         for til in tils
    #     ]
    # )
    # rewritten = replace_chunk(rewritten, "tils", tils_md)

    # entries = fetch_blog_entries()[:5]
    # entries_md = "\n".join(
    #     ["* [{title}]({url}) - {published}".format(**entry) for entry in entries]
    # )
    # rewritten = replace_chunk(rewritten, "blog", entries_md)
    #
    # readme.open("w").write(rewritten)

