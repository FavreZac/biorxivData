#! /usr/bin/env python
# coding: utf-8


from bs4 import BeautifulSoup
import requests
from time import sleep
from datetime import datetime


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
                                  "link": i.a["href"]})
    return links

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
        "December": "12"
    }
    metrics = make_soup(url + ".article-metrics")
    info = make_soup(url + ".article-info")
    views = metrics.findAll("td")
    versions = info.findAll("ul", "issue-toc-list")
    current_version = "_".join(url.split("/")[5:8])
    # get metrics
    if len(views) >= 3:  # should be at least 3 fields, otherwise too new for metrics
        abstract = views[1].text
        pdf = views[2].text
    else:
        abstract = "NA"
        pdf = "NA"
    # get versions
    if len(versions) > 0:
        for v in versions:
            for i in v.findAll("li"):
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

for i in all_papers:
    try:
        get_metrics(i["link"])
    except:
        sleep(5)
    else:
        pass
    abstract, pdf, current, oldest = get_metrics(i["link"])
    i["abstract"] = abstract
    i["pdf"] = pdf
    i["current"] = current
    i["oldest"] = oldest
    sleep(1)

now = datetime.now()
date = str(now.year) + "_" + str(now.month) + "_" + str(now.day)

with open("biorxiv_data_" + date + ".tsv", "w+") as outfile:
    outfile.write("Title\tURL\tAbstract views\tPDF views\tOriginal submission\tCurrent submission\n")
    for i in all_papers:
        s = i['title'] + "\t" + \
            i['link'] + "\t" + \
            i['abstract'] + "\t" + \
            i["pdf"] + "\t" + \
            i["oldest"] + "\t" + \
            i["current"] + "\n"
        outfile.write(s.encode("UTF-8"))