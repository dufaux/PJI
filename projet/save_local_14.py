import locale # module pour gérer les locales (latin1, utf8 etc...)
import sys    # module pour gérer le système
locale.getpreferredencoding = lambda: 'UTF-8'

from urllib.request import urlopen
import bs4 as BeautifulSoup
import re
import time
import os.path
import sys 

def parcours_sommaire(url_locale) :
    html = open(url_locale, encoding = "ISO-8859-1").read()
    soup = BeautifulSoup.BeautifulSoup(html)
    regex = '\[?\s*(analyse\s*du\s*scrutin)\s*\]?'

    liens = soup.find_all("a")
    nb_liens = len(liens)

    for a in range(nb_liens) :

        #retire les retour à la ligne et les espaces supplémentaires.
        liens[a].string = liens[a].text.replace('\n','')
        liens[a].string = liens[a].text.replace('\r','')
        liens[a].string = ' '.join(liens[a].text.split())


        re_groupe_lien = re.match(regex, liens[a].text)
        if(re_groupe_lien) :
            url = liens[a]['href']
            enregistrer_page("http://www2.assemblee-nationale.fr"+url) #lien relatif donc ajout du http://www2.assemblee-nationale.fr




def enregistrer_page(url) :
    numero = url.split('/')[-1] #recupere le dernier element d'url (XXX)
    namefile = 'scrutins'+legislature+'/'+legislature+'-'+str(numero)+'.html'

            
    print("###############################################################################")
    print(url+" et numero = "+str(numero))
    if not os.path.isfile(namefile) :
        time.sleep(3)          # attente pour "temporiser" l'enregistrement
        u = urlopen(url)
        page = u.read()
        print(page)
                
        localFile = open(namefile, 'wb')
        localFile.write(page)
        localFile.close()





########################################################################################################
##############################    MAIN     #############################################################
########################################################################################################


legislature = "14"
scrutins = sys.argv[1] # 0 pour enregistrer les pages "sommaires" depuis le net,
                       # autre pour enregistrer chaque scrutin depuis les liens net des pages "sommaire" locales.


indicemax = 1000 # que 10 pages pour l'instant 1000*10


indice = 0
if scrutins == "0" :
    while(indice <= indicemax) :
        namefile = "./ressources/liste14-"+str(indice)+".html"
        somm = "http://www2.assemblee-nationale.fr/scrutins/liste/(offset)/"+str(indice)+"/(legislature)/14/(type)/TOUS/(idDossier)/TOUS"
        #tente d'ouvrir en utf-8. Sinon en iso 8859.

        if not os.path.isfile(namefile) :
            u = urlopen(somm)
            page = u.read()
            print(page)
                
            localFile = open(namefile, 'wb')
            localFile.write(page)
            localFile.close()
            time.sleep(3)

        indice = indice + 100

        
else :
    partie = sys.argv[2] #pour savoir quel page enregistrer.
                         #-1 si on veut tout de même tout enregistrer en même temps.
                         #(3s par page pour pas ralentir le site).

    if partie == "-1" :
        while(indice <= indicemax) :
            url_locale = "./ressources/liste14-"+str(indice)+".html"
            parcours_sommaire(url_locale)
            indice = indice + 100
    else :
        url_locale = "./ressources/liste14-"+partie+".html"
        parcours_sommaire(url_locale)

