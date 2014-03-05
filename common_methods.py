import requests
import csv
import codecs
import os.path
import cStringIO

def query_request(url):
    for i in range(0,5):
        try:
            resp = requests.get(url)  
            if resp.status_code == 200:
                return resp
        except Exception:
            pass
    raise

def pretty_time(time):
    sep = lambda n: (int(n / 60), int(n % 60))
    mins, secs = sep(time)
    hrs, mins = sep(mins)
    return '{0}h {1}m {2}s'.format(hrs, mins, secs)

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

# docs.python.org/2/library/csv.html#examples
class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        data = self.encoder.encode(data)
        self.stream.write(data)
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)