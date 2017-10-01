#! /usr/bin/env python
# coding: utf-8


from bs4 import BeautifulSoup
import requests
from time import sleep
from datetime import datetime
from argparse import ArgumentParser


parser = ArgumentParser(description='scrape biorxiv site for view data')
parser.add_argument('--pages', help='file containing paper titles and links', required=False)
parser.add_argument('--data', help='file containing link data (will resume from last paper in file)', required=False)
options = parser.parse_args()

def make_soup(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    return soup

def find_pages(url):
    """
    work out how many pages there are
    """
    soup = make_soup(url)
    div = soup.find("div", "highwire-list page-group-items item-list")
    page_range = int(div.findAll("li")[-1].a.string)
    return [url + "?page="+str(x) for x in range(1, page_range)]

def get_paper_links(url):
    """
    gets paper title and link for each paper on page
    apply to each page in archive
    """
    soup = make_soup(url)
    div = soup.findAll("div", "highwire-list")
    links = []
    for date in div:
        for i in date.findAll("li"):
            try:
                i.a.string
            except:
                pass
            else:  # hack
                if i.a.string == None:
                    pass
                elif len(i.a.string) < 5:
                    pass
                else:
                    links.append({"title": i.a.string,
                                  "link": "http://biorxiv.org" + i.a["href"]})
    return links

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def get_metrics(url):
    """
    get number of abstract view and PDF downloads
    Not all papers have this, only after a certain length of time
    Also get when it was first posted and the date most recent version was posted
    """
    months = {
        "January": '01',
        "February": "02",
        "March": "03",
        "April": "04",
        "May": "05",
        "June": "06",
        "July": "07",
        "August": "08",
        "September": "09",
        "October": "10",
        "November": "11",
        "December": "12"}
    metrics = make_soup(url + ".article-metrics")
    info = make_soup(url + ".article-info")
    views = metrics.findAll("td")
    versions = info.findAll("ul", "issue-toc-list")
    current_version = "_".join(url.split("/")[5:8])
    # get metrics
    if len(views) >= 3:  # should be at least 3 fields, otherwise too new for metrics
        abstract = 0
        pdf = 0
        # not all papers have a pdf version, some just have abstract views
        # can check by looking at 3rd position
        if is_number(views[2].text):
            for i in range(len(views)):
                if i % 3 == 1:
                    abstract += int(views[i].text)
                elif i % 3 == 2:
                    pdf += int(views[i].text)
        else:
            pdf = "NA"
            for i in range(len(views)):
                if i % 2 == 1:
                    abstract += int(views[i].text)
        abstract = str(abstract)
        pdf = str(pdf)
    else:
        abstract = "NA"
        pdf = "NA"
    # get versions
    if len(versions) > 0:
        for v in versions:
            for i in v.findAll("li"):
                if i.span:
                    if "(" in i.span.string:
                        month, day, year = i.span.string.replace("(", ")").split(")")[1].split(" ")[:3]
                        month = months[month]
                        day = day.strip(",")
                        oldest = "_".join([year, month, day])
                        break
                else:
                    try:
                        i.a.string
                    except:
                        oldest = current_version
                    else:
                        s = str(i.a.string)
                        month, day, year = s.replace("(", ")").split(")")[1].split(" ")[:3]
                        month = months[month]
                        day = day.strip(",")
                        oldest = "_".join([year, month, day])

    else:
        oldest = current_version
    return [abstract, pdf, current_version, oldest]


url = "http://biorxiv.org/content/early/recent"
now = datetime.now()
date = str(now.year) + "_" + str(now.month) + "_" + str(now.day)

if options.pages is None:
    pages = find_pages(url)
    all_papers = []

    for page in pages:
        try:
            get_paper_links(page)
        except:
            sleep(5)
        else:
            pass
        all_papers += get_paper_links(page)
        sleep(1)

    # save list of papers and links
    with open("links_" + date + ".tsv", "w+") as outfile:
        for i in all_papers:
            s = i['link'] + '\t' + i['title'] + '\n'
            outfile.write(s.encode("UTF-8"))
else:
    # read links from file
    with open(options.pages, 'r') as infile:
        all_papers = []
        for line in infile:
            line = line.strip('\n').split('\t')
            all_papers.append({'link': line[0], 'title': line[1]})


if options.data is None:
    with open("biorxiv_data_" + date + ".tsv", "w+") as outfile:
        outfile.write("Title\tURL\tAbstract views\tPDF views\tOriginal submission\tCurrent submission\n")

        for i in all_papers:
            try:
                get_metrics(i["link"])
            except:
                sleep(5)
            else:
                pass
            abstract, pdf, current, oldest = get_metrics(i["link"])
            s = i['title'] + "\t" + \
                i['link'] + "\t" + \
                abstract + "\t" + \
                pdf + "\t" + \
                oldest + "\t" + \
                current + "\n"
            outfile.write(s.encode("UTF-8"))
            sleep(1)
else:
    # get the last line so we know where to start from
    with open(options.data, 'r') as infile:
        for l in infile:
            l = l.split('\t')
    last_entry = {'link': l[1], 'title': l[0]}

    # remove all links prior to last paper from all_papers
    last_paper = all_papers.index(last_entry)
    all_papers = all_papers[last_paper:]

    with open(options.data, 'a') as outfile:
        for i in all_papers:
            try:
                get_metrics(i["link"])
            except:
                sleep(5)
            else:
                pass
            abstract, pdf, current, oldest = get_metrics(i["link"])
            s = i['title'] + "\t" + \
                i['link'] + "\t" + \
                abstract + "\t" + \
                pdf + "\t" + \
                oldest + "\t" + \
                current + "\n"
            outfile.write(s)
            sleep(1)
