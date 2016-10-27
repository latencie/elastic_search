from flask import Flask, render_template, request
from es_index import *
from elasticsearch import Elasticsearch

app = Flask(__name__, static_url_path='')

es = Elasticsearch()
done, files = index_data('/data', es)
if done:
    print files

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'search' in request.form:
        query = request.form['query']
        if query == '':
            results = ['Please ask us something!']
            return render_template('resultpage.html', results=results)
        else:
            res = search(es, query)
            result = []
            results_length = len(res['hits']['hits'])

            for i in range(len(res['hits']['hits'])):
                result.append([])

            i = 0
            for item in res['hits']['hits']:
                result[i].append(item[unicode('_source')][unicode('title')])
                result[i].append(item[unicode('_source')][unicode('date')])
                result[i].append(item[unicode('_source')][unicode('text')])
                i += 1

            return render_template('resultpage.html', results=result, query=query, length=results_length)

    if 'advanced' in request.form:
        return render_template('advanced_search.html')

    return render_template('index.html')

if __name__ == "__main__":
    app.run()
