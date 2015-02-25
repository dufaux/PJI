import locale # module pour gérer les locales (latin1, utf8 etc...)
import sys    # module pour gérer le système
locale.getpreferredencoding = lambda: 'UTF-8'

from urllib.request import urlopen
import bs4 as BeautifulSoup
import re
import time

#html = open('./ressources/liste11.html', encoding = "ISO-8859-1").read()
html = open('./ressources/liste12.html', encoding = "ISO-8859-1").read()

soup = BeautifulSoup.BeautifulSoup(html)

liens = soup.find_all("a")
nb_liens = len(liens)

print(str(nb_liens)+ " liens (donc scrutin!).")

for a in range(nb_liens) :

    #retire les retour à la ligne et les espaces supplémentaires.
    liens[a].string = liens[a].text.replace('\n','')
    liens[a].string = liens[a].text.replace('\r','')
    liens[a].string = ' '.join(liens[a].text.split())


    #re_groupe_lien = re.match('N° ([0-9]+)', liens[a].text) # pour la 11em
    re_groupe_lien = re.match('n° ([0-9]+)', liens[a].text) # pour la 12em
    if(re_groupe_lien) :
        url = liens[a]['href']
        numero = re_groupe_lien.group(1)

        u = urlopen(url)
        page = u.read()
        print(page)
        namefile = 'scrutins12/12-'+str(numero)+'.html'

        localFile = open(namefile, 'wb')
        localFile.write(page)
        localFile.close()

        print(liens[a].string+" et numero = "+str(numero))
        print(url)

        time.sleep(3)







