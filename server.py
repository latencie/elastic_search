from flask import Flask, render_template, request
from elasticsearch_client import *
from elasticsearch import Elasticsearch

app = Flask(__name__, static_url_path='')

es = Elasticsearch()
done, files = index_data('data', es)

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'search' in request.form or request.args.get('search') == 'Search':
        query = get_value(request, 'query')
        if query == '':
            results = ['Please ask us something!']
            return render_template('resultpage.html', results=results)
        else:
            facet = get_value(request, 'facet')
            res, result_length, count_per_month = search(es, query, [], facet)
            result = []
            facets = []
            filesdate, filestext = [], [] # To store the found files and compute tf-idfs

            for i in range(len(res)):
                if res not in result:
                    result.append([])
            i = 0

            for item in res:
                facet = item[unicode('_type')]
                if facet not in facets:
                    facets.append(facet)

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

            labels, values = extract_labels_values(count_per_month)

            return render_template('resultpage.html', results=result, query=query, length=result_length,
                                    word_cloud=word_cloud, years_freq=years_freq, values=values, labels=labels,
                                    facets=facets)

    if 'advanced' in request.form:
        return render_template('advanced_search.html')

    if 'advanced_search' in request.form:
        # query = get_value(request, 'advanced_query')
        title = get_value(request, 'title').encode('UTF-8')
        print title
        if title == '':
            results = ['Please ask us something!']
            return render_template('resultpage.html', results=results)
        else:
            # facet = get_value(request, 'facet')
            res, result_length, count_per_month = search_title(es, title)
            print result_length
            result = []
            facets = []
            filesdate, filestext = [], [] # To store the found files and compute tf-idfs

            for i in range(len(res)):
                if res not in result:
                    result.append([])
            i = 0

            for item in res:
                # facet = item[unicode('_type')]
                # if facet not in facets:
                #     facets.append(facet)

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

            labels, values = extract_labels_values(count_per_month)

            return render_template('resultpage.html', results=result, query=title, length=result_length,
                                    word_cloud=word_cloud, years_freq=years_freq, values=values, labels=labels,
                                    facets=facets)


    return render_template('index.html')

def extract_labels_values(count_per_month):
    labels = ["January","February","March","April","May","June","July","August","September","October","November", "December"]
    values = [0,0,0,0,0,0,0,0,0,0,0,0]

    for year in count_per_month:
        for month in count_per_month[year]:
            values[labels.index(month)] = count_per_month[year][month]

    return labels, values

def get_value(request, key):
    if request.method == 'POST' and key in request.form:
        return request.form[key]
    elif request.method == 'GET' and key in request.args:
        return request.args.get(key)

    return ''

if __name__ == "__main__":
    app.run()
