import urllib.request, urllib
import zipfile, csv, redis, cherrypy, os, ast, json
from jinja2 import Environment, FileSystemLoader


CUR_DIR = os.path.dirname(os.path.abspath(__file__))
env=Environment(loader=FileSystemLoader(CUR_DIR), trim_blocks=True)


class Index(object):
    # Connect to redis database
    r_db = redis.StrictRedis('localhost', 6379, charset="utf-8", decode_responses=True)
    
    @cherrypy.expose()
    def index(self):
        template = env.get_template('index.html')
        # RENDER TEMPLATE PASSING IN DATA
        return template.render()


    @cherrypy.expose()
    def download(self, day,month,year):
        template = env.get_template('table.html')

        date = '%s%s%s' % (day, month, year)

        #condition to check if bhavData already exist in database for given date
        if not self.r_db.hexists('bhavData', date):
            url = 'http://www.bseindia.com/download/BhavCopy/Equity/EQ%s_CSV.ZIP' % (date)

            try:
                tmp_file = urllib.request.urlretrieve(url)
            except urllib.error.HTTPError:
                return template.render(data='')
            archive = zipfile.ZipFile(tmp_file[0])
            file = archive.extract(archive.namelist()[0])

            with open(file, encoding='utf-8') as data:
                csvfile = csv.reader(data)
                next(csvfile)
                li = []
                for row in csvfile:
                    c_name = row[1].strip()
                    c_data = {'name': c_name, 'code': int(row[0]), 'open': float(row[4]), 'high': float(row[5]),
                              'low': float(row[6]), 'close': float(row[7])}
                    li.append(c_data)
                data = json.dumps(li)
                self.r_db.hset('bhavData', date, data)

        #get the top 10 companies and render
        data = self.r_db.hget('bhavData', date)
        bhav_data = ast.literal_eval(data)
        return template.render(data=bhav_data[:10], date=date)


    @cherrypy.expose()
    def search(self, name, date):
        template = env.get_template('table.html')
        comp = []
        data = self.r_db.hget('bhavData', date)
        bhav_data = ast.literal_eval(data)
        for company in bhav_data:
            if name.upper() in company['name']:
                comp.append(company)

        return template.render(data=comp)


if __name__ == '__main__':
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        }
    }
    # RUN
    cherrypy.quickstart(Index(), '/', conf)
