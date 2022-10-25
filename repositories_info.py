import csv
import pathlib
import pandas
import re


def fill_repos_urls(csv_in, csv_out):
    # create csv file
    csv_file_table = open(str(csv_out), "w+")
    csv_table = csv.writer(csv_file_table)
    # Write CSV Header, If you dont need that, remove this line
    # repo_name  repo_url  #linked_issues  #linked_pulls
    csv_table.writerow(["repo_name", "repo_url", "#linked_issues", "#linked_pulls"])
    result = pandas.read_csv(str(csv_in))

    # initialize a with set()
    repos_name_set = set()
    repos_url_set = set()
    repos_issues_set = set()

    for issue in result['issue_url']:
        repo_url = re.sub('(/issues/)(.* ?)', '', issue)
        repo_name = re.sub('(https://github.com/)', '', repo_url)
        repos_name_set.add(repo_name)
        repos_issues_set.add(issue)

    print("start grap repos info ...")
    for repo in repos_name_set:
        repo_url = 'https://github.com/' + repo
        issus_no = sum(repo in s for s in list(repos_issues_set))
        pulls_no = sum(repo in s for s in list(result['pull_url']))
        csv_table.writerow([repo, repo_url, issus_no, pulls_no])

    csv_file_table.close()



if __name__ == "__main__":
    data_dir = "../../../data"
    root = pathlib.Path(__file__).parent.resolve()
    csv_file_name_in = "android_closed_issues_2011-01-01_2021-01-01_all_clean.csv"
    csv_file_name_out = "android_closed_issues_2011-01-01_2021-01-01_repos.csv"
    csv_in = root / data_dir / csv_file_name_in
    csv_out = root / data_dir / csv_file_name_out
    fill_repos_urls(csv_in, csv_out)
    print(csv_file_name_out + " is created")
    # repos_names = get_repos_names()
