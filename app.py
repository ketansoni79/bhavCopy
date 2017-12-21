import urllib.request, urllib
import zipfile, csv, redis, cherrypy, os, ast
from jinja2 import Environment, FileSystemLoader


CUR_DIR = os.path.dirname(os.path.abspath(__file__))
env=Environment(loader=FileSystemLoader(CUR_DIR), trim_blocks=True)


class Index(object):
    @cherrypy.expose()
    def index(self):
        template = env.get_template('index.html')
        # RENDER TEMPLATE PASSING IN DATA
        return template.render()


    @cherrypy.expose()
    def download(self, day,month,year):
        template = env.get_template('table.html')

        day,month,year = [int(day), int(month), int(year)]

        url = 'http://www.bseindia.com/download/BhavCopy/Equity/EQ%d%d%d_CSV.ZIP' % (day, month, year)
        r_db = redis.StrictRedis('localhost', 6379, charset="utf-8", decode_responses=True)
        r_db.flushall()

        try:
            tmp_file = urllib.request.urlretrieve(url)
        except urllib.error.HTTPError:
            return template.render(data='')
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


        top_10 = r_db.lrange('list',0,9)
        top = [ast.literal_eval(x) for x in top_10]
        return template.render(data=top)

    @cherrypy.expose()
    def search(self, name):
        template = env.get_template('table.html')
        r_db = redis.StrictRedis('localhost', 6379, charset="utf-8", decode_responses=True)

        data=[]
        c_name = name.upper()
        for i in range(r_db.llen('list')):
            dic = r_db.lindex('list',i)
            c_data = ast.literal_eval(dic)
            if c_name in c_data['name']:
                data.append(c_data)

        return template.render(data=data)


if __name__ == '__main__':
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './public'
        }
    }
    # RUN
    cherrypy.quickstart(Index(), '/', conf)
