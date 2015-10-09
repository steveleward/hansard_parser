#!/usr/bin/env python

import os, csv, sys, re, requests, itertools, json
from bs4 import BeautifulSoup
from tools.io import escape_line_breaks

KEYS = ['url', 'date']
colex = re.compile(r'Column [\d]+')

tb_temp = r'([A-Z][a-z][\S\s]+) \(([\S\s]+)\) \(([\S\s]+)\)'
ob_temp = r'([A-Z][a-z][\S\s]+) \(([\S\s]+)\)'

name_temp = r'([Mr|Mr\.|Mrs|Mrs\.|Ms|Ms\.|Dr|Dr\.|Prof|Prof\.|Pf|Pf\.|Sir|Lord|Lady|Dame|Cr|Cr\.|Fr|Fr\. ]*)([A-Z][\S\s]+)? ([A-Z][\S\s]+)'
tailex = re.compile(r'\/debtext\/([\S]*)\.htm')
suffex = re.compile(r'\/mnt\/ssd0\/ukhansard\/pages\/([\S]*)')

tb_ex = re.compile(tb_temp)
ob_ex = re.compile(ob_temp)
name_ex = re.compile(name_temp)

validex = re.compile(r'[\d]{6,6}-[\d]{4,4}')

def get_all_files(dirpath):
    def is_valid(f):
        isfile = os.path.isfile(os.path.join(dirpath, f))
        vlist = validex.findall(f)
        if len(vlist) == 0:
            return False
        ideal_f = vlist[0]
        iscorrect = (f == ideal_f)
        return isfile and iscorrect
    all_files = [os.path.join(dirpath, f) for f in os.listdir(dirpath) if is_valid(f)]
    return all_files

def listsplit(iterable, rgex):
    return [list(g) for k, g in itertools.groupby(iterable, lambda x: len(rgex.findall(x)) > 0) if not k]

def _flatten_list(llist):
    return [item for sublist in llist for item in sublist]

def process_texts(texts):
    texts = 1
    texts = 1
    return [' '.join(text.split()) for text in texts]

def load_urls():
    urlfilepath = '/mnt/ssd0/ukhansard/pages/urls.txt'
    with open(urlfilepath, 'r') as f:
        urls = [url for url in f.read().split('\n') if len(url) > 0]
    return {tailex.findall(url)[0]: url for url in urls}

def get_filestem_groups():
    dirpath = '/mnt/ssd0/ukhansard/pages/'
    stemex = re.compile(r'\/mnt\/ssd0\/ukhansard\/pages\/([\S]*)')
    all_files = [stemex.findall(f)[0] for f in get_all_files(dirpath)]
    prefix_list = list(set([f[:6] for f in all_files]))
    filestem_groups = [[f for f in all_files if f[:6] == prefix] for prefix in prefix_list]
    return filestem_groups

def utf_encode_dct(dct):
    return {k: v.encode('utf-8') for k, v in dct.iteritems()}


class UKHansardParser(object):

    def __init__(self, filestems):
        self.soups = []
        self.filestems = filestems
        for filestem in filestems:
            filename = '/mnt/ssd0/ukhansard/pages/%s' % filestem
            with open(filename, 'r') as f:
                html_data = f.read()
                soup = BeautifulSoup(html_data, from_encoding='utf-8')
                self.soups.append(soup)
        self.paragraphs = self.get_paragraphs()
        self.speakers = self.get_speakers()
        self.speaker_metadata = self.get_speaker_metadata()
        self.urls = self.get_urls()
        self.date = self.get_date()
        self.para_dicts = self.get_para_dicts()

    def get_date(self):
        rawdate = self.filestems[0].split('-')[0]
        year, month, day = rawdate[:2], rawdate[2:4], rawdate[4:]
        return '/'.join([day, month, year])

    def get_urls(self):
        urllist = []
        for filestem in self.filestems:
            if filestem[0] == '0':
                url = urldict[filestem[1:]]
            else:
                url = urldict[filestem]
            urllist.append(url)
        return urllist

    def _create_dict(self, para):
        lst = para.split(':\n')
        if len(lst) > 1:
            speaker = lst[0]
            text = ' '.join(lst[1:])
        else:
            speaker = ''
            text = lst[0]
        return {'speaker': speaker.strip(), 'text': text.strip()}

    def _group_paras(self, paras):
        new_paras = []
        paras = [dct for dct in paras if dct != {'speaker': '', 'text': ''}]
        for i, para in enumerate(paras):
            if para['speaker'] != '' or i == 0:
                new_paras.append(para)
            else:
                new_paras[-1]['text'] += ' ' + para['text']
        return new_paras

    def get_paragraphs(self):
        parasllist = [[p.text for p in soup.find_all('p')] for soup in self.soups]
        paras = _flatten_list(parasllist)
        chunks = listsplit(paras, colex)
        paras = [self._create_dict(para) for para in _flatten_list(chunks)]
        return self._group_paras(paras)

    def get_speakers(self):
        raw_speakers = list(set([para['speaker'] for para in self.paragraphs]))
        return raw_speakers

    def parse_name(self, name):
        namelist = name_ex.findall(name)
        if len(namelist) > 0:
            nametuple = name_ex.findall(name)[0]
        else:
            nametuple = tuple(['', '', ''])
        return tuple([entry.strip() for entry in nametuple])

    def extract_first_last_name(self, para):
        speaker = para['speaker']
        tb_out = tb_ex.findall(speaker)
        ob_out = ob_ex.findall(speaker)
        if len(tb_out) > 0:
            name, _, _ = tb_out[0]
        elif len(ob_out) > 0:
            _, name = ob_out[0]
        else:
            name = speaker
        names = name_ex.findall(name)
        if len(names) > 0:
            title, first_name, last_name = names[0]
        else:
            title, first_name, last_name = '', '', ''
        return (title, first_name, last_name)

    def get_speaker_metadata(self):
        speaker_metadata = []
        for speaker in self.speakers:
            if len(tb_ex.findall(speaker)) > 0:
                name, electorate, party = tb_ex.findall(speaker)[0]
                title, first_name, last_name = self.parse_name(name)
                speaker_metadata.append({'title': title, 'first_name': first_name, 'last_name': last_name,
                                         'position': 'MP for ' + electorate, 'party': party})
            elif len(ob_ex.findall(speaker)) > 0:
                position, name = ob_ex.findall(speaker)[0]
                title, first_name, last_name = self.parse_name(name)
                speaker_metadata.append({'title': title, 'first_name': first_name, 'last_name': last_name,
                                         'position': position, 'party': ''})
        return speaker_metadata

    def get_para_dicts(self):
        para_dicts = []
        for i, para in enumerate(self.paragraphs):
            para['urls'] = json.dumps(self.urls)
            para['date'] = self.date
            para['id'] = self.filestems[0][:6] + ('_para_%i' % i)
            title, first_name, last_name = self.extract_first_last_name(para)
            appellation = para['speaker']
            for speaker in self.speaker_metadata:
                if last_name == speaker['last_name'] and first_name == speaker['first_name']:
                    para['speaker_metadata'] = json.dumps(speaker)
                    para_dicts.append(para)
                    break
                if appellation == speaker['position']:
                    para['speaker_metadata'] = json.dumps(speaker)
                    para_dicts.append(para)
                    break
        return para_dicts
