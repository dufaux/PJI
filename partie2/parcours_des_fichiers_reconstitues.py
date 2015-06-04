import locale # module pour gerer les locales (latin1, utf8 etc...)
import sys    # module pour gérer le système
import os
locale.getpreferredencoding = lambda: 'UTF-8'

from urllib.request import urlopen
import bs4 as BeautifulSoup
import re
import csv
import glob
import logging
from operator import itemgetter
from Levenshtein import distance

import copy

####################################################
#################### EXCEPTIONS ####################
####################################################
class PasDePageScrutinTrouvee(Exception) :
    pass

class SixColonnePasDistinctesError(Exception) :
    pass

class ImpossibleDeTrouverColonneCentraleError(Exception) :
    pass


####################################################
###################### OBJETS ######################
####################################################

class InfosDePage:

    def __init__(self,p_numero,p_milieu,p_colonnes):
        self.numero = p_numero
        self.milieu = p_milieu
        self.colonnes = p_colonnes

    def get_numero(self) :
        return self.numero

    def get_milieu(self) :
        return self.milieu

    def get_colonnes(self) :
        return self.colonnes



####################################################
#################### FONCTIONS #####################
####################################################
def nettoie_page(text_page) :
    #tentative retirer les points. (remplace par espace). pourquoi?!
    #return text_page.replace('.',' ');
    return text_page

def supprime_premiere_ligne_ecrite(text_page) :
    lignes = text_page.split('\n')
    supprime = False
    i = 0
    while(not supprime and i < len(lignes)):
        if(not lignes[i] or lignes[i].isspace()):
            i=i+1
        else:
            del lignes[i]
            break
    return '\n'.join(lignes)

def parcours_fichier(fichier) :
    global logger
    global filename

    fichier = fichier.replace('\r','');
    fichier = fichier.replace('\t',' '); #replace tab par un espace!
    pages = fichier.split("\x0c");
    
    """debut = None
    for i in range(0,len(pages)) : #recherche de la premiere page comprenant un scrutin
        if page_comprend_scrutin(pages[i]):
            debut = i
            break

    if (debut == None):
        raise PasDePageScrutinTrouvee(filename)"""

    #parcours page par page
    for i in range(0,len(pages)) :
        if(pages[i]) :
            lignes = pages[i].split('\n');
            #parcours ligne par ligne
            for y in range(0,len(lignes)) :
                if(lignes[y]) :
                    cherche_infos_globales(lignes[y])
                    #last_current_vote = current_vote pareil que new_vote
                    new_vote = cherche_vote(lignes[y])
                    
                    if(new_vote) :
                        print("Nouveau vote page =  "+str(i)+", y = "+str(y)+"et vote = "+str(current_vote))

                    #si on a un vote courant et pas de new vote alors c'est un nom.
                    if(current_vote and not new_vote) :
                        print("lit nom page =  "+str(i)+", y = "+str(y))

##
## A rajouter: chercher aussi les mots "nombres de votants" etc
## interrogation : trouver la fin du fichier/scrutin. dur à ne pas prendre en compte
## les textes "intrus". 
##
##

#A COMPLETER POUR NUMERO, nbr de votants, etc...(date? impossible imho)
def cherche_infos_globales(ligne) :
    if("SCRUTIN" in ligne) :
        changement_de_scrutin()

##a completer pour réinitialiser les variables. verifier le scrutin precedent etc.
def changement_de_scrutin() :
    pass




def contient_mot_cle(text_page):
    lignes = text_page.split('\n');

    #Peut-etre inutile de faire sur chaque ligne faire sur le text direct?
    for i in range(0,len(lignes)) :
        if (mot_cle_pour(lignes[i])[0] or mot_cle_contre(lignes[i])[0]
        or mot_cle_abstenu(lignes[i])[0] or mot_cle_pas_pris_part(lignes[i])[0]
        or mot_cle_absent(lignes[i])[0] or mot_cle_delegue(lignes[i])[0]):
            return True
        
    return False


####################################################
###################### VOTES #######################
####################################################
def cherche_vote(text) :
    global current_vote
    plus_proche_mot_cle = None
    
    retour = mot_cle_pour(text)
    if(retour[0][0]) :
        if(not plus_proche_mot_cle or plus_proche_mot_cle[0][1] > retour[0][1]) :
            plus_proche_mot_cle = retour
            
    retour = mot_cle_contre(text)
    if(retour[0][0]) :
        if(not plus_proche_mot_cle or plus_proche_mot_cle[0][1] > retour[0][1]) :
            plus_proche_mot_cle = retour
            
    retour = mot_cle_abstenu(text)
    if(retour[0][0]) :
        if(not plus_proche_mot_cle or plus_proche_mot_cle[0][1] > retour[0][1]) :
            plus_proche_mot_cle = retour
            
    retour = mot_cle_pas_pris_part(text)
    if(retour[0][0]) :
        if(not plus_proche_mot_cle or plus_proche_mot_cle[0][1] > retour[0][1]) :
            plus_proche_mot_cle = retour
            
    retour = mot_cle_absent(text)
    if(retour[0][0]) :
        if(not plus_proche_mot_cle or plus_proche_mot_cle[0][1] > retour[0][1]) :
            plus_proche_mot_cle = retour
            
    retour = mot_cle_delegue(text)
    if(retour[0][0]) :
        if(not plus_proche_mot_cle or plus_proche_mot_cle[0][1] > retour[0][1]) :
            plus_proche_mot_cle = retour

    ##si on en a trouvé un
    if(plus_proche_mot_cle) :
        current_vote = plus_proche_mot_cle[1]
        return True




def nettoie_mot_cle_a_chercher(text):
    return " ".join(text.split()) #remove multiple space

#Return tuple of bool,dist
# return : (Boolean,Int)
def valide_mot_cle(mot_cle,text) :
    marge_erreur = 0.3 #pourcentage d'erreur autorisé (distance leven < len*marge)
    text = nettoie_mot_cle_a_chercher(text)
    dist_max = max(len(mot_cle),len(text))
    dist = distance(mot_cle,text)
    if(dist < dist_max*marge_erreur) :
        return (True,dist)
    return (False,dist)

#Return tuple of tuple and string
# return : ((Boolean,Int),String)
def mot_cle_pour(text):
    mot_cherche = "Ont voté pour (1) :"
    mot_cle_pour = "POUR"
    return (valide_mot_cle(mot_cherche,text),mot_cle_pour)

def mot_cle_contre(text):
    mot_cherche = "Ont voté contre (1) :"
    mot_cle_contre = "CONTRE"
    return (valide_mot_cle(mot_cherche,text), mot_cle_contre)

def mot_cle_abstenu(text):
    mot_cherche = "Se sont abstenus volontairement (1) :"
    mot_cle_abstenu = "ABSTENU"
    return (valide_mot_cle(mot_cherche,text), mot_cle_abstenu)

def mot_cle_pas_pris_part(text):
    mot_cherche = "N'ont pas pris part au vote :"
    mot_cle_pas_pris_part = "PAS PRIS PART"
    return (valide_mot_cle(mot_cherche,text), mot_cle_pas_pris_part)

def mot_cle_absent(text):
    mot_cherche = "Excusés ou absents par congé (2) :"
    mot_cle_absent = "ABSENT"
    return (valide_mot_cle(mot_cherche,text), mot_cle_absent)

def mot_cle_delegue(text):
    mot_cherche = "Ont délégué leur droit de vote :"
    mot_cle_delegue = "DELEGUE"
    return (valide_mot_cle(mot_cherche,text), mot_cle_delegue)



def add_infos_page(num,milieu,sixcol):
    global dico_infos_pages
    dico_infos_pages[num] = InfosDePage(num,milieu,sixcol)
    #dico_infos_pages[num] = (milieu,sixcol)



def reinitialise_variables() :
    global current_num_scrutin
    global current_nom_scrutin
    global current_vote
    global current_nb_votant
    global filename
    global infos_page
    global pages_reconstituees
    global dico_infos_pages
    global helper

    current_legislature = None
    current_num_scrutin = None
    current_nom_scrutin = None
    current_vote = None
    current_nb_votant = None
    filename = None
    infos_page = None
    pages_reconstituees = ""
    dico_infos_pages = {}
    helper = []


#######################################################################
###############__######__#######__#######__####___####__###############
###############___####___#####______###########____###__###############
###############____##____####___##___####__####__#__##__###############
###############__#____#__####________####__####__##__#__###############
###############__######__####__####__####__####__###____###############
###############__######__####__####__####__####__####___###############
#######################################################################


current_legislature = None
current_num_scrutin = None
current_nom_scrutin = None
current_vote = None
current_nb_votant = None
filename = None

infos_page = None
pages_reconstituees = ""
dico_infos_pages = {}
helper = []

current_legislature = "4"
#logs
logging
logger = logging.getLogger('myapp')
hdlr = logging.FileHandler('./logs/'+current_legislature+'_reconstitues.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.ERROR)


logger_info = logging.getLogger('main')
hdlr2 = logging.FileHandler('./logs/'+current_legislature+'_reconstitues_info.log')
formatter2 = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr2.setFormatter(formatter2)
logger_info.addHandler(hdlr2) 
logger_info.setLevel(logging.DEBUG)

"""
for root, subdirs, files in os.walk("4-reconstitues"):

    for nomfichier in files :
        filepath = root+"/"+nomfichier
        print("Fichier lu: "+filepath)
        
        fichierlayout = open(filepath).read()
        
        filename = nomfichier
        try :
            parcours_fichier(fichierlayout)
            
            dest = "legislature4.csv"
            fichiertxt = open(dest,"w") # a pour ecrire à la fin, w pour remplacer
            fichiertxt.write(pages_reconstituees)
            fichiertxt.close()
            print("Fichier cree: "+dest)
        
        except PasDePageScrutinTrouvee as e :
            logger.error("["+str(filepath)+"]EXCEPT: PasDePageScrutinTrouvee ")
        except ImpossibleDeTrouverColonneCentraleError :
            logger.error("["+str(filepath)+"]EXCEPT: ImpossibleDeTrouverColonneCentraleError ")


        reinitialise_variables()
        logger_info.info("\n\n\n")
"""

filename = "007.txt";
fichier = open(filename).read()

parcours_fichier(fichier)


"""
pagetest = pages[37];
pagetest= pagetest.replace('\n','')
lignes = pagetest.split('\n');
"""

