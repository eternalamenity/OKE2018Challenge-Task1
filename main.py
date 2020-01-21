from SPARQLWrapper import SPARQLWrapper, JSON
from pynif import NIFCollection
from itertools import tee, islice, chain
import re
import nltk
from tkinter import *
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

def firstStringToOutputFile():
    f_input = open("input","r")
    contents = f_input.read()
    f = open("output","w+")
    f.write(contents)
    f.close()
    f_input.close()

def fromStringToOutputFile(outputString, start, end, textLen):
    f_input = open("output","r")
    contents = f_input.read()
    f = open("output","w+")
    splittedOutputString = outputString.translate ({ord(c): " " for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+"})
    f.write(contents)
    f.write('<http://example.com/example-task1#char=' + str(start) + ',' + str(end) + '>\n')
    f.write('        a                     nif:RFC5147String , nif:String ;\n')
    f.write('        nif:anchorOf          "' + splittedOutputString + '"@en ;\n')
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


def fromStringToInputFile(inputText):
    f = open("input","w+")
    f.write('@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n')
    f.write('@prefix nif: <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#> .\n')
    f.write('@prefix dbpedia: <http://dbpedia.org/resource/> .\n')
    f.write('@prefix itsrdf: <http://www.w3.org/2005/11/its/rdf#> .\n')
    f.write('<http://example.com/example-task1#char=0,' + str(len(inputText)) + '>\n')
    f.write('        a                     nif:RFC5147String , nif:String , nif:Context ;\n')
    f.write('        nif:beginIndex        "0"^^xsd:nonNegativeInteger ;\n')
    f.write('        nif:endIndex          "' + str(len(inputText)) + '"^^xsd:nonNegativeInteger ;\n')
    f.write('        nif:isString          "' + inputText + '"@en .\n')
    f.close()

def mainFunctionality():
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
    # Create initial OUTPUT file
    firstStringToOutputFile()
    for word in output:
        start, end, textLen = findIndexesOfFoundWordInOriginalText(word, './input')
        print("Word "+ word + " position [" + str(start) + ', ' + str(end) + ']')
        fromStringToOutputFile(word, start, end, textLen)



def clicked():
    test = txt.get()
    fromStringToInputFile(test)
    mainFunctionality()
    #Put output to box
    data = ''
    with open('output', 'r') as file:
        data = file.read()
    wynik.config(state=NORMAL)
    wynik.insert(1.0, data)
    wynik.config(state=DISABLED)


if __name__ == '__main__':
    window = Tk()
    window.resizable(width=False, height=False)
    window.title("Task 1")
    window.geometry('1280x720')
    lbl = Label(window, text="Enter your text:")
    wynik = Text(window,height=24,width=87)
    wynik.config(state=DISABLED)
    lbl.grid(column=0, row=0)
    lbl.place(x=10,y=10)
    wynik.place(x=10,y=80)
    txt = Entry(window, width=100)
    txt.grid(column=1, row=0)
    txt.place(x=100,y=10)
    btn = Button(window, text="Check", command=clicked)
    btn.grid(column=5, row=5)
    btn.place(x=340,y=40)
    window.mainloop()