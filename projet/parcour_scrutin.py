
import locale # module pour gérer les locales (latin1, utf8 etc...)
import sys    # module pour gérer le système
locale.getpreferredencoding = lambda: 'UTF-8'

from urllib.request import urlopen
import bs4 as BeautifulSoup
import re
import csv



class MembreQueUnNomError(Exception) :
    pass


#reçois : tableau de string découpé ["MM","Prenom","Nom1", "Nom2", ...]
#supprime les MM, Mme, Mmes, M
#retourne : un nouveau tableau de 2 element ["prenom","Nom1 Nom2 Nom3"]
def nettoie_membre(membre) :
    
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
def parcours_membres(liste_membres) :
    taille = len(liste_membres)
    for membre in range(taille) :
        liste_membres[membre] =  liste_membres[membre].replace(".","")
        liste_membres[membre] = re.sub('\(.*?\)', '', liste_membres[membre])
        liste_membres[membre] = liste_membres[membre].split()
        liste_membres[membre] = nettoie_membre(liste_membres[membre])
        
        spamwriter.writerow([str(current_legislature), current_date, current_num_scrutin, current_nom_scrutin,
                            current_groupe_politique, liste_membres[membre][1], liste_membres[membre][0], current_vote]);
        #fichier.write(str(current_legislature)+" | "+current_date+" | "+current_num_scrutin+" | "+current_nom_scrutin+" | "+current_groupe_politique+" | "+liste_membres[membre][1]+" | "+liste_membres[membre][0]+" | "+current_vote+"\n")

    return liste_membres


def parcours_paragraphe_membre(paragraphe) :
    liste_membres = paragraphe.text.split(",");
    if(liste_membres[-1].find(" et ") != -1) :
        avant_dernier,dernier = liste_membres[-1].split(" et ")
        liste_membres[-1] = avant_dernier
        liste_membres.append(dernier)
    liste_membres = parcours_membres(liste_membres)





current_legislature = None
current_date = None
current_num_scrutin = None
current_nom_scrutin = None
current_groupe_politique = None
current_vote = None
current_legislature = 11



nom_fichier = 'votes.csv'
fichier = open(nom_fichier, 'a', newline='')
spamwriter = csv.writer(fichier, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)


#html = urlopen('http://www.assemblee-nationale.fr/12/scrutins/jo0437.asp').read()
#html = urlopen('http://www.assemblee-nationale.fr/11/scrutins/jo0374.asp').read()
#html = urlopen('http://www.assemblee-nationale.fr/11/scrutins/jo0100.asp').read()
#html = urlopen('http://www.assemblee-nationale.fr/11/scrutins/jo0001.asp').read()
html = open('./scrutins/11-379.html', encoding = "ISO-8859-1").read()


soup = BeautifulSoup.BeautifulSoup(html)

paragraphes = soup.find_all("p")


#Parcour des "<p>"
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
        print("NOM DE SCRUTIN = "+current_nom_scrutin)


    re_groupe_parti = re.match('(GROUPE)\s*(([^\s]+\s?)*[^\s])\s*(\(.*\))', paragraphes[p].text.replace("\n", ""), re.DOTALL)
    if(re_groupe_parti) :
        current_groupe_politique = re_groupe_parti.group(2)
        print("--"+re_groupe_parti.group(2)+"--"+re_groupe_parti.group(4))


    re_groupe_no_parti = re.match('(DEPUTES\s*NON\s*INSCRITS)\s*(\(.*\))', paragraphes[p].text.replace("É","E").replace("-"," "), re.DOTALL)
    if(re_groupe_no_parti) :
        current_groupe_politique = re_groupe_no_parti.group(1)
        print("--"+re_groupe_no_parti.group(1)+"--"+re_groupe_no_parti.group(2))



    re_groupe_vote = re.match('(POUR|CONTRE|NON-VOTANT|ABSTENTION)', paragraphes[p].text, re.DOTALL)

    if(re_groupe_vote) :
        current_vote = re_groupe_vote.group(1)
        parcours_paragraphe_membre(paragraphes[p+1])
        print(re_groupe_vote.group(1))


fichier.close()



