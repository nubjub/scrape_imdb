import argparse
import re
import os.path
import time
import codecs
import requests
import bs4
import pyparsing as pyparse
import sys
from unicodewriter import UnicodeWriter

def pretty_seconds(time):
    sep = lambda n: (int(n / 60), int(n % 60))
    mins, secs = sep(time)
    hrs, mins = sep(mins)
    return '{0}h {1}m {2}s'.format(hrs, mins, secs)

def query_request(url):
    resp = requests.get(url)
    if resp.status_code != 200:
        print 'fetch failed'
        exit()
    return resp
def csv_out(imdb, file): 
    print '\nWriting to', file
    username = os.path.splitext(os.path.basename(file))[0]
    with codecs.open(file, 'wb') as outfile:
        w = UnicodeWriter(outfile)
        row0 = []
        for n in imdb:
            row0.extend(n.keys())
        row0 = set(row0)
        w.writerow(row0)
        for n in imdb:
            row1 = []
            for m in row0:
                v = n.get(m)
                if(v == None):
                    v = ""
                row1.append(v)
            w.writerow(row1)
    
def parse_list(html):
    ttlist = []
    tds = html.find_all('td', class_='title')
    for td in tds:
        imdb_url = td.a['href']
        imdb_id = re.search('(tt[0-9]{7})', imdb_url).group(1)
        ttlist.append(imdb_id)
    return ttlist
    
def parse_movie(tt):
    try:
        url = "http://www.imdb.com/title/" + tt + '/business?ref_=tt_dt_bus'
        resp = query_request(url)
        soup = bs4.BeautifulSoup(resp.text)
        html = soup.find('div', id='tn15content')
        whitelist = ["h5", "br"]
        for tag in soup.findAll(True):
            if tag.name not in whitelist:
                tag.extract()
                    
        html = unicode(html)
        html = re.sub("<h5>Filming.*", "</div>\n<div id=junk>", html)
        html = bs4.BeautifulSoup(html).find('div', id='tn15content')                    
        html = unicode(html)
        html = html.replace(",","")
        html = html.replace("</h5>\n","<br/>")
        html = re.sub("\n<br/>\n", "</h5>\n", html)
        html = html.replace("<br/>","<br/>\n")
        html = re.sub(r'\n\$(\d+) \(USA\)', r'\n<dol>\1</dol>', html)
        html = re.sub(r'\n\$(\d+) \(estimated\)', r'\n<dol>\1</dol>', html)
        html = bs4.BeautifulSoup(html).findAll('h5')
    
        integer = pyparse.Word(pyparse.nums).setParseAction(lambda t :  int(t[0]) ).ignore(pyparse.CharsNotIn(pyparse.nums))   
        #integer = pyparse.Word(pyparse.nums).ignore(pyparse.CharsNotIn(pyparse.nums))
        has_money = False
        movie_money = {}
        for n in html:
            n_id = (unicode(n.next).lower())
            if(n_id == 'gross'):
                has_money = True
            m = n.findAll('dol')
            val = 0;
            for l in m:
                val = max(val,(integer.parseString(l.get_text()))[0])
            movie_money[n_id] = unicode(val)
    
        if(has_money == False):
            raise
        
        movie = {}
        movie['id'] = tt
        url = "http://www.imdb.com/title/" + tt
        resp = query_request(url)
        soup = bs4.BeautifulSoup(resp.text)
        soup = soup.find('h1', class_="header")
        html = soup.find('span', class_="itemprop", itemprop="name")
        movie['title'] = html.get_text()
        html = soup.find('span', class_="nobr").get_text()
        #integer = pyparse.Word(pyparse.nums).setParseAction(lambda t :  int(t[0]) ).ignore(pyparse.CharsNotIn(pyparse.nums))
        integer = pyparse.Word(pyparse.nums).ignore(pyparse.CharsNotIn(pyparse.nums))
        html = integer.parseString(html)
        movie['year'] = html[0]
        soup = bs4.BeautifulSoup(resp.text)
        html = soup.find('meta', itemprop="datePublished")
        movie['date'] = html.attrs['content']
        html = soup.find('div', class_="txt-block", itemprop="director")
        html = html.findAll('span', itemprop="name")
        for i in range(len(html)):
            movie[str('director_' + str(i+1))] = html[i].get_text()
        html = soup.find('div', class_="txt-block", itemprop="creator")
        html = html.findAll('span', itemprop="name")
        for i in range(len(html)):
            movie[str('writer_' + str(i+1))] = html[i].get_text()
        html = soup.find('div', class_="txt-block", itemprop="actors")
        html = html.findAll('span', itemprop="name")
        for i in range(len(html)):
            movie[str('actor_' + str(i+1))] = html[i].get_text()
    
        soup = soup.find('div', class_="star-box-details")
        html = soup.find('span', itemprop="ratingValue")
        #integer = pyparse.Word(pyparse.nums+'.').setParseAction(lambda t : float(t[0]) ).ignore(pyparse.CharsNotIn(pyparse.nums+'.'))
        integer = pyparse.Word(pyparse.nums+'.').ignore(pyparse.CharsNotIn(pyparse.nums+'.'))
        html = integer.parseString(html.get_text()) 
        movie['imdb_rating'] = html[0]
        html = soup.find('span', itemprop="ratingCount")
        #integer = pyparse.Word(pyparse.nums).setParseAction(lambda t :  int(t[0]) ).ignore(pyparse.CharsNotIn(pyparse.nums))
        integer = pyparse.Word(pyparse.nums).ignore(pyparse.CharsNotIn(pyparse.nums))
        html = html.get_text().replace(",","")
        html = integer.parseString(html) 
        movie['imdb_votes'] = html[0]
        html = soup.find('a', title=re.compile('Metacritic'))
        integer = pyparse.OneOrMore((pyparse.Word(pyparse.nums).setParseAction(lambda t:  int(t[0]) )).ignore(pyparse.CharsNotIn(pyparse.nums)))
        html = integer.parseString(html.get_text()) 
        html = unicode(float(html[0]) / float(html[1]))
        movie['metacritic'] = html
        movie.update(movie_money)
    except Exception:
        return None
    return movie
    

if __name__ == '__main__':
    opts = argparse.ArgumentParser(description='Download large IMDb rating lists.')
    opts.add_argument('ratings_url', help='URL to IMDb user ratings page')
    opts.add_argument('outfile', help='Path to output CSV file')
    args = opts.parse_args()

    start_time = time.time()
    url = args.ratings_url
    print 'fetching: ' + url
    resp = query_request(url)
    soup = bs4.BeautifulSoup(resp.text)
    q_title = soup.title.string
    print 'query: ' + q_title
    q_size_text = soup.find(id='left').text
    q_size_text = q_size_text.replace(",","")
    integer = pyparse.OneOrMore((pyparse.Word(pyparse.nums).setParseAction(lambda t:  int(t[0]) )).ignore(pyparse.CharsNotIn(pyparse.nums)))
    q_size = integer.parseString(q_size_text)
    
    if len(q_size) != 3:
        if len(q_size) != 1:
            print 'Could not determine number of pages'
            exit()
        q_size = [1, q_size[0], q_size[0]]
    #[0] = start_position
    #[1] = results_per_page
    #[2] = total_results
    #[3] = current_page
    #[4] = total_pages
    
    ttlist = [] 
    imdb = []
    while (not (q_size[0] > q_size[2])):
        print 'Processing', q_size[0], 'through', min((q_size[0] + q_size[1] -1),q_size[2]), 'of', q_size[2]
        ttlist.extend(parse_list(soup))
        q_size[0] = q_size[0]+ q_size[1]
        url = args.ratings_url + '&start=' + str(q_size[0])
        resp = query_request(url)
        soup = bs4.BeautifulSoup(resp.text) 
    list_time = time.time()
    print 'List of', len(ttlist), 'movies generated in', pretty_seconds(list_time - start_time)

    sys.stdout.write('Parsing ')
    i =0
    for tt in ttlist:
        if(i > 9):
            i = 0
            sys.stdout.write('\nParsing ')
        i = i+1
        sys.stdout.write( tt + ' ')
        movie = parse_movie(tt)
        if(movie != None):
            imdb.append(movie)
            
    csv_out(imdb,args.outfile)
    end_time = time.time() 
    print 'Parsed', len(ttlist), 'movies in', pretty_seconds(list_time - start_time)

