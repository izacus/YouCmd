#! /usr/bin/env python2

import argparse
import os
from fabulous.color import blue, yellow, green, fg256, magenta, bold, red
import yaml
from youtrack.connection import Connection

status_sort_map = {"Obsolete": 0, "Duplicate": 1, "Won't fix": 2, "Submitted": 3, "To be discussed": 4, "Open": 5, "In Progress": 6, "Fixed": 7, "Verified": 8 }
priority_sort_map = {"Show-stopper": 0, "Critical": 1, "Major": 2, "Normal": 3, "Minor": 4}


def parse_arguments():
    parser = argparse.ArgumentParser(description="A simple command-line interfact to YouTrack bug tracking system.")
    command_subparser = parser.add_subparsers(title="command", dest="command")
    list_subparser = command_subparser.add_parser("list", help="Lists all issues")
    list_subparser.add_argument("-a", "--all", action="store_true")

    show_subparser = command_subparser.add_parser("show", help="Shows issue details")
    show_subparser.add_argument("id")

    args = parser.parse_args()
    return args

def colorize_priority(priority, text):
    if priority == "Show-stopper":
        return bold(red(text))
    elif priority == "Critical":
        return bold(red(text))
    elif priority == "Major":
        return red(text)
    elif priority == "Normal":
        return green("N")

    return text

def get_priority_short_string(priority):
    if priority == "Show-stopper":
        string = colorize_priority(priority, "S")
    elif priority == "Critical":
        string = colorize_priority(priority, "C")
    elif priority == "Major":
        string = colorize_priority(priority, "M")
    elif priority == "Normal":
        string = colorize_priority(priority, "N")
    elif priority == "Minor":
        string = colorize_priority(priority, "M")
    else:
        string = "?"

    return "[" + string + "]"

def pad_string_to(string, length):
    spaces = length - len(string)
    return string + (spaces * " ")

def get_state_color(state):
    if state == "Open":
        return blue(state)
    elif state == "In Progress":
        return yellow(state)
    elif state == "Fixed":
        return green(state)
    else:
        return fg256("#AAA", state)


def pretty_print_issues(issues, details=False):
    for issue in sorted(issues, key=lambda i: (status_sort_map[i["State"]], priority_sort_map[i["Priority"]], i["id"])):
        state = issue["State"]

        summary = issue["summary"]
        if "Assignee" in issue:
            summary = summary + " " + bold(magenta("[{username}]".format(username=issue["Assignee"])))

        print "[{id}]{crit}{state}{summary}".format(state=pad_string_to("[" + get_state_color(state) + "]", 18),
                                                                   crit=get_priority_short_string(issue["Priority"]),
                                                                   id=fg256("#AAA", pad_string_to(issue["id"], 8)),
                                                                   summary=summary)
        if details:
            if "description" in issue:
                for line in issue["description"].split('\n'):
                    print pad_string_to("", 28) + fg256("#AAA", line)
                print ""
            else:
                print ""

def show_issues(youtrack, all=False):
    if all:
        filter = ""
    else:
        filter = "state: Open,{In Progress},Submitted"

    issues = youtrack.getIssues(configuration["project"], filter, 0, 500)
    pretty_print_issues(issues)

def show_issue_details(youtrack, id):
    issue = youtrack.getIssue(id)
    state = issue["State"]

    assignee = ""
    if "Assignee" in issue:
        assignee = magenta(" [Assigned to ") +   \
                   bold(magenta("{username}".format(username=issue["Assignee"]))) + \
                   magenta("]")

    print ""
    print fg256("#DDD", "--=== ") + issue["summary"] + fg256("#DDD", " ===--")
    print "[ID: {id}] [{crit}]{assignee} {state} ".format(state="[" + get_state_color(state) + "]",
                                                          assignee=assignee,
                                                          crit=colorize_priority(issue["Priority"], issue["Priority"]),
                                                          id=fg256("#AAA", issue["id"]))

    print ""
    if "description" in issue:
        for line in issue["description"].split('\n'):
            print fg256("#CCC", line)

    print "--"

    if int(issue["commentsCount"]) > 0:
        comments = sorted(youtrack.getComments(id), key=lambda c: c.created)
        for comment in comments:
            firstLine = True
            for line in comment["text"].split('\n'):
                if len(line.strip()) == 0:
                    continue

                if firstLine:
                    print pad_string_to(comment["authorFullName"] + ":", 28), fg256("#AAA", line)
                    firstLine = False
                else:
                    print pad_string_to("", 28), fg256("#AAA", line)


if __name__ == "__main__":
    args = parse_arguments()

    # Load configuration
    config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.yaml")
    configuration = yaml.load(file(config_file, "r"))

    # Establish connection
    youtrack = Connection(configuration["site"], configuration["authentication"]["username"], configuration["authentication"]["password"])

    if args.command == "list":
        show_issues(youtrack, all=args.all)
    elif args.command == "show":
        show_issue_details(youtrack, args.id)

