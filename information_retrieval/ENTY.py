from find_keyname import get_req_keyname
from find_near_page import get_near_page
import wikipedia
from practnlptools.tools import Annotator
from SPARQLWrapper import SPARQLWrapper, JSON
from sparqlquery import *
from nltk.corpus import wordnet as wn
from nltk.stem.snowball import SnowballStemmer
import en

dbo = Namespace("http://dbpedia.org/ontology/")
sparql = SPARQLWrapper("http://dbpedia.org/sparql")
annotator = Annotator()
wikipedia.set_lang('en')
stemmer = SnowballStemmer("english")

def correct_form_verb(word):
    req_words = []

    syns = wn.synsets(word)[:3]

    for s in syns:
        for name in s.lemma_names():
            if name not in req_words:
                if len(name)>2:
                    req_words.append(name)

    return req_words


def get_query(fine_class,target,special_words):
    answer = []
    #finding the resource page
    verb_syn = []
    to_search = ""
    for t in target:
        to_search = to_search+" "+t
    for s in special_words:
        to_search = to_search+" "+s
    #print "TO SEARCH : ",to_search
    search_result = wikipedia.search(to_search)
    page = search_result[0]
    wiki_page = wikipedia.page(page)
    wiki_url = wiki_page.url
    resource_page = ""
    resource_page = wiki_url.split('/')[-1]
    print "\nRESOURCE : ",resource_page
    dbpedia_base ="http://dbpedia.org/resource/"
    uri =  Namespace(dbpedia_base+resource_page)
    first_uri = uri

    #find the key-name from the resource page w.r.t. query
    target_findkey = []
    temp_target = []
    for t in target:
        words = t.split()
        for w in words:
            temp_target.append(w)
    target_findkey = temp_target

    for t in target_findkey:
        pos_t = annotator.getAnnotations(t)['pos']
        if pos_t[0][1] in ['VB','VBD','VBG','VBN','VBP','VBZ']:
            req_word = en.verb.infinitive(pos_t[0][0])
            if req_word == "":
                req_word = pos_t[0][0]
            target_findkey.remove(t)
            target_findkey.append(req_word)
    #print "\nfind : ",target_findkey

    data_req = get_req_keyname(uri,target_findkey,fine_class)
    data_req = Namespace(data_req)

    if data_req =="":
        query = Select([v.x]).where((first_uri,dbo.abstract,v.x))
        query = query.compile()
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            if "xml:lang" in result["x"]:
                if result["x"]["xml:lang"] == "en":
                    answer.append(result["x"]["value"])
            else:
                answer.append(result["x"]["value"])

    else:
        #forming the query
        query = Select([v.x]).where((uri,data_req,v.x))
        query = query.compile()
        #print "\nQUERY : \n",query

        # retrieving data from the dbpedia page
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        if not results["results"]["bindings"]:
            query = Select([v.x]).where((uri,dbo.abstract,v.x))
            query = query.compile()
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()

        for result in results["results"]["bindings"]:
            if "xml:lang" in result["x"]:
                if result["x"]["xml:lang"] == "en":
                    answer.append(result["x"]["value"])
            else:
                answer.append(result["x"]["value"])

        #if the answer is a resource
        check_answer = answer[0].split('/')
        if "http" in check_answer[0]:
            temp_answer = answer
            answer = []
            for a in temp_answer:
                split_answer = a.split('/')
                if "http" in split_answer[0]:
                    new_uri = Namespace(a)
                    query = Select([v.x]).where((new_uri,dbo.abstract,v.x))
                    query = query.compile()
                    sparql.setQuery(query)
                    sparql.setReturnFormat(JSON)
                    results = sparql.query().convert()

                    if not results["results"]["bindings"]:
                        query = Select([v.x]).where((uri,dbo.abstract,v.x))
                        query = query.compile()
                        sparql.setQuery(query)
                        sparql.setReturnFormat(JSON)
                        results = sparql.query().convert()

                    for result in results["results"]["bindings"]:
                        if "xml:lang" in result["x"]:
                            if result["x"]["xml:lang"] == "en":
                                answer.append(result["x"]["value"])
                        else:
                            answer.append(result["x"]["value"])


    #print "->| ",answer
    ret_answer = ""
    line_flag = False
    for a in answer:
        if line_flag:
            ret_answer = ret_answer + "\n"+ a
        else:
            line_flag = True
            ret_answer = ret_answer + a
        #print "test : ",ret_answer
    return ret_answer