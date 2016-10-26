from flask import Flask, render_template, request
from es_index import *
from elasticsearch import Elasticsearch

app = Flask(__name__, static_url_path='')

es = Elasticsearch()
index_data('/data', es)
print('indexed data')

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'search' in request.form:
        text = request.form['query']
        results = text.split(' ')
        if text == '':
            results = ['Please ask us something!']
            return render_template('resultpage.html', results=results)
        else:
            res = search(es, results[0])
            print res
            data = []
            data.append(res['hits']['total'])
            # print(data)
            # print('#######', res['hits']['total'])
            return render_template('resultpage.html', results=data)

    if 'advanced' in request.form:
        return render_template('advanced_search.html')

    return render_template('index.html')

if __name__ == "__main__":
    app.run()
