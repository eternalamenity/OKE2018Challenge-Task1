from SPARQLWrapper import SPARQLWrapper, JSON
from pynif import NIFCollection
import rdflib
import re
import nltk
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

def getSentencesFromWords(tokens):         
    serie = ''
    series = []
    counter = 0
    for token in tokens:
        if  token[0].isupper():
            if  serie == '':
                serie = serie + token
            else:
                serie = serie + '_' + token
            counter = counter + 1
            if counter == 2:
                counter = 0
                series += [serie]
                serie = ''
        else:
            if serie != '':
                series += [serie]
            series += [token]
            serie = ''
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