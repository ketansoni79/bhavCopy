import redis, urllib.request, zipfile, csv, urllib

def download(day, month, year):

    day, month, year = [int(day), int(month), int(year)]

    url = 'http://www.bseindia.com/download/BhavCopy/Equity/EQ%d%d%d_CSV.ZIP' % (day, month, year)
    r_db = redis.StrictRedis('localhost', 6379, charset="utf-8", decode_responses=True)
    r_db.flushall()

    try:
        tmp_file = urllib.request.urlretrieve(url)
    except urllib.error.HTTPError:
        return
    archive = zipfile.ZipFile(tmp_file[0])
    file = archive.extract(archive.namelist()[0])

    with open(file, encoding='utf-8') as data:
        csvfile = csv.reader(data)
        next(csvfile)
        for row in csvfile:
            c_name = row[1].strip()
            c_data = {'name': c_name, 'code': int(row[0]), 'open': float(row[4]), 'high': float(row[5]),
                      'low': float(row[6]), 'close': float(row[7])}
            r_db.rpush('list', c_data)