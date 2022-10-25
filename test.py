import re


if __name__ == "__main__":
    pattern = "(close|fix|resolve|solve)(.* ?)#([0-9]+)"
    pattern = "(close|closed|closes|fix|fixed|fixes|resolve|resolved|resolves|solve|solved|solves)( +(issue)? ?#([0-9]+))+"
    text = "A quick git blame reveals that we added the blur in order to fix #5514."
    search = re.search(pattern, text)
    if(search != None):
        search = re.search(pattern, text).group(0)
    print("---------------------------------------------------")
    print(search)