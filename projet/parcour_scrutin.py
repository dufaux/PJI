
import locale # module pour gérer les locales (latin1, utf8 etc...)
import sys    # module pour gérer le système
locale.getpreferredencoding = lambda: 'UTF-8'

from urllib.request import urlopen
import bs4 as BeautifulSoup
import re
import csv
import glob
import logging


class MembreQueUnNomError(Exception) :
    pass

class NomDeScrutinError(Exception) :
    pass

class DonneeVideError(Exception) :
    pass

class CalculNombreVotantError(Exception) :
    pass

class DonneeChangeeAnormalementError(Exception) :
    pass

class TotalVotantDifferentError(Exception) :
    pass

#reçois : tableau de string découpé ["MM","Prenom","Nom1", "Nom2", ...]
#supprime les MM, Mme, Mmes, M
#retourne : un nouveau tableau de 2 element ["prenom","Nom1 Nom2 Nom3"]
def nettoie_membre(membre) :
    global current_date
    global current_num_scrutin
    global current_nom_scrutin
    global current_groupe_politique
    global current_vote
    global current_legislature


    if "MM" in membre :
        membre.remove("MM")
    if "Mme" in membre :
        membre.remove("Mme")
    if "Mmes" in membre :
        membre.remove("Mmes")
    if "M" in membre :
        membre.remove("M")


    taille = len(membre)
    if taille == 0 :
        raise MembreQueUnNomError("Membre nul trouvé ?")
    if taille == 1 :
        raise MembreQueUnNomError("Membre "+membre[0]+" n'a qu'un seul nom/prenom")

    return [membre[0]," ".join(membre[1:])];


#reçois : tableau de string découpé ["MM Prenom Nom","Prenom Nom Nom1", "...", ...]
#découpe chaque "membre", supprime les points, puis appelle nettoie_membre.
#retourne : un nouveau tableau de membre "nettoyés" [["Prenom1","Nom1"],["Prenom2","Nom2"],[...],...]
def parcours_membres(liste_membres, nbr) :
    taille = len(liste_membres)

    if(taille != nbr) :


        for membre in range(taille) :
            print(liste_membres[membre])

        raise CalculNombreVotantError("Le nombre de votant ne correspond pas: "+str(taille)+" -- Attendu: "+str(nbr)+" !")
    

    for membre in range(taille) :
        liste_membres[membre] =  liste_membres[membre].replace(".","")
        liste_membres[membre] = re.sub('\(.*?\)', '', liste_membres[membre])
        liste_membres[membre] = liste_membres[membre].split()
        liste_membres[membre] = nettoie_membre(liste_membres[membre])
        
        if(current_legislature == None or current_date == None or current_num_scrutin == None or current_nom_scrutin == None or current_groupe_politique == None or current_vote == None or liste_membres[membre][1] == None or liste_membres[membre][0] == None) :
            raise DonneeVideError()

        #ecrit dans le fichier.        
        spamwriter.writerow([str(current_legislature), current_date, current_num_scrutin, current_nom_scrutin,
                            current_groupe_politique, liste_membres[membre][1], liste_membres[membre][0], current_vote]);
        #fichier.write(str(current_legislature)+" | "+current_date+" | "+current_num_scrutin+" | "+current_nom_scrutin+" | "+current_groupe_politique+" | "+liste_membres[membre][1]+" | "+liste_membres[membre][0]+" | "+current_vote+"\n")

    return liste_membres


def parcours_paragraphe_membre(paragraphe, nbr) :
    liste_membres = paragraphe.text.split(",");
    if(liste_membres[-1].find(" et ") != -1) :
        avant_dernier,dernier = liste_membres[-1].split(" et ")
        liste_membres[-1] = avant_dernier
        liste_membres.append(dernier)
    liste_membres = parcours_membres(liste_membres, nbr)


def reset_currents_all() :
    global current_date
    global current_num_scrutin
    global current_nom_scrutin
    global current_groupe_politique
    global current_vote
    global current_legislature
    global current_nb_votant

    current_date = None
    current_num_scrutin = None
    current_nom_scrutin = None
    current_groupe_politique = None
    current_vote = None
    current_legislature = 11
    current_nb_votant = None


def reset_currents_groupe_vote() :
    global current_groupe_politique
    global current_vote

    current_groupe_politique = None
    current_vote = None



def parcours_scrutin_html(url) :

    global current_date
    global current_num_scrutin
    global current_nom_scrutin
    global current_groupe_politique
    global current_vote
    global current_nb_votant
    global logger

    print(" ########################### PARCOURS DE "+url+" ###########################") 

    total_votant = 0;

    #html = open('./scrutins/11-132.html', encoding = "ISO-8859-1").read()
    html = open(url, encoding = "ISO-8859-1").read()

    #supprime les retour à la ligne et les espace nombreux
    html = html.replace('\n','')
    html = html.replace('\r','')
    html = ' '.join(html.split())

    soup = BeautifulSoup.BeautifulSoup(html)
    paragraphes = soup.find_all("p")

    #Parcour des "<p>"
    #Normalement, chaque groupe de votant est précédé de son vote (pour/contre..) et de son partie.
    nb_paragraphe = len(paragraphes)
    for p in range(nb_paragraphe) :



        re_groupe_num_scrutin = re.match('\s*(ANALYSE DU SCRUTIN) N° ([0-9]+)', paragraphes[p].text, re.DOTALL)
        re_groupe_date = re.match('.*(Séance du) ([0-9]{1,2}(er)? [0-9A-Za-zéû]* (19|20)\d\d)', paragraphes[p].text, re.DOTALL)
        re_groupe_nom_scrutin = re.match(".*SCRUTIN PUBLIC.*", paragraphes[p].text, re.DOTALL)

        re_groupe_nb_votant = re.match(".*Nombre de votants\s*:\s*([0-9]*).*", paragraphes[p].text)
        
        if (re_groupe_nb_votant) :
            if(current_nb_votant != None) :
                raise DonneeChangeeAnormalementError("Nbr de votant déjà présent!")
            current_nb_votant = int(re_groupe_nb_votant.group(1))

        if (re_groupe_num_scrutin) :
            if(current_num_scrutin != None) :
                raise DonneeChangeeAnormalementError("Numéro de scrutin déjà présent!")            
            
            current_num_scrutin = str(re_groupe_num_scrutin.group(2))
            print("NUMERO DE SCRUTIN = "+current_num_scrutin)

        if (re_groupe_date) :
            if(current_date != None) :
                raise DonneeChangeeAnormalementError("Date déjà présente!")            
            
            current_date = re_groupe_date.group(2)
            print("DATE DU SCRUTIN = "+current_date)


        if (re_groupe_nom_scrutin) :
            if(current_nom_scrutin != None) :
                raise DonneeChangeeAnormalementError("Nom de scrutin déjà présent!")            
            
            current_nom_scrutin = paragraphes[p+1].text
            i = 2
            while (paragraphes[p+i].find("font",{"color" : "#000066"})) != None :
                if (paragraphes[p+i].text.find("Nombre de votants") !=-1) :
                    raise NomDeScrutinError("ERREUR DU PARAGRAPHE NBR DE VOTANT SUR SCRUTIN: "+current_nom_scrutin)
                current_nom_scrutin +=" "+paragraphes[p+i].text
                i += 1
            current_nom_scrutin = current_nom_scrutin.replace('\n','')
            current_nom_scrutin = current_nom_scrutin.replace('\r','')
            print("NOM DU SCRUTIN = "+current_nom_scrutin)


        re_groupe_parti = re.match('\s*(GROUPE)\s*(([^\s]+\s?)*[^\s])\s*(\(.*)', paragraphes[p].text.replace("\n", ""), re.DOTALL)
        re_groupe_no_parti = re.match('\s*(DEPUTES\s*NON\s*INSCRITS)\s*(\(.*)', paragraphes[p].text.replace("É","E").replace("-"," "), re.DOTALL)
        re_groupe_vote = re.match('\s*(POUR|CONTRE|NON-VOTANT|ABSTENTION)\s*:([\s\.])*([0-9]*)', paragraphes[p].text, re.DOTALL)


        if(re_groupe_parti) :
            reset_currents_groupe_vote()
            current_groupe_politique = re_groupe_parti.group(2)
            print("--"+re_groupe_parti.group(2)+"--"+re_groupe_parti.group(4))

        if(re_groupe_no_parti) :
            reset_currents_groupe_vote()
            current_groupe_politique = re_groupe_no_parti.group(1)
            print("--"+re_groupe_no_parti.group(1)+"--"+re_groupe_no_parti.group(2))

        if(re_groupe_vote) :
            current_vote = re_groupe_vote.group(1)
            try :
                nbr = int(re_groupe_vote.group(3))
            except :
                print(" PROBLEME NOMBRE VOTANT SUR ''"+current_groupe_politique+" -- "+re_groupe_vote.group(1)+"'' DANS LE FICHIER "+url)
                raise

            print(re_groupe_vote.group(1))
            print("Nombre = "+re_groupe_vote.group(3))
            total_votant += nbr
            parcours_paragraphe_membre(paragraphes[p+1], nbr)



    
    if(current_nb_votant != total_votant) :
        if(current_nb_votant != None) :
            raise TotalVotantDifferentError("Nombre : "+str(total_votant)+", Attendu : "+str(current_nb_votant))
        logger.error("Nombre de votant incohérent pour fichier "+url)
    

    del html
    del soup
    del paragraphes


#######################################################################
###############__######__#######__#######__####___####__###############
###############___####___#####______###########____###__###############
###############____##____####___##___####__####__#__##__###############
###############__#____#__####________####__####__##__#__###############
###############__######__####__####__####__####__###____###############
###############__######__####__####__####__####__####___###############
#######################################################################


current_legislature = None
current_date = None
current_num_scrutin = None
current_nom_scrutin = None
current_groupe_politique = None
current_vote = None
current_legislature = 11
current_nb_votant = None


logging
logger = logging.getLogger('myapp')
hdlr = logging.FileHandler('./logs/11.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.WARNING)



nom_fichier = 'votes.csv'
fichier = open(nom_fichier, 'a', newline='')
spamwriter = csv.writer(fichier, delimiter=',')
#spamwriter = csv.writer(fichier, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)



lst_scrutins_html = glob.glob('./scrutins/*.html')    #On liste uniquement les fichiers '.html'
lst_scrutins_html.sort()
print(lst_scrutins_html)


for s in range(len(lst_scrutins_html)) :
    parcours_scrutin_html(lst_scrutins_html[s])
    reset_currents_all()

    #fichier.close()
    #fichier = open(nom_fichier, 'a', newline='')
    #spamwriter = csv.writer(fichier, delimiter=',')

"""
#html = urlopen('http://www.assemblee-nationale.fr/12/scrutins/jo0437.asp').read()
#html = urlopen('http://www.assemblee-nationale.fr/11/scrutins/jo0374.asp').read()
#html = urlopen('http://www.assemblee-nationale.fr/11/scrutins/jo0100.asp').read()
#html = urlopen('http://www.assemblee-nationale.fr/11/scrutins/jo0001.asp').read()
html = open('./scrutins/11-379.html', encoding = "ISO-8859-1").read()


soup = BeautifulSoup.BeautifulSoup(html)

paragraphes = soup.find_all("p")


#Parcour des "<p>"
#Normalement, chaque groupe de votant est précédé de son vote (pour/contre..) et de son partie.
nb_paragraphe = len(paragraphes)
for p in range(nb_paragraphe) :

    #retire les retour à la ligne et les espaces supplémentaires.
    paragraphes[p].string = paragraphes[p].text.replace('\n','')
    paragraphes[p].string = paragraphes[p].text.replace('\r','')
    paragraphes[p].string = ' '.join(paragraphes[p].text.split())


    re_groupe_num_scrutin = re.match('(ANALYSE DU SCRUTIN) N° ([0-9]+)', paragraphes[p].text, re.DOTALL)
    re_groupe_date = re.match('.*(Séance du) ([0-9]{1,2} [0-9A-Za-zéû]* (19|20)\d\d)', paragraphes[p].text, re.DOTALL)
    re_groupe_nom_scrutin = re.match(".*SCRUTIN PUBLIC.*SUR", paragraphes[p].text, re.DOTALL)

    #print("PARAGRAPHE TEXT = "+paragraphes[p].text)

    if (re_groupe_num_scrutin) :
        current_num_scrutin = str(re_groupe_num_scrutin.group(2))
        print("NUMERO DE SCRUTIN = "+current_num_scrutin)

    if (re_groupe_date) :
        current_date = re_groupe_date.group(2)
        print("DATE DU SCRUTIN = "+current_date)


    if (re_groupe_nom_scrutin) :
        current_nom_scrutin = paragraphes[p+1].text
        i = 2
        while (paragraphes[p+i].find("font",{"color" : "#000066"})) != None :
            if (paragraphes[p+i].text.find("Nombre de votants") !=-1) :
                raise NomDeScrutinError("ERREUR DU PARAGRAPHE NBR DE VOTANT SUR SCRUTIN: "+current_nom_scrutin)
            current_nom_scrutin +=" "+paragraphes[p+i].text
            i += 1
        current_nom_scrutin = current_nom_scrutin.replace('\n','')
        current_nom_scrutin = current_nom_scrutin.replace('\r','')
        print("NOM DU SCRUTIN = "+current_nom_scrutin)


    re_groupe_parti = re.match('(GROUPE)\s*(([^\s]+\s?)*[^\s])\s*(\(.*\))', paragraphes[p].text.replace("\n", ""), re.DOTALL)
    re_groupe_no_parti = re.match('(DEPUTES\s*NON\s*INSCRITS)\s*(\(.*\))', paragraphes[p].text.replace("É","E").replace("-"," "), re.DOTALL)
    re_groupe_vote = re.match('(POUR|CONTRE|NON-VOTANT|ABSTENTION)', paragraphes[p].text, re.DOTALL)


    if(re_groupe_parti) :
        reset_currents_groupe_vote()
        current_groupe_politique = re_groupe_parti.group(2)
        print("--"+re_groupe_parti.group(2)+"--"+re_groupe_parti.group(4))

    if(re_groupe_no_parti) :
        reset_currents_groupe_vote()
        current_groupe_politique = re_groupe_no_parti.group(1)
        print("--"+re_groupe_no_parti.group(1)+"--"+re_groupe_no_parti.group(2))

    if(re_groupe_vote) :
        current_vote = re_groupe_vote.group(1)
        parcours_paragraphe_membre(paragraphes[p+1])
        print(re_groupe_vote.group(1))
"""

fichier.close()



