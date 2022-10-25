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
import csv
import pathlib
import pandas
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.tokenize import word_tokenize
import string
from nltk.stem.porter import PorterStemmer
from nltk.corpus import stopwords


data_dir = "../../../data"
root = pathlib.Path(__file__).parent.resolve()
client = GraphqlClient(endpoint="https://api.github.com/graphql")
TOKEN = "2980cff9724515b7c161badcd0e9e0d9b180474d"
issues_data = []


# issue_no: issue_lables: pull_info: pull_no: pull_lables:
def make_query(issue_url):
    return """
{

  issue: resource(url: "ISSUE_URL"){
    ... on Issue{
      issue_no: number
      issue_url: url
      issue_title: title
      issue_body: body
      issue_repository: repository{
        nameWithOwner
      }
      
      issue_comments: comments(first: 20){
        edges{
          node{         
            comment_body: body
          }
        }
      }
      
      created_at: createdAt
      closed_at: closedAt
      
      issue_labels: labels(first: 6){
        edges{
          node{
            label: name
          }
        }
      }
      
      
      timelineItems(first: 10, itemTypes: [CROSS_REFERENCED_EVENT, UNMARKED_AS_DUPLICATE_EVENT, MENTIONED_EVENT, CLOSED_EVENT]) {
          ... on IssueTimelineItemsConnection {
            nodes {
              ... on CrossReferencedEvent @include(if: true) {
                pull_info: source {
                  ... on PullRequest {
                    pull_no: number
                    pull_url: url
                    pull_title: title
                    pull_body: bodyText
                    repository{
        			    nameWithOwner
      				}
      				issue_comments: comments(first: 20){
                        edges{
                            node{         
                                comment_body: body
                            }
                        }
                    }
      				createdAt
      				closedAt
                    pull_lables: labels(first: 10) {
                      nodes {
                        lable: name
                        description
                      }
                    }
                    commits: commits(first: 10) {
                      nodes {
                        commit: commit {
                          commit_url: commitUrl
                          commit_message: message
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
""".replace("ISSUE_URL", issue_url)


def fitch_issues(csv_in, json_out):

    result = pandas.read_csv(str(csv_in))
    # i = 0
    total_issues_count = result['issue_url'].count()
    progress = 0
    for issue_url in result['issue_url']:
        data = client.execute(
            query=make_query(issue_url),
            headers={"Authorization": "Bearer {}".format(TOKEN)},
        )
        data = remove_empty_elements(data)
        # print(data)
        if "data" in data and "issue" in data["data"] and data["data"]["issue"] is not None:
            issues_data.append(data["data"]["issue"])
            progress += 1
            printProgressBar(progress, total_issues_count, prefix='Progress:', suffix='Complete', length=50)
        # i = i + 1
        # if i > 10:
        #     break

    # print(issues_data)
    file = open(json_out, 'w+')
    file.write(json.dumps(issues_data, indent=4))
    issues_data.clear()


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


def convert_json_to_csv(json_file, csv_file):
    # create csv file
    csv_file_table = open(str(csv_file), "w", encoding="utf-8")
    csv_table = csv.writer(csv_file_table)
    # Write CSV Header, If you dont need that, remove this line
    # issue_no	issue_url	issue_title	issue_body	issue_repo	created_at	closed_at	issue_comments	issue_lables	pull_nos	pull_urls	pull_titles	pull_bodies	pull_comments	pull_lables	pull_commits
    csv_table.writerow(
        ["cluster", "url", "title", "body", "repo", "created_at", "closed_at", "comment", "label"])

    with open(str(json_file), encoding="utf-8") as f:
        json_data = json.load(f)
        vectorizer = TfidfVectorizer(stop_words={'english'})
        for i in range(len(json_data)):
            # remove unlinked issues
            if "timelineItems" not in json_data[i]:
                print(json_data[i]["issue_url"])
                continue

            issue_comments = ""
            if "issue_comments" in json_data[i]:
                for comment in json_data[i]["issue_comments"]["edges"]:
                    issue_comments += comment["node"]["comment_body"] + "|"

            issue_lables = ""
            if "issue_lables" in json_data[i]:
                for lable in json_data[i]["issue_lables"]["edges"]:
                    issue_lables += lable + "|"

            csv_table.writerow([
                i,
                json_data[i]["issue_url"],
                clean_text(json_data[i]["issue_title"]),
                clean_text(json_data[i]["issue_body"]),
                json_data[i]["issue_repository"]["nameWithOwner"],
                json_data[i]["created_at"] if "created_at" in json_data[i] else "",
                json_data[i]["closed_at"] if "closed_at" in json_data[i] else "",
                clean_text(issue_comments),
                issue_lables
            ])


            for node in json_data[i]["timelineItems"]["nodes"]:
                pull_nos = str(node["pull_info"]["pull_no"])
                pull_urls = node["pull_info"]["pull_url"]
                pull_titles = node["pull_info"]["pull_title"]
                pull_bodies = node["pull_info"]["pull_body"]

                pull_comments = ""
                pull_lables = ""
                pull_commits_urls = ""
                pull_commits_messages = ""

                if "pull_lables" in node:
                    for lable in node["pull_info"]["pull_lables"]["nodes"]:
                        pull_lables += lable + "|"

                if "commits" in node:
                    for commit in node["pull_info"]["pull_commits"]["nodes"]:
                        pull_commits_urls += commit["commit"]["commit_url"] + "|"
                        pull_commits_messages += commit["commit"]["commit_message"] + "|"

                csv_table.writerow([
                    i,
                    pull_urls,
                    clean_text(pull_titles),
                    clean_text(pull_bodies),
                    node["pull_info"]["repository"]["nameWithOwner"],
                    node["pull_info"]["createdAt"] if "createdAt" in node["pull_info"] else "",
                    node["pull_info"]["closedAt"] if "closedAt" in node["pull_info"] else "",
                    clean_text(pull_comments + "|" + pull_commits_messages),
                    pull_lables
                ])

            # if i > 2:
            #     break

    # csv_file_table.close()


def clean_text(text):
    # split into words
    tokens = word_tokenize(text)

    # convert to lower case
    tokens = [w.lower() for w in tokens]

    # remove punctuation from each word
    table = str.maketrans('', '', string.punctuation)
    stripped = [w.translate(table) for w in tokens]

    # remove remaining tokens that are not alphabetic
    words = [word for word in stripped if word.isalpha()]

    # filter out stop words
    stop_words = set(stopwords.words('english'))
    words = [w for w in words if w not in stop_words]
    # print(words)

    # stemming of words
    porter = PorterStemmer()
    stemmed = [porter.stem(word) for word in words]

    # print(stemmed)
    # print('----------------------------------------------------------------------------')
    return stemmed



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

    data_dir = "../../../data"
    root = pathlib.Path(__file__).parent.resolve()
    csv_file_name_in = "android_closed_issues_2011-01-01_2021-01-01_all_clean.csv"
    json_file_name_out = "android_closed_issues_2011-01-01_2021-01-01_all_clean_issues.json"
    csv_file_name_out = "android_closed_issues_2011-01-01_2021-01-01_all_clean_issues.csv"

    csv_in = root / data_dir / csv_file_name_in
    json_out = root / data_dir / json_file_name_out
    csv_out = root / data_dir / csv_file_name_out

    # fitch_issues(csv_in, json_out)
    # print(json_file_name_out + " is created")

    convert_json_to_csv(json_out, csv_out)
    print(">> " + csv_file_name_out + " is created")