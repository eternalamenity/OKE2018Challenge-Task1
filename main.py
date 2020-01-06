# sparql = SPARQLWrapper("http://dbpedia.org/sparql")
# sparql.setQuery("""
#         SELECT ?label
#         WHERE { <http://dbpedia.org/resource/Person> dct:subject ?label }
# """)


# sparql = SPARQLWrapper("http://dbpedia.org/sparql")
# sparql.setQuery("""
#         SELECT ?label
#         WHERE { <http://dbpedia.org/resource/Place> rdf:type ?label }
# """)
# sparql.setReturnFormat(JSON)
# results = sparql.query().convert()

# for result in results["results"]["bindings"]:
#     print(result)


# import rdflib
# g=rdflib.Graph()
# g.load('http://dbpedia.org/resource/Programmer')

# for s,p,o in g:
#     print(s, p, o)

# collection = NIFCollection(uri="http://freme-project.eu")
# context = collection.add_context(
#     uri="http://freme-project.eu/doc32",
#     mention="Diego Maradona is from Argentina.")


# context.add_phrase(
#     beginIndex=0,
#     endIndex=14,
#     taClassRef=['http://dbpedia.org/ontology/SportsManager', 'http://dbpedia.org/ontology/Person', 'http://nerd.eurecom.fr/ontology#Person'],
#     score=0.9869992701528016,
#     annotator='http://freme-project.eu/tools/freme-ner',
#     taIdentRef='http://dbpedia.org/resource/Diego_Maradona',
#     taMsClassRef='http://dbpedia.org/ontology/SoccerManager')

# generated_nif = collection.dumps(format='turtle')
# print(generated_nif)

from SPARQLWrapper import SPARQLWrapper, JSON
from pynif import NIFCollection
import re
import nltk
from nltk.corpus import stopwords 
nltk.download('stopwords')

def remove_stopwords(tokens):
    stop_words = set(stopwords.words('english'))
    return list(filter(lambda x: x not in stop_words, tokens))

def tokenize():
    wordsList=[]
    with open('input','r') as f:
        for line in f:
            for word in line.split():
                cleanString = re.sub('\W+','', word)
                wordsList.append(cleanString)
    # Remove stopwords
    stopWordsList = remove_stopwords(wordsList)
    return stopWordsList

def sendDBPediaQuery():
    wordsList = tokenize()
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")

    for word in wordsList:
        sparql.setQuery("""
                SELECT ?label
                WHERE { <http://dbpedia.org/resource/"""+word+"""> rdf:type ?label }
        """)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        print("Example for word: ", word)
        for result in results["results"]["bindings"]:
            print(result)
                    

sendDBPediaQuery()
