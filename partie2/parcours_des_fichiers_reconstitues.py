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
                    #if(current_vote and not new_vote) :
                        #print("lit nom page =  "+str(i)+", y = "+str(y))

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
        if (cherche_mot_cle_pour(lignes[i])[0] or cherche_mot_cle_contre(lignes[i])[0]
        or cherche_mot_cle_abstenu(lignes[i])[0] or cherche_mot_cle_pas_pris_part(lignes[i])[0]
        or cherche_mot_cle_absent(lignes[i])[0] or cherche_mot_cle_delegue(lignes[i])[0]):
            return True
        
    return False


####################################################
###################### VOTES #######################
####################################################
def cherche_vote(text) :
    global current_vote
    plus_proche_mot_cle = None
    
    retour = cherche_mot_cle_pour(text)
    if(retour[0][0]) :
        if(not plus_proche_mot_cle or plus_proche_mot_cle[0][1] > retour[0][1]) :
            plus_proche_mot_cle = retour
            
    retour = cherche_mot_cle_contre(text)
    if(retour[0][0]) :
        if(not plus_proche_mot_cle or plus_proche_mot_cle[0][1] > retour[0][1]) :
            plus_proche_mot_cle = retour
            
    retour = cherche_mot_cle_abstenu(text)
    if(retour[0][0]) :
        if(not plus_proche_mot_cle or plus_proche_mot_cle[0][1] > retour[0][1]) :
            plus_proche_mot_cle = retour
            
    retour = cherche_mot_cle_pas_pris_part(text)
    if(retour[0][0]) :
        if(not plus_proche_mot_cle or plus_proche_mot_cle[0][1] > retour[0][1]) :
            plus_proche_mot_cle = retour
            
    retour = cherche_mot_cle_absent(text)
    if(retour[0][0]) :
        if(not plus_proche_mot_cle or plus_proche_mot_cle[0][1] > retour[0][1]) :
            plus_proche_mot_cle = retour
            
    retour = cherche_mot_cle_delegue(text)
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
def cherche_mot_cle_pour(text):
    mot_cherche = "Ont voté pour (1) :"
    mot_cle_pour = "POUR"
    return (valide_mot_cle(mot_cherche,text),mot_cle_pour)

def cherche_mot_cle_contre(text):
    mot_cherche = "Ont voté contre (1) :"
    mot_cle_contre = "CONTRE"
    return (valide_mot_cle(mot_cherche,text), mot_cle_contre)

def cherche_mot_cle_abstenu(text):
    mot_cherche = "Se sont abstenus volontairement (1) :"
    mot_cle_abstenu = "ABSTENU"
    return (valide_mot_cle(mot_cherche,text), mot_cle_abstenu)

def cherche_mot_cle_pas_pris_part(text):
    mot_cherche = "N'ont pas pris part au vote :"
    mot_cle_pas_pris_part = "PAS PRIS PART"
    return (valide_mot_cle(mot_cherche,text), mot_cle_pas_pris_part)

def cherche_mot_cle_absent(text):
    mot_cherche = "Excusés ou absents par congé (2) :"
    mot_cle_absent = "ABSENT"
    return (valide_mot_cle(mot_cherche,text), mot_cle_absent)

def cherche_mot_cle_delegue(text):
    mot_cherche = "Ont délégué leur droit de vote :"
    mot_cle_delegue = "DELEGUE"
    return (valide_mot_cle(mot_cherche,text), mot_cle_delegue)



def add_infos_page(num,milieu,sixcol):
    global dico_infos_pages
    dico_infos_pages[num] = InfosDePage(num,milieu,sixcol)
    #dico_infos_pages[num] = (milieu,sixcol)


#cherche la colonne vide la plus à gauche de x. (souvent x en fait :-/)
#SUPPOSITION : on suppose que l'espace au milieu est composé d'au moins 1 blanc. On commence donc à x-1
# ça permet parfois d'eviter un problème si la 4em colonne comporte des mots décalé d'une ou deux cases à gauche.
def chercher_milieu_de_page(text_page,x):
    vide = True
    lignes = text_page.split('\n');
    x=x-1 #supposition
    while( vide == True) :
        for y in range(0,len(lignes)) :
            if(len(lignes[y]) > x):
                if not lignes[y][x-1].isspace():
                    vide = False
        x = x-1
    return x+1

def cherche_six_colonnes_page(numpage,text_page):
    global helper
    dico_de_coord = {}

    ecart_entre_six_et_sept_minimum = 10 #au moins X de + dans la 6em que 7em (utile pour les petites page)
    difference_entre_six_et_sept = 2.5 #sixieme colonne > diff*7emcolonne. (pour 3, 6>7*3)
    print("Cherche six colonnes pour page ="+str(numpage))
    
    text_page = nettoie_page(text_page);
    lignes = text_page.split('\n');
    for y in range(0,len(lignes)) :
        for x in range(0,len(lignes[y])-1) :
            if( lignes[y][x+1] != " " and lignes[y][x] == " ") :
                if x+1 in dico_de_coord:
                    dico_de_coord[x+1] += 1
                else:
                    dico_de_coord[x+1] = 1


    coords_triees = sorted(dico_de_coord.items(),key=itemgetter(1),reverse=True)

    if(len(coords_triees) < 6) :
        raise SixColonnePasDistinctesError(filename+" page "+str(numpage))

        
    for i in range (0,len(coords_triees)) : #repasse les tuple en array (pour etre modifie)
        coords_triees[i] = list(coords_triees[i])
    
        
    # parcourir les coords_triees. et pour la 1, la 2, la 3...6, fusionner les voisines
    # ex, si la 1 est x = 94. et que dans la liste on a du x=93/95,
    # on additionne tout dans x=95 et supprime les autres.
    for i in range (0,6) :
        decalage = 0
        for j in range (0,len(coords_triees)) :
            if(coords_triees[j-decalage][0] == coords_triees[i][0]-1 or
               coords_triees[j-decalage][0] == coords_triees[i][0]+1) :
                coords_triees[i][1] += coords_triees[j-decalage][1]
                del coords_triees[j-decalage]
                decalage +=1

    coords_triees = sorted(coords_triees,key=itemgetter(1),reverse=True)

    #debug perso parceque j'sais pas utiliser un debuggeur
    if(numpage == 44) :
        helper.append(copy.deepcopy(coords_triees))

        
    #verifie qu'il y a bien 6 distinct. On propose la 7em colonne doit etre au moins
    #deux 1.5 plus faible que la 6em.
    if(coords_triees[5][1] <= difference_entre_six_et_sept * coords_triees[6][1] or coords_triees[5][1] <= ecart_entre_six_et_sept_minimum+coords_triees[6][1]) :
        raise SixColonnePasDistinctesError(filename+" page "+str(numpage))


    sixcolonnes = [coords_triees[0][0],coords_triees[1][0],coords_triees[2][0],coords_triees[3][0],coords_triees[4][0],coords_triees[5][0]]
    sixcolonnes.sort()

    logger_info.info("SIX COLONNES TROUVEES: ")
    logger_info.info(coords_triees)

    milieu = chercher_milieu_de_page(text_page,sixcolonnes[3])
    add_infos_page(numpage,milieu,sixcolonnes)




"""
##recupere la longueur de la ligne la plus longue.
##divise par 2, et cherche la colonne vide la plus proche (à gauche ou à droite).
## ici le "vide" est pas évident à determiner.
## approche totalement à taton et random:
## essai avec vide = 0 caractere.
## on va conciderer que si ça depasse les 20% d'écart c'est inquiétant et on ne prend pas
## ex: si une page fait 200carac max, alors on cherche le milieu entre 80 et 120
## si on ne trouve pas, on tente avec vide = 1. et ainsi de suite jusqu'à en trouver une.
"""
def cherche_colonne_centrale_vide(numpage,text_page):
    global helper
    marge_erreur = 0.2 #droit à cette marge autour du centre.
    marge_bas_haut_de_page = 0.2 #correspond aux pourcentages reprsentant le haut ou pas. (0.2 = haut 20% de page, bas à partir de 80%)
    nombre_de_caractere_dans_centre_max = 8 #en estimant les petites phrases en debut/fin
    y_max = 0
    trouve = False
    #print(text_page)
    
    text_page = nettoie_page(text_page);
    lignes = text_page.split('\n');

    #cherche la ligne la plus longue
    for y in range(0,len(lignes)) :
        if( len(lignes[y]) > y_max) :
            y_max = len(lignes[y])



    difference_centrale = 0 #cherche à partir de la colonne centrale.
    nombre_de_caractere_autorise = 0
    milieu = int(y_max/2)
    print("milieu theorique = "+str(milieu))
    while(not trouve) :

        #colonne droite
        colonne_blanche = True
        compteur = nombre_de_caractere_autorise
        for y in range(0,len(lignes)) : #parcours la page
            if(len(lignes[y]) > milieu+difference_centrale) : #verifie si la ligne s'arrete pas avant
                
                if(not lignes[y][milieu+difference_centrale].isspace()) :
                    if(compteur == 0 or ( y > len(lignes)*marge_bas_haut_de_page and y < len(lignes)-(len(lignes)*marge_bas_haut_de_page))) : #trop de caractere comptee. Ou caractere trouvé au milieu de page
                        colonne_blanche = False
                        break
                    print(str(lignes[y][milieu+difference_centrale]))
                    compteur-= 1

                    
        #TROUVE            
        if(colonne_blanche) :
            logger_info.info("COLONNE BLANCHE TROUVEE A DROITE: ")
            logger_info.info("milieu ="+str(milieu+difference_centrale));
            logger_info.info("nbr caractere dans colonne blanche ="+str(nombre_de_caractere_autorise))
            add_infos_page(numpage,milieu+difference_centrale,[])
            return milieu+difference_centrale


        #colonne gauche
        colonne_blanche = True
        compteur = nombre_de_caractere_autorise
        for y in range(0,len(lignes)) :
            if(len(lignes[y]) > milieu-difference_centrale) :
                if(not lignes[y][milieu-difference_centrale].isspace()) :
                    if(compteur == 0 or ( y > len(lignes)*marge_bas_haut_de_page and y < len(lignes)-(len(lignes)*marge_bas_haut_de_page))) :
                        colonne_blanche = False
                        break
                    compteur-= 1

        #TROUVE         
        if(colonne_blanche) :
            logger_info.info("COLONNE BLANCHE TROUVEE A GAUCHE: ")
            logger_info.info("milieu ="+str(milieu-difference_centrale));
            logger_info.info("nbr caractere dans colonne blanche ="+str(nombre_de_caractere_autorise))
            
            add_infos_page(numpage,milieu-difference_centrale,[])
            return milieu-difference_centrale

        difference_centrale+= 1
        #si marge d'erreur atteinte (plus de 20% eloigne du "milieu theorique"
        if(difference_centrale > milieu*marge_erreur):
            difference_centrale = 0
            nombre_de_caractere_autorise+= 1

            if(nombre_de_caractere_autorise > nombre_de_caractere_dans_centre_max) :
                raise ImpossibleDeTrouverColonneCentraleError(filename+" page "+str(numpage))



def reconstitue_page(i,text_page) :
    global pages_reconstituees
    milieu = dico_infos_pages[i].get_milieu()
    text = ""

    text_page = supprime_premiere_ligne_ecrite(text_page);
    lignes = text_page.split('\n');
    #print(text_page)
    print("milieu = "+str(milieu));
    #partie gauche
    for y in range(0,len(lignes)) :
        fin_tmp = min(milieu,len(lignes[y]))
        text += lignes[y][0:fin_tmp]+"\n";
    text += "\x0c";
    text += "\n";
    
    #partie droite
    for y in range(0,len(lignes)) :
        fin = len(lignes[y])
        if(milieu < fin):
            text += lignes[y][milieu:fin]+"\n";

    text += "\x0c";

    pages_reconstituees += text


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

