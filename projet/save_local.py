import locale # module pour gérer les locales (latin1, utf8 etc...)
import sys    # module pour gérer le système
locale.getpreferredencoding = lambda: 'UTF-8'

from urllib.request import urlopen
import bs4 as BeautifulSoup
import re
import time
import os.path

#html = open('./ressources/liste11.html', encoding = "ISO-8859-1").read()
#html = open('./ressources/liste12.html', encoding = "ISO-8859-1").read()
#html = open('http://www.assemblee-nationale.fr/13/scrutins/table-2006-2007.asp', encoding = "ISO-8859-1").read()
#soup = BeautifulSoup.BeautifulSoup(html)

legislature = "13"
partie = "2011-2012"

if legislature == "11" :
    html = open('./ressources/liste11.html', encoding = "ISO-8859-1").read()
    regex = 'N° ([0-9]+)'
elif legislature == "12" :
    html = open('./ressources/liste12.html', encoding = "ISO-8859-1").read()
    regex =  'n° ([0-9]+)'
elif legislature == "13" :
    html = open('./ressources/liste13-'+partie+'.html', encoding = "ISO-8859-1").read()
    regex = '\[?\s*(analyse\s*du\s*scrutin)\s*\]?'
else :
    raise Exception("pas de legislature correcte")

soup = BeautifulSoup.BeautifulSoup(html)



liens = soup.find_all("a")
nb_liens = len(liens)

print(str(nb_liens)+ " liens (donc scrutin!).")

for a in range(nb_liens) :

    #retire les retour à la ligne et les espaces supplémentaires.
    liens[a].string = liens[a].text.replace('\n','')
    liens[a].string = liens[a].text.replace('\r','')
    liens[a].string = ' '.join(liens[a].text.split())


    """#re_groupe_lien = re.match('N° ([0-9]+)', liens[a].text) # pour la 11em
    #re_groupe_lien = re.match('n° ([0-9]+)', liens[a].text) # pour la 12em
    re_groupe_lien = re.match('n° ([0-9]+)\[?\s*(analyse\s*du\s*scrutin)\s*\]?', liens[a].text) # pour la 13em"""
    re_groupe_lien = re.match(regex, liens[a].text)
    if(re_groupe_lien) :
        url = liens[a]['href']

        if legislature == "13" :
            numero = url.split('/')[-1].split('.')[0] #recupere le dernier element d'url (joXXX.asp) et le premier avant le point.
        else :
            numero = re_groupe_lien.group(1)

        namefile = 'scrutins'+legislature+'/'+legislature+'-'+str(numero)+'.html'
        if not os.path.isfile(namefile) :
            u = urlopen(url)
            page = u.read()
            print(page)
            
            localFile = open(namefile, 'wb')
            localFile.write(page)
            localFile.close()

            time.sleep(3)


        print("###############################################################################")
        print(liens[a].string+" et numero = "+str(numero))
        print(url)







