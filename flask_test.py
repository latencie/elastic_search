from flask import Flask, render_template, request
from es_index import *
from elasticsearch import Elasticsearch

app = Flask(__name__, static_url_path='')

es = Elasticsearch()
done, files = index_data('data', es)
# if done:
#     print('indexing done')
#     print files

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
            filesdate, filestext = [], [] # To store the found files and compute tf-idfs
            result_length = len(res['hits']['hits'])

            for i in range(len(res['hits']['hits'])):
                if res['hits']['hits'] not in result:
                    result.append([])
            i = 0
            for item in res['hits']['hits']:
                result[i].append(item[unicode('_source')][unicode('title')])
                result[i].append(item[unicode('_source')][unicode('date')])
                result[i].append(item[unicode('_source')][unicode('text')])

                if(item[unicode('_source')][unicode('date')] not in filesdate):
                    filesdate.append(item[unicode('_source')][unicode('date')])
                if(item[unicode('_source')][unicode('text')] not in filestext):
                    filestext.append(item[unicode('_source')][unicode('text')])
                i += 1
            tf, df = term_and_doc_freq(filestext)
            num_docs = len(filestext)
            yearsfreq = years_freq(filesdate)
            top10 = tfidf(tf, df, num_docs)
            word_cloud = []
            for x in top10:
                word_cloud.append(x[0])
            word_cloud = word_cloud[::-1]
            chart()
            return render_template('resultpage.html', results=result, query=query, length=result_length, \
                                    word_cloud=word_cloud, years_freq=years_freq)

    if 'advanced' in request.form:
        return render_template('advanced_search.html')

    return render_template('index.html')

def chart():
    print('CHART')
    labels = ["January","February","March","April","May","June","July","August"]
    values = [10,9,8,7,6,4,7,8]
    return render_template('chart.html', values=values, labels=labels)

if __name__ == "__main__":
    app.run()
