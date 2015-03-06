import locale # module pour gerer les locales (latin1, utf8 etc...)
import sys    # module pour gérer le système
locale.getpreferredencoding = lambda: 'UTF-8'

from urllib.request import urlopen
import bs4 as BeautifulSoup
import re
import csv
import glob
import logging



## Variables globales :
##  global current_legislature
##  global current_date
##  global current_num_scrutin
##  global current_nom_scrutin
##  global current_groupe_politique
##  global current_vote
##  global current_legislature
##  global current_nb_votant
##  enregistrement ## (si on doit enregistrer les données ou juste parcourir pour voir les erreurs).
##  global name_file

class MembreQueUnNomError(Exception) :
    pass

class NomDeScrutinError(Exception) :
    pass

class DonneesVideError(Exception) :
    pass

class DonneesMembreVideError(Exception) :

    def __init__(self,message,legislature,date,numero,nomscru,groupe,vote,prenom,nom):
        self.mess = message
        self.mess +=" legi="+str(legislature)+", date="+str(date)+", num="+str(numero)+", nom="+str(nomscru)+", groupe="+str(groupe)+", vote="+str(vote)+", prenom="+str(prenom)+", nom="+str(nom)
    
    def __str__(self):
        return self.mess

class CalculNombreVotantError(Exception) :
    pass

class DonneeChangeeAnormalementError(Exception) :
    pass

class TotalVotantDifferentError(Exception) :
    pass

## retourne une string contenant l'info du fichier.
################################################################################################
def info_fichier() :
    global current_legislature
    global current_date
    global current_num_scrutin
    global current_nom_scrutin
    global current_groupe_politique
    global current_vote
    global current_legislature
    global current_nb_votant
    global name_file

    return str(name_file)#+", "+str(current_groupe_politique)

#reçois : tableau de string découpé ["MM","Prenom","Nom1", "Nom2", ...]
#supprime les MM, Mme, Mmes, M
#retourne : un nouveau tableau de 2 element ["prenom","Nom1 Nom2 Nom3"]
################################################################################################
def nettoie_membre(membre) : ## throw MembreQueUnNomError
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
        raise MembreQueUnNomError("Membre nul trouvé dans "+current_groupe_politique+" - "+current_vote)
    if taille == 1 :
        raise MembreQueUnNomError("Membre "+membre[0]+" n'a qu'un seul nom/prenom")

    return [membre[0]," ".join(membre[1:])];



#reçois : tableau de string découpé ["MM Prenom Nom","Prenom Nom Nom1", "...", ...]
#découpe chaque "membre", supprime les points, puis appelle nettoie_membre.
#retourne : un nouveau tableau de membre "nettoyés" [["Prenom1","Nom1"],["Prenom2","Nom2"],[...],...]
################################################################################################
def parcours_membres(liste_membres, nbr) :  ## throw CalculNombreVotantError, DonneesMembreVideError
    taille = len(liste_membres)


    if(taille != nbr and nbr != 0) :

        for membre in range(taille) :
            print(liste_membres[membre])

        raise CalculNombreVotantError("Le nombre de votant ne correspond pas: "+str(taille)+" -- Attendu: "+str(nbr)+" !")


    # boucle d'enregistrement!
    for membre in range(taille) :
        liste_membres[membre] =  liste_membres[membre].replace(".","")
        liste_membres[membre] = re.sub('\(.*?\)', '', liste_membres[membre])
        liste_membres[membre] = liste_membres[membre].split()
        
        try :
            liste_membres[membre] = nettoie_membre(liste_membres[membre])
        except MembreQueUnNomError as e :
            logger.error("THROW ERROR : "+str(e))
            logger.error("----"+info_fichier())

        if(current_legislature == None or current_date == None or current_num_scrutin == None or current_nom_scrutin == None or current_groupe_politique == None or current_vote == None or liste_membres[membre][1] == None or liste_membres[membre][0] == None) :
            raise DonneesMembreVideError("Donnee vide Error", current_legislature, current_date, current_num_scrutin, current_nom_scrutin, current_groupe_politique, current_vote, liste_membres[membre][1], liste_membres[membre][0])

        #ecrit dans le fichier.
        if(enregistrement == "1") :
            spamwriter.writerow([str(current_legislature), current_date, current_num_scrutin, current_nom_scrutin,current_groupe_politique, liste_membres[membre][1], liste_membres[membre][0], current_vote]);
    return liste_membres



################################################################################################
def parcours_membres_anonymes(nbr) :
   
    # boucle d'enregistrement!
    for membre in range(nbr) :
        if(current_legislature == None or current_date == None or current_num_scrutin == None or current_nom_scrutin == None or current_groupe_politique == None or current_vote == None) :
            raise DonneesMembreVideError("Donnee vide Error", current_legislature, current_date, current_num_scrutin, current_nom_scrutin, current_groupe_politique, current_vote,"Anonyme","Anonyme")

        #ecrit dans le fichier.
        if(enregistrement == "1") :
            spamwriter.writerow([str(current_legislature), current_date, current_num_scrutin, current_nom_scrutin,current_groupe_politique,"Anonyme","Anonyme", current_vote]); 


################################################################################################
def parcours_paragraphe_membre(paragraphe_texte, nbr) : ## throw CalculNombreVotantError, DonneesMembreVideError

    if(re.match("\s*membres? du groupe, présents? ou ayant délégué (leur|son) droit de vote\.\s*",paragraphe_texte)) :
        parcours_membres_anonymes(nbr)
    else :   
        liste_membres = paragraphe_texte.split(",");
        if(liste_membres[-1].find(" et ") != -1) :
            avant_dernier,dernier = liste_membres[-1].split(" et ")
            liste_membres[-1] = avant_dernier
            liste_membres.append(dernier)
        liste_membres = parcours_membres(liste_membres, nbr)


################################################################################################
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
    current_nb_votant = None


################################################################################################
def reset_currents_groupe_vote() :
    global current_groupe_politique
    global current_vote

    current_groupe_politique = None
    current_vote = None


################################################################################################
################################################################################################
def cherche_date(texte) :
    global current_date

    re_groupe_date = re.match('.*(séance du)[\s\:]*(()[0-9]{1,2}(er)? [0-9A-Za-zéû]* (19|20)\d\d|[0-9]{1,2}\/[0-9]{1,2}\/(19|20)\d\d)',texte, re.DOTALL)
    if (re_groupe_date) :
        if(current_date != None) :
            raise DonneeChangeeAnormalementError("Date déjà présente!") 
        current_date = re_groupe_date.group(2)
        print("DATE DU SCRUTIN = "+current_date)

    else :
        logger.error("-- regex date pas réussi : "+texte)
        
####################
def cherche_num_scrutin(texte) :
    global current_num_scrutin

    re_groupe_num_scrutin = re.match('\s*(analyse du scrutin) n° ([0-9]+)',texte, re.DOTALL)
    if (re_groupe_num_scrutin) :
        if(current_num_scrutin != None) :
            raise DonneeChangeeAnormalementError("Numéro de scrutin déjà présent!")
        current_num_scrutin = str(re_groupe_num_scrutin.group(2))

        print("NUMERO DE SCRUTIN = "+current_num_scrutin)
    else :
        logger.error("-- regex num pas réussi : "+texte)
        
####################
def cherche_nb_votant(texte) :
    global current_nb_votant

    re_groupe_nb_votant = re.match(".*nombre de votants\s*:?\s*([0-9]*).*",texte, re.DOTALL)
    if (re_groupe_nb_votant) :
        if(current_nb_votant != None) :
            raise DonneeChangeeAnormalementError("Nbr de votant déjà présent!")
        current_nb_votant = int(re_groupe_nb_votant.group(1))

        print("CURRENT NB VOTANTS = "+str(current_nb_votant))


####################
def verifie_donnees_correctes() :
    global current_date
    global current_num_scrutin
    global current_nom_scrutin
    global current_legislature
    global current_nb_votant

    if(current_date == None or current_num_scrutin == None or current_nom_scrutin == None or current_legislature == 0 or current_legislature == None or current_nb_votant == None) :
        raise DonneesVideError("Donnees par remplie à temps : legislature= "+str(current_legislature)+", date = "+str(current_date)+", num="+str(current_num_scrutin)+", nom="+str(current_nom_scrutin)+", nombre_votant="+str(current_nb_votant))
################################################################################################
################################################################################################




################################################################################################
def parcours_scrutin_html(url) :  ## throw DonneeChangeeAnormalementError, NomDeScrutinError, TotalVotantDifferentError

    global current_date
    global current_num_scrutin
    global current_nom_scrutin
    global current_groupe_politique
    global current_vote
    global current_nb_votant
    global logger

    print(" ########################### PARCOURS DE "+url+" ###########################") 

    total_votant = 0;


    #tente d'ouvrir en utf-8. Sinon en iso 8859.
    try :
        html = open(url).read()
    except :
        html = open(url, encoding = "ISO-8859-1").read()


    
    #supprime les retour à la ligne et les espace nombreux
    html = html.replace('\n',' ')
    html = html.replace('\r',' ')
    html = ' '.join(html.split())

    soup = BeautifulSoup.BeautifulSoup(html)


    #entete (date et num)
    if len(soup.find_all("p",{"class":"entetegeneraliste"})) != 1 :
        raise Exception("Nombre de paragraphe 'titre' different de 1")
    
    cherche_num_scrutin(soup.find_all("p",{"class":"entetegeneraliste"})[0].text.lower())  
    cherche_date(soup.find_all("p",{"class":"entetegeneraliste"})[0].text.lower())
    

    #Titre (nom du scrutin)
    if len(soup.find_all("p",{"class":"titre"})) != 1 :
        raise Exception("Nombre de paragraphe 'titre' different de 1")

    current_nom_scrutin = soup.find_all("p",{"class":"titre"})[0].text;

    re_groupe_nom_scrutin = re.match("scrutin\s*public\s*sur(.*)",current_nom_scrutin, re.IGNORECASE) #elimination du "scrutin public sur"
    if (re_groupe_nom_scrutin) :
        current_nom_scrutin = re_groupe_nom_scrutin.group(1)

            
    #nombre de votant
    repartitionvotes = soup.find_all("p",{"class":"repartitionvotes"})
    nb_repartitionvotes = len(repartitionvotes)
    for rv in range(nb_repartitionvotes) :
        cherche_nb_votant(repartitionvotes[rv].text.lower())


    #Parcour des "<p>"
    #Normalement, chaque groupe de votant est précédé de son vote (pour/contre..) et de son parti.
    paragraphes = soup.find_all("div",{"id":"analyse"})[0].find_all("p")
    nb_paragraphe = len(paragraphes)
    for p in range(nb_paragraphe) :


        re_groupe_parti = re.match('\s*(GROUPE)[\s\:]*(([^\s\(\)]+\s)*)(.*)', paragraphes[p].text.upper(), re.DOTALL)
        re_groupe_no_parti = re.match('\s*(DEPUTES\s*NON\s*INSCRITS)\s*(\(.*)', paragraphes[p].text.replace("É","E").replace("-"," ").upper(), re.DOTALL)
        re_groupe_vote = re.match('\s*(POUR|CONTRE|NON-VOTANT\s*\(?\s*S?\s*\)?|ABSTENTION)\s*[:\.]*\s*([0-9]*)\s*(.*)', paragraphes[p].text.upper(), re.IGNORECASE)
 

        if(re_groupe_parti) :
            verifie_donnees_correctes()
            reset_currents_groupe_vote()
            current_groupe_politique = re_groupe_parti.group(2)
            print("--"+re_groupe_parti.group(2)+"--"+str(re_groupe_parti.group(4)))
            if paragraphes[p]['class'][0] != "nomgroupe" :
                raise Exception("nomgroupe pas bonne class"+current_groupe_politique)

        if(re_groupe_no_parti) :
            verifie_donnees_correctes()
            reset_currents_groupe_vote()
            current_groupe_politique = re_groupe_no_parti.group(1)
            print("--"+re_groupe_no_parti.group(1)+"--"+str(re_groupe_no_parti.group(2)))
            if paragraphes[p]['class'][0] != "nomgroupe" :
                raise Exception("nomgroupe pas bonne class"+current_groupe_politique)

        nbr = 0
        if(re_groupe_vote) :
            verifie_donnees_correctes()
            current_vote = re_groupe_vote.group(1)
            print(re_groupe_vote.group(1))
            print("Nombre = "+str(re_groupe_vote.group(2))) 
            if paragraphes[p]['class'][0] != "typevote" :
                raise Exception("typevote pas bonne classe"+current_vote)



            if(re.match('NON-VOTANT\s*\(?\s*S?\s*\)?',re_groupe_vote.group(1), re.IGNORECASE)) :
                current_vote = "NON-VOTANT(S)"  ##pour uniformiser les non-votant non-votants etc..
                nbr = 0
            else :
                try :
                    nbr = int(re_groupe_vote.group(2))
                except :
                    logger.error("THROW ERROR : PROBLEME NOMBRE VOTANT SUR ''"+current_groupe_politique+" -- "+re_groupe_vote.group(1)+"'' DANS LE FICHIER "+url)
                    logger.error("----"+info_fichier())

            total_votant += nbr


            if paragraphes[p+1]['class'][0] != "noms" :
                raise Exception("noms pas bonne classe"+current_vote)
            try :
                """if(re_groupe_vote.group(3) != "") :
                    parcours_paragraphe_membre(re_groupe_vote.group(3), nbr)
                else :   """
                parcours_paragraphe_membre(paragraphes[p+1].text, nbr)
            except Exception as e :
                logger.error("THROW ERROR : "+str(e))
                logger.error("----"+info_fichier())

                
            """#peut etre effectué que sur le p+1 (je pense) et comparer avec "noms"
            try :
                if(re_groupe_vote.group(3) != "") : # quelque chose dans le paragraphe. sans doute la liste des membres.
                    parcours_paragraphe_membre(re_groupe_vote.group(3), nbr)
                else :   
                    parcours_paragraphe_membre(paragraphes[p+1].text, nbr)
            except Exception as e :
                logger.error("THROW ERROR : "+str(e))
                logger.error("----"+info_fichier())"""

    
    if(current_nb_votant != total_votant) :
        if(current_nb_votant != None) :
            raise TotalVotantDifferentError("Nombre : "+str(total_votant)+", Attendu : "+str(current_nb_votant))
        logger.error("Nombre de votant TOTAL incohérent "+current_nb_votant+"/"+total_votant+"pour fichier "+url)
    

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
current_legislature = 0
current_nb_votant = None
name_file = None


current_legislature = sys.argv[1]
enregistrement = sys.argv[2]


logging
logger = logging.getLogger('myapp')
hdlr = logging.FileHandler('./logs/'+current_legislature+'.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.WARNING)


nom_fichier = 'votes'+current_legislature+'.csv'
fichier = open(nom_fichier, 'a', newline='')
spamwriter = csv.writer(fichier, delimiter=',')
#spamwriter = csv.writer(fichier, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)



lst_scrutins_html = glob.glob('./scrutins'+current_legislature+'/*.html')    #On liste uniquement les fichiers '.html'
lst_scrutins_html.sort()
print(lst_scrutins_html)


for s in range(len(lst_scrutins_html)) :
    name_file = lst_scrutins_html[s];
    try :
        parcours_scrutin_html(lst_scrutins_html[s])
    except Exception as e :
        logger.error("THROW ERROR GRAVE parcours_scrutin_html : "+str(e))
        logger.error("----"+info_fichier())
    reset_currents_all()

    #fichier.close()
    #fichier = open(nom_fichier, 'a', newline='')
    #spamwriter = csv.writer(fichier, delimiter=',')

fichier.close()



