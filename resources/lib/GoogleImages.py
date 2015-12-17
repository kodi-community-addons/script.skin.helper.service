#!/usr/bin/python

from Utils import *
import BeautifulSoup
import htmlentitydefs
import urllib2, re


class googleImagesAPI:
    baseURL = 'https://www.google.com/search?hl=en&site=imghp&tbm=isch&tbs=isz:m{start}{query}'
    perPage = 1
    
    def __init__(self):
        pass
                
    def createQuery(self,terms,**kwargs):
        args = ['q={0}'.format(urllib.quote_plus(terms))]
        for k in kwargs.keys():
            if kwargs[k]: args.append('{0}={1}'.format(k,kwargs[k]))
        return '&'.join(args)
        
    def parseQuery(self,query):
        return dict(urlparse.parse_qsl(query))
    
    def parseImages(self,html):
        soup = BeautifulSoup.BeautifulSoup(html)
        results = []
        for td in soup.findAll('td'):
            if td.find('td'): continue
            br = td.find('br')
            if br: br.extract()
            cite = td.find('cite')
            site = ''
            if cite:
                site = cite.string
                cite.extract()
            i = td.find('a')
            if not i: continue
            if i.text or not '/url?q' in i.get('href',''): continue
            for match in soup.findAll('b'):
                match.string = '[COLOR FF00FF00][B]{0}[/B][/COLOR]'.format(str(match.string))
                match.replaceWithChildren()
            page = urllib.unquote(i.get('href','').split('q=',1)[-1].split('&',1)[0]).encode('utf-8')
            tn = ''
            img = i.find('img')
            if img: tn = img.get('src')
            image = tn
            results.append({'unescapedUrl':image,'page':page})
        return results
    
    def getImages(self,query,page=1):
        start = ''
        if page > 1: start = '&start=%s' % ((page - 1) * self.perPage)
        url = self.baseURL.format(start=start,query='&' + query)
        html = self.getPage(url)
        return self.parseImages(html)

    def getPage(self,url):
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        html = opener.open(url).read()
        return html
        
    def getPageImages(self,url):
        html = self.getPage(url)
        soup = BeautifulSoup.BeautifulSoup(html)
        results = []
        for img in soup.findAll('img'):
            src = img.get('src')
            if src: results.append({'title':src,'url':urlparse.urljoin(url,src),'file':src.split('/')[-1]})
        return results
