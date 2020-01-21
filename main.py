from SPARQLWrapper import SPARQLWrapper, JSON
from pynif import NIFCollection
from itertools import tee, islice, chain
import rdflib
import re
import nltk
import numpy as np
from nltk.corpus import stopwords 
nltk.download('stopwords')


class WordAndClass():
    "Stores words and theirs classes"
    def __init__(self, word, wordsClass, whereFound):
        self.word = word
        self.wordsClass = wordsClass
        self.whereFound = whereFound
    
    def printText(self):
        print("Word: " + self.word + " matches to " + self.wordsClass + " class")
        print("From Text: " + self.whereFound)


def openAndPurifyFile(file):
    with open(file) as openfile:
        for line in openfile:
            if "isString" in line:
                head, sep, tail = line.partition('@')
                searchedText = head.split()
                searchedText.pop(0)
                finalText = ' '.join(searchedText)
                finalText = re.sub('[^A-Za-z0-9]+', ' ', finalText)
                return finalText

def removeStopwords(tokens):
    stop_words = set(stopwords.words('english'))
    return list(filter(lambda x: x not in stop_words, tokens))

def tokenize(sentence):
    wordsList=[]
    for word in sentence.split():
        cleanString = re.sub('\W+','', word)
        wordsList.append(cleanString)
    return wordsList

def capitalizeList(wordsList):
    newList = []
    for word in wordsList:
        newList.append(word.title())
    return newList

def previous_and_next(some_iterable):
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return zip(prevs, items, nexts)

def getSentencesFromWords(tokens):         
    serie = ''
    series = []
    counter = 0
    for previous, token, nxt in previous_and_next(tokens):
        if  token[0].isupper():
            if  serie == '':
                serie = serie + token
                series += [serie]
            else:
                serie = serie + '_' + token
            counter = counter + 1
            if counter == 2:
                series += [serie]
                if (nxt[0].isupper() and (serie.count('_')) == 1):
                    serie = serie + '_' + nxt
                    series += [serie]
                counter = 0
                serie = ''  
        else:
            if serie != '':
                series += [serie]
            series += [token]
            serie = ''
            counter = 0
            
    series = list(set(series))
    return series

def sendDBPediaQuery(wordsList, wordClasses):
    output=[]
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    for word in wordsList:
        sparql.setQuery("""
                SELECT ?label
                WHERE { <http://dbpedia.org/resource/"""+word+"""> rdf:type ?label }
        """)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        for result in results["results"]["bindings"]:
            # print(word + ' ' + result['label']['value'])
            if 'http://dbpedia.org/ontology/' in result['label']['value']:
                # print('Word: ' + word + ', class: ' + result['label']['value'])
                finalText = re.sub('http://dbpedia.org/ontology/', '', result['label']['value'])
                if isWordInSearchedClasses(finalText, wordClasses):
                    print('Word: ' + word + ', class: ' + result['label']['value'])
                    output.append(word)
                else: 
                    foundWordClass = isOntologyOfSubclass(word)
                    if foundWordClass in wordClasses:
                        print('Word: ' + word + ', class: ' + 'http://dbpedia.org/ontology/' + foundWordClass)
                        output.append(word)
    return output

def isWordInSearchedClasses(word, wordClasses):
    if word in wordClasses:
        return True
    return False

def findIndexesOfFoundWordInOriginalText(word, file):
    with open(file) as openfile:
        for line in openfile:
            if "isString" in line:
                head, sep, tail = line.partition('@')
                searchedText = head.split()
                searchedText.pop(0)
                finalText = ' '.join(searchedText)
                finalText = re.sub('["]', '', finalText)
                formatted = getSentencesFromWords(finalText.split())
                
                final = ''
                for formattedWord in formatted:
                    final += formattedWord 
                    final += ' '
                startIndex = final.find(word)
                start, end = startIndex, startIndex + len(word)
                textLen = len(final) - 1
                return start, end, textLen

def fromStringToOutputFile(outputString, start, end, textLen):
    f = open("output","w+")
    f_input = open("input","r")
    contents = f_input.read()
    f.write(contents + '\n')
    f.write('<http://example.com/example-task1#char=' + str(start) + ',' + str(end) + '>\n')
    f.write('        a                     nif:RFC5147String , nif:String ;\n')
    f.write('        nif:anchorOf          "Florence May Harding"@en ;\n')
    f.write('        nif:beginIndex        "' + str(start) + '"^^xsd:nonNegativeInteger ;\n')
    f.write('        nif:endIndex          "' + str(end) + '"^^xsd:nonNegativeInteger ;\n')
    f.write('        nif:referenceContext  <http://example.com/example-task1#char=0,' + str(textLen) + '> ;\n')
    f.write('        itsrdf:taIdentRef     dbpedia:' + outputString + ' .\n')

    f.close()
    f_input.close()


def isOntologyOfSubclass(word):
    wordClasses = ['Person', 'Place', 'Organisation']
    finalText = "Initial Text"
    while finalText != None:
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setQuery("""
                    SELECT ?value
                    WHERE { <http://dbpedia.org/ontology/"""+word+"""> rdfs:subClassOf ?value }
            """)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        values = results['results']['bindings']
        if values:
            if 'http://dbpedia.org/ontology/' in str(values):
                uniqueList = unique(values)
                for x in uniqueList:
                    singleOntology = x['value']['value']
                    finalText = re.sub('http://dbpedia.org/ontology/', '', singleOntology)
                    # print(finalText)
                    word = finalText
                    if word in wordClasses:
                        return word
                    break
            else:
                finalText = None
        else:
            finalText = None
    return 'False'


def unique(list1): 
    # intilize a null list 
    unique_list = [] 
    for x in list1: 
        # check if exists in unique_list or not 
        if x not in unique_list: 
            unique_list.append(x) 
    return unique_list 

if __name__ == "__main__":
    wordClasses = ['Person', 'Place', 'Organisation']

    # Open and purify file
    openedFile = openAndPurifyFile('./input')
    # Delete stopwords
    purifiedString = tokenize(openedFile)
    # Remove stopwords
    purifiedString = removeStopwords(purifiedString)
    # Get sentences from string that matches to each other
    purifiedString = getSentencesFromWords(purifiedString)
    # Make all words/sentences start with uppercase
    wordsList = capitalizeList(purifiedString)
    # Send DBPedia Queries
    output = sendDBPediaQuery(wordsList, wordClasses)
    for word in output:
        start, end, textLen = findIndexesOfFoundWordInOriginalText(word, './input')
        print("Word "+ word + " position [" + str(start) + ', ' + str(end) + ']')
        fromStringToOutputFile(word, start, end, textLen)

