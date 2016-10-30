import tarfile
from contextlib import closing
import xml.etree.cElementTree as ET
import glob
import os
import gzip
import unicodedata
import time
import json
from elasticsearch import Elasticsearch
import datetime
import pprint
import numpy as np
import operator

INDEX = 'telegraaf'


def index_data(folder, es, force = False):
    """
    Read in XML and save data to Elasticsearch

    Keyword arguments:
    folder -- folder where gzipped xmls are stored
    es -- elasticsearch instance

    return void
    """

    # Only reindex files if force is set
    if es.indices.exists(index=INDEX):
        if force:
            # Delete and recreate ES index
            es.indices.delete(index=INDEX)
            es.indices.create(index=INDEX)
        else:
            return True, []
    

    files_indexed = []
    namespaces = {'pm': 'http://www.politicalmashup.nl', 'dc': 'http://purl.org/dc/elements/1.1/'}
    # Loop over all files in folder
    for filename in glob.glob( os.path.join(folder, '*.gz') ):
        files_indexed.append(filename)
        # Open them and parse XML
        with gzip.open(filename) as xml:
            print filename
            tree = ET.parse(xml)

            # Get all articles and extract data from it
            root = tree.getroot()
            for article in root.findall('pm:root', namespaces):
                date = (article.find('pm:meta/dc:date', namespaces)).text
                subject = (article.find('pm:meta/dc:subject', namespaces)).text
                title = (article.find('pm:content/title', namespaces)).text
                if title == None:
                    title = ''

                text = ''
                if article.find('pm:content/text/p', namespaces) != None:
                    text = (article.find('pm:content/text/p', namespaces)).text

                # Construct JSON data structure and store in ES
                data = {}
                data['date'] = date
                data['subject'] = subject
                data['title'] = unicodedata.normalize('NFKD', unicode(title)).encode('ascii','ignore')
                data['text'] = unicodedata.normalize('NFKD', unicode(text)).encode('ascii','ignore')
                json_data = json.dumps(data)
                res = es.index(index=INDEX, doc_type='article', body=json_data)

    return True, files_indexed

def term_and_doc_freq(filestext):
    tf = {}
    dftext = {}
    dfcount = {}

    i = 1
    for text in filestext:
        words = text.split(' ')
        text = 'd'+str(i) # d1, d2, d3
        for word in words:
            word = word.encode('UTF-8')
            if(word == '.' or word == '' or word == '-' or word == "'"): # remove some punctuation
                continue
            if(word not in tf):
                tf[word] = 1
            elif(word in tf):
                tf[word] += 1

            if(word not in dftext):
                dftext[word] = [text]
            elif(dftext[word][0] != text):
                dftext[word].append(text)
        i += 1

    for key, values in dftext.items():
        dfcount[key] = len(values)

    return tf, dfcount
    # for date in filesdate:
    #     year = date[:4] # get first 4 for year
    #     if(year not in years):
    #         years.append(year.encode('UTF-8'))
    #
    # for filename in glob.glob( os.path.join('data', '*.gz') ):
    #     # print filename[15:19], years, type(filename[15:19])
    #     if(filename[15:19] in years): #15:19 is the year part in da filename
    #         with gzip.open(filename) as xml:
    #             tree = ET.parse(xml)
    #             # Get all articles and extract data from it
    #             root = tree.getroot()
    #             for article in root.findall('pm:root', namespaces):
    #                 date = (article.find('pm:meta/dc:date', namespaces)).text
    #                 if(date in filesdate):
    #                     # print filesdate, date
    #                     text = (article.find('pm:content/text/p', namespaces)).text
    #                     text = unicodedata.normalize('NFKD', unicode(text)).encode('ascii','ignore')
    #                     # print(text)
    #                     if(text in filestext):
    #
                        # else:
                            # print('!!!!!!!!!!!!!!!')

            # for date in files:
            #     if(filename in files):
            #         print('##########' ,True)
            #     else:
            #         print('!!!!!!!!!!!')

def years_freq(filesdate):
    years = {}
    for date in filesdate:
        year = date[:4] # get first 4 for year
        year = year.encode('UTF-8')
        if(year in years):
            years[year] += 1
        elif(year not in years):
            years[year] = 1

    return years

def tfidf(tf, df, num_docs): #{{word1 : tf}, {word2 : tf}, ..}, {{word1 : df}, {word2 : df}, ..}
    tfidf_weight = {}
    if(num_docs != 0):
        for key, value in tf.items():
            if(df[key] != 0 and value != 0):
                tfidf_weight[key] = (1 + np.log10(value))*np.log10(num_docs/df[key])

    tfidf_sorted = sorted(tfidf_weight.items(), key=operator.itemgetter(1))

    return tfidf_sorted[-10:]

def search(es, text, fields=[], filter_query={}):
    """
    Search

    text -- Search query
    fields -- fields to search in
    filter_query -- filter

    return [documents]
    """
    body = {
      'query': {
        'query_string': {
            'query': text
        }
      },
      'filter': filter_query
    }

    #if len(fields) > 0 :
    #    body['query']['query_string']['fields'] = fields

    return es.search(index=INDEX, body=body)


def search_title(es, title):
    """
    Search on title

    title -- (Part of) the title

    return [documents]
    """
    return search(es, title, ['nee ik krijg dit resultaattitle'])

def search_body(es, body):
    """
    Search on body

    body -- (Part of) the body

    return [documents]
    """
    return search(es, body, ['text'])

def search_date(es, date):
    """
    Search on date

    date -- (Part of) the date (YYYY-MM-DD)

    return [documents]
    """
    return search(es, date, ['date'])

def search_free(es, text):
    """
    Search on text (no field restriction)

    text -- (Part of) the text

    return [documents]
    """
    return search(es, text)

def search_in_range(es, text, start, end):
    """
    Search on text in date rannee ik krijg dit resultaatge

    text -- (Part of) the text
    start -- start date (YYYY-MM-DD)
    end -- end date (YYYY-MM-DD)

    return [documents]
    """
    start_split = start.split('-')
    start = datetime.date(start_split[0], start_split[1], start_split[2])

    end_split = end.split('-')
    end = datetime.date(end_split[0], end_split[1], end_split[2])
    filter_query = {
      'range': {
        'date': {'gte': start, 'lte': end}
      }
    }
    filter_query = json.dumps(filter_query)

    return search(es, text, [], filter_query)

def word_cloud(es, size = 10):
    body = {
    	"size": 0,
        "aggregations": {
            "tagcloud": {
                "terms": {
                    "field": "text",
                    "size": "20",
                    "exclude": ["de", "i", "van", "het", "en", "v", "t", "1"]
                }
            }
        },
        "query" : {
          "match_all" : {}
        }
    }

    res = es.search(index=INDEX, body=body)
    pprint.pprint(res['aggregations']['tagcloud'])
    result = []
    # for i in range(res['aggregations']['tagcloud']):
    #     result.append([])
    # i = 0
    # for item in res['hits']['hits']:
    #     result[i].append(item[unicode('_source')][unicode('title')])
    #     result[i].append(item[unicode('_source')][unicode('date')])
    #     result[i].append(item[unicode('_source')][unicode('text')])
    #     i += 1

    return result

if __name__ == '__main__':
    es = Elasticsearch()
    done, files = index_data('data', es)
    # res = search(es, 'dier')
    word_cloud = word_cloud(es)
    print(word_cloud, 1)
    # print search_free(es, 'duits')
