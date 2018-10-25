
# coding: utf-8

# In[ ]:


#the new version before boosting
#!/usr/bin/env python
import argparse
import sys
import codecs
if sys.version_info[0] == 2:
    from itertools import izip
else:
    izip = zip
from collections import defaultdict as dd
import re
import os.path
import gzip
import tempfile
import shutil
import atexit
from string import punctuation

import nltk
from nltk.tokenize import word_tokenize

scriptdir = os.path.dirname(os.path.abspath('__file__'))

reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')
def prepfile(fh, code):
    if type(fh) is str:
        fh = open(fh, code)
    ret = gzip.open(fh.name, code if code.endswith("t") else code+"t") if fh.name.endswith(".gz") else fh
    if sys.version_info[0] == 2:
        if code.startswith('r'):
            ret = reader(fh)
        elif code.startswith('w'):
            ret = writer(fh)
        else:
            sys.stderr.write("I didn't understand code "+code+"\n")
            sys.exit(1)
    return ret

def addonoffarg(parser, arg, dest=None, default=True, help="TODO"):
    ''' add the switches --arg and --no-arg that set parser.arg to true/false, respectively'''
    group = parser.add_mutually_exclusive_group()
    dest = arg if dest is None else dest
    group.add_argument('--%s' % arg, dest=dest, action='store_true', default=default, help=help)
    group.add_argument('--no-%s' % arg, dest=dest, action='store_false', default=default, help="See --%s" % arg)

from nltk.tokenize import word_tokenize
class LimerickDetector:
    def __init__(self):
        self._pronunciations = nltk.corpus.cmudict.dict()
    def num_syllables(self, word):
        
        word = word.lower()
        if word not in self._pronunciations:
            return 1
        else:
            syl = 0
            mini = []
            for i in range(len(self._pronunciations[word])):
                for z in self._pronunciations[word][i]:
                    #Since cudict puts digits on new syllables / vowel sounds
                    if not z.isalpha():
                    
                        syl+=1
                        
                mini.append(syl)
                syl =0
            syl= min(mini)
            return max (1, syl)        
  
    def rhymes(self, a, b):
       
        a = a.lower()
        b = b.lower()
        if a not in self._pronunciations or b not in self._pronunciations:
            return False
        t1 = cons_elem(a)
        t2 = cons_elem(b)
        for set1 in t1:
            for set2 in t2:
                diff = 0
                count = 0 
                check = False
                if set1==set2:
                    return True
                elif cmp(len(set1),len(set2)) > 0:
                    diff = len(set1) - len (set2)
                    while diff<len(set1):
                        if set1[diff] != set2[count]:
                            check = False
                            break
                        else:
                            #check = True ??
                            return True
                        count+=1
                        diff+=1
                elif cmp(len(set1),len(set2)) < 0:
                    diff = len(set2) - len (set1)
                    while diff<len(set2):

                        if set2[diff] != set1[count]:
                            check = False
                            break
                        else:
                            #check = True ??
                            return True
                        count+=1
                        diff+=1
        return check
    
    def is_limerick(self, son):
        
        punct = set(['.', ',', '!', ':', ';','?','(',')','[',']','``','"'])
        son = son.lower()
        each_syl = []
        last_words = []
        is_lime = False
        son = os.linesep.join([s for s in son.splitlines() if s.strip()])
        sentence_split=son.split('\n')
        if len(sentence_split) <> 5:
            return False
        for ln in sentence_split:       
            words_of_sentence = word_tokenize(ln)
            my_list = []
            for w in words_of_sentence:
                if w not in punct:
                    my_list.append(w)
            nums = 0 
            for f in my_list:
                nums+= self.num_syllables(f)
            each_syl.append(nums)
            if nums <4:
                return False
            last_words.append(my_list[len(my_list)-1])
        if self.rhymes(last_words[2],last_words[3]) ==True:
            if  self.rhymes(last_words[1],last_words[4])==True and self.rhymes(last_words[0],last_words[1]) ==True and self.rhymes(last_words[0],last_words[4])== True:
                if self.rhymes(last_words[0],last_words[2])==False and self.rhymes(last_words[1],last_words[2])==False and self.rhymes(last_words[4],last_words[2])==False:
                    if self.rhymes(last_words[0],last_words[3])==False and self.rhymes(last_words[1],last_words[3])==False and self.rhymes(last_words[4],last_words[3])==False:
                        if abs(each_syl[0]-each_syl[1]) <= 2 and abs(each_syl[1]-each_syl[4]) <= 2 and abs(each_syl[0]-each_syl[4]) <= 2:
                            if abs(each_syl[2]-each_syl[3]) <= 2:
                                if each_syl[2]<each_syl[0] and each_syl[2]<each_syl[1] and each_syl[2]<each_syl[4]:
                                    if each_syl[3]<each_syl[0] and each_syl[3]<each_syl[1] and each_syl[3]<each_syl[4]:
                                        return True
                                    
        return False
def cons_elem(word):
    elst = []
    prondict = nltk.corpus.cmudict.dict()
    temp1 = prondict[word]
    for i in range(len(temp1)): 
        for z in range(len(temp1[i])):
            #VOWEL SOUNDS HAVE DIGIT IN CMUDICT
            if temp1[i][z].isalpha():
                pass
            else:
                break
        elst.append(temp1[i][z:])
    return elst             
def main():
    parser = argparse.ArgumentParser(description="limerick detector. Given a file containing a poem, indicate whether that poem is a limerick or not",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    addonoffarg(parser, 'debug', help="debug mode", default=False)
    parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
    parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")
    try:
        args = parser.parse_args()
    except IOError as msg:
        parser.error(str(msg))
    infile = prepfile(args.infile, 'r')
    outfile = prepfile(args.outfile, 'w')
    ld = LimerickDetector()
    lines = ''.join(infile.readlines())
    outfile.write("{}\n-----------\n{}\n".format(lines.strip(), ld.is_limerick(lines)))
    if __name__ == '__main__':
        main()

