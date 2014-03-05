import argparse
import re
import os.path
import time
import codecs
import bs4
import pyparsing as pyparse
import sys
import gevent
from gevent.pool import Pool
import common_methods as cm

def parse_mpaa_rating(soup):
    html = soup.find('span', itemprop='contentRating')
    html = html.attrs['content']
    return html

def parse_name(nm):
    nm_main = cm.query_request("http://www.imdb.com/name/" + nm)
    soup = bs4.BeautifulSoup(nm_main.text)
    name = {}
    name['id'] = nm
    return name

def parse_title(tt):
    title = None
    try:
        title = {}
        title['id'] = unicode(tt)
        tt_main = cm.query_request("http://www.imdb.com/title/" + tt)
        #tt_money = cm.query_request("http://www.imdb.com/title/" + q + "/business")
        soup = bs4.BeautifulSoup(tt_main.text)
        try:
            title['mpaa'] = parse_mpaa_rating(soup)
        except:
            pass
    except:
        pass
    return title

def parse_list(parser,query_list):
    r_list = []
    sys.stdout.write('Parsing ')
    pool = Pool(10)    
    for q in pool.map(parser,query_list):
        if q != None:
            r_list.append(q)
    pool.join()
    return r_list

if __name__ == '__main__':
    opts = argparse.ArgumentParser(description='List to list')
    opts.add_argument('outfile', help='Path to output CSV file')
    opts.add_argument('query_list', help='URL to IMDb user ratings page')
    args = opts.parse_args()

    start_time = time.time()
    
    with open(args.query_list) as file_query_list:
        query_list = [line.rstrip() for line in file_query_list]
    
    l = len(query_list)
    if(not (l > 0)):
        print 'List empty'
        exit(1)    
    print 'Fetch size: ', l
    imdb = []
    qtype = ''
    if(query_list[0].startswith('tt')):
        imdb = parse_list(parse_title,query_list)
        qtype = 'movies'
    elif(query_list[0].startswith('nm')):
        imdb = parse_list(parse_name,query_list)
        qtype = 'names'
    print 'Parsed', len(imdb), qtype +' in', cm.pretty_time(time.time() - start_time)
    cm.csv_out(imdb,args.outfile)
        
    

