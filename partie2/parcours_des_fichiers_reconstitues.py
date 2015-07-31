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
import re
import copy

from depute import DeputeIntrouvableError
from depute import Liste_deputes
from depute import Depute_modele
from depute import Depute


####################################################
#################### EXCEPTIONS ####################
####################################################
class TroisColonnePasDistinctesError(Exception) :
    pass

class PasDeScrutinDansLaLigneError(Exception) :
    pass

####################################################
###################### OBJETS ######################
####################################################

class InfosDePage:

    def __init__(self,p_numero,p_colonnes):
        self.numero = p_numero
        self.colonnes = p_colonnes

    def get_numero(self) :
        return self.numero

    def get_colonnes(self) :
        return self.colonnes


class InfoMotCle :

    def __init__(self,param_page,param_ligne,param_mot) :
        self.page = param_page
        self.ligne = param_ligne
        self.mot = param_mot

####################################################
#################### FONCTIONS #####################
####################################################

def redecoupage_nom(nom) :
    mots = nom.split()
    decoupages = trouver_decoupage(len(mots))
    les_phrases = []
    for decoupe in decoupages :
        phrase = []
        for i in range (len(decoupe)-1) :
            phrase.append(" ".join(mots[decoupe[i]:decoupe[i+1]]))
        phrase.append(" ".join(mots[decoupe[len(decoupe)-1]:len(mots)]))
        les_phrases.append(phrase)

    return les_phrases



##en attendant mieux...
liste_de_decoupage = []
def trouver_decoupage(taille) :
    global liste_de_decoupage
    liste_de_decoupage = []
    if(taille > 6) :
        return [list(range(0,taille))]
    decoupage_recursif(0,taille,[])
    return liste_de_decoupage

                          
def decoupage_recursif(debut, fin, array) :
	global liste_de_decoupage
	
	array = array + [debut]
	if not array in liste_de_decoupage :
	    liste_de_decoupage.append(array)
	for i in range (debut+1, fin) :
		#print(array)
		decoupage_recursif(i,fin,array)


def enregistre_depute(nom, prenom, parti) :
    global Liste_de_deputes_a_enregistrer
    depute = Depute(nom,prenom,parti,current_vote)
    Liste_de_deputes_a_enregistrer.append(depute)
    
def nettoie_text(text) :
    text = text.replace("MM.","   ")
    text = text.replace("M.","  ")
    text = text.replace("MM .","    ")
    text = text.replace("M.","  ")
    text = text.replace("Mme ","    ")
    text = text.replace("Mlle ","     ")
    return text
    
def parcours_fichier(fichier) :
    global logger
    global filename
    global current_vote
    
    fichier = fichier.replace('\r','');
    fichier = fichier.replace('\t',' '); #replace tab par un espace!
    pages = fichier.split("\x0c");

    liste_mot_cle = []
    liste_scrutin = []
    
    #parcours page par page
    for i in range(0,len(pages)) :
        if(pages[i]) :

            
            try :
                troiscolonnes = cherche_trois_colonnes_text(i,pages[i],10,2.5)
                add_infos_page(i,troiscolonnes)
            except TroisColonnePasDistinctesError :
                add_infos_page(i,None)
            
            lignes = pages[i].split('\n');
            #parcours ligne par ligne
            for y in range(0,len(lignes)) :
                if(lignes[y]) :
                    try :
                        numero_scrutin = cherche_scrutin(lignes[y])
                        le_scrutin = InfoMotCle(i,y,numero_scrutin)
                        liste_scrutin.append(le_scrutin)
                        
                    except PasDeScrutinDansLaLigneError :
                        pass
                    
                    #last_current_vote = current_vote pareil que new_vote
                    new_vote = cherche_vote(lignes[y])
                    
                    if(new_vote) :
                        mot = InfoMotCle(i,y,current_vote)
                        liste_mot_cle.append(mot)
                        #print("Nouveau vote page =  "+str(i)+", y = "+str(y)+"et vote = "+str(current_vote))

                    #si on a un vote courant et pas de new vote alors c'est un nom.
                    #if(current_vote and not new_vote) :
                        #print("lit nom page =  "+str(i)+", y = "+str(y))

    current_scrutin = 0
    changement_de_scrutin(liste_scrutin[current_scrutin].mot)

    #parcours chaque mot clé
    for i in range(len(liste_mot_cle)-1) :
        logger_grave.error("--- mot clé --- "+str(liste_mot_cle[i].mot))
        #print("Mot clé "+liste_mot_cle[i].mot+" et page = "+str(liste_mot_cle[i].page)+" et ligne = "+str(liste_mot_cle[i].ligne))

        current_vote = liste_mot_cle[i].mot
        current_page = liste_mot_cle[i].page
        current_ligne = liste_mot_cle[i].ligne+1


        #si le mot clé est après un new scrutin, on change de scrutin.        
        if(len(liste_scrutin) > current_scrutin+1) :
            if( (current_page > liste_scrutin[current_scrutin+1].page) or (current_page == liste_scrutin[current_scrutin+1].page and current_ligne >= liste_scrutin[current_scrutin+1].ligne)) :
                current_scrutin += 1
                changement_de_scrutin(liste_scrutin[current_scrutin].mot)
                current_vote = liste_mot_cle[i].mot #comme ça a été remi à zéro



        #defini l'arret de la lecture du paragraphe. (prochain mot clé ou le mot scrutin si avant prochain mot clé)
        stop_page = liste_mot_cle[i+1].page
        stop_ligne = liste_mot_cle[i+1].ligne-1
        if(len(liste_scrutin) > current_scrutin+1) : 
            if( (stop_page > liste_scrutin[current_scrutin+1].page) or (stop_page == liste_scrutin[current_scrutin+1].page and stop_ligne >= liste_scrutin[current_scrutin+1].ligne)) :
                stop_page = liste_scrutin[current_scrutin+1].page
                stop_ligne = liste_scrutin[current_scrutin+1].ligne-1





        print("Traitement du mot clé : "+liste_mot_cle[i].mot)
        while(current_page < stop_page) :
            
            parcours_partie_de_page(current_page,pages[current_page],current_ligne,(len(pages[current_page].split('\n'))-1))
            #print("Traitement d'un paragraphe page "+str(current_page)+" de ligne "+str(current_ligne)+" à "+str(len(pages[current_page].split('\n'))-1))
            current_page += 1
            current_ligne = 0

        parcours_partie_de_page(current_page,pages[current_page],current_ligne,(stop_ligne))
        #print("Traitement d'un paragraphe page "+str(current_page)+" de ligne "+str(current_ligne)+" à "+str(liste_mot_cle[i+1].ligne-1))


    # a utiliser pour les colonnes
    """try :
        dico_infos_pages[i]
    except KeyError as e :
        print("pas de 3 colonnes pour i="+str(e))"""




##
## A rajouter: chercher aussi les mots "nombres de votants" etc
## interrogation : trouver la fin du fichier/scrutin. dur à ne pas prendre en compte
## les textes "intrus". 
##
##

def parcours_partie_de_page(num_page,contenu_page,ligne_debut,ligne_fin) :
    #print("Traitement d'un paragraphe page "+str(num_page)+" de ligne "+str(ligne_debut)+" à "+str(ligne_fin))
    lignes = contenu_page.split('\n')
    text = "\n".join(lignes[ligne_debut:ligne_fin+1])
    parcours_paragraphe_membre(num_page, text)

def parcours_paragraphe_membre(num_page, text) :
    text = nettoie_text(text)

    """print("TEXTTTTTTTTTTTTTTTTTTTTTTTTTTT")
    print(text)"""
    troiscolonnes = None
    
    try :
        troiscolonnes = cherche_trois_colonnes_text(num_page,text,0,1.9)

        #print("TROIS COLONNES")
        #print("----- 0 = "+str(troiscolonnes[0])+" et 1 = "+str(troiscolonnes[1])+" et 2 = "+str(troiscolonnes[2]))
   
        if not(troiscolonnes == dico_infos_pages[num_page].get_colonnes()) :
            ## on a trois colonnes mais pas les même.
            ## log info?
            logger_info.info("["+str(filename)+"]-"+str(num_page)+" trois colonnes differentes")

        col1 = ""
        col2 = ""
        col3 = ""
        lignes = text.split('\n')
        ##on doit de toute manière reconstituer le text en lisant colonnes par colonnes
        for i in range (len(lignes)) :
            col1 = col1+lignes[i][0:troiscolonnes[1]]
            col2 = col2+lignes[i][troiscolonnes[1]:troiscolonnes[2]]
            col3 = col3+lignes[i][troiscolonnes[2]:]

        text = col1+" "+col2+" "+col3



        
    except TroisColonnePasDistinctesError :
        text = text.replace(" et "," . ")
        ##pas trois colonnes
        ##test d'une liste normal? ne rien faire?
        ##eventuellement remplacer un " et " par un " . "?
        pass


    """print(troiscolonnes == dico_infos_pages[num_page].get_colonnes())
    print(text)"""

    liste_deputes = re.split(',|\.',text)
    liste_modeles = Liste_deputes() #peut etre passé en globale fixe
    liste_modeles.init_from_file("./4-deputes/liste.txt")

    for i in range(len(liste_deputes)) :
        depute_a_trouver = " ".join(liste_deputes[i].split())
        
        try :
            trouvaille =  liste_modeles.cherche_depute(depute_a_trouver,0.3)
            #print("TROUVE -"+str(trouvaille[0])+" "+depute_a_trouver+" => "+trouvaille[1].nom+"["+trouvaille[1].parti+"]")
            enregistre_depute(trouvaille[1].nom,trouvaille[1].prenom,trouvaille[1].parti)
            
        except DeputeIntrouvableError as e:
            ##replace les eventuels chiffres
            depute_a_trouver = depute_a_trouver.replace("0","o").replace("1","l")
            try :
                trouvaille =  liste_modeles.cherche_depute(depute_a_trouver,0.3)
                #print("TROUVE2 -"+str(trouvaille[0])+" "+depute_a_trouver+" => "+trouvaille[1].nom+"["+trouvaille[1].parti+"]")
                enregistre_depute(trouvaille[1].nom,trouvaille[1].prenom,trouvaille[1].parti)
            except DeputeIntrouvableError as e1:
                #split le nom en toute les possibilités et essayes pour chacune
                #on garde la combinaison où on a le plus de match
                liste_nouveaux_noms = redecoupage_nom(e1.get_nom())
                compteur_max = None
                i_max = None
                compteur = 0
                for i in range(len(liste_nouveaux_noms)) :
                    compteur = 0
                    nouveaux_noms = liste_nouveaux_noms[i]
                    for nom in nouveaux_noms :
                        try :
                            trouvaille =  liste_modeles.cherche_depute(nom,0.3)
                            compteur = compteur +1
                        except DeputeIntrouvableError as e2:
                            #print info ?
                            pass
                    if(not compteur_max or compteur_max < compteur) :
                        compteur_max = compteur
                        i_max = i

                #meilleur trouve
                for bons_noms in liste_nouveaux_noms[i_max] :
                    try :
                        trouvaille =  liste_modeles.cherche_depute(nom,0.3)
                        enregistre_depute(trouvaille[1].nom,trouvaille[1].prenom,trouvaille[1].parti)
                    except DeputeIntrouvableError as e3:
                        logger_grave.error("PAS RECONNU : "+str(e3.get_nom()))
                        #print("NOM PAS PASSE : "+str(e3.get_nom()))
                        pass



def cherche_scrutin(ligne) :
    if("SCRUTIN" in ligne):
        try :
            nombres = re.findall(r'\d+',ligne)
            return nombres[len(nombres)-1]
        except Exception as e:
            return "UNKNOW"
    else :
        raise PasDeScrutinDansLaLigneError()

#A COMPLETER POUR NUMERO, nbr de votants, etc...(date? impossible imho)
def cherche_infos_globales(ligne) :
    if("SCRUTIN" in ligne) :
        changement_de_scrutin(ligne)

##a completer pour réinitialiser les variables. verifier le scrutin precedent etc.
def changement_de_scrutin(numero_scrutin) :
    global current_num_scrutin
    print("changement de scrutin ancien = "+str(current_num_scrutin)+" et nouveau ="+str(numero_scrutin))
    logger_grave.error("--- new scrutin --- "+str(numero_scrutin))
    sauvegarde_liste_deputes()
    reinitialise_variables_de_scrutin()
    current_num_scrutin = numero_scrutin

def contient_mot_cle(text_page):
    lignes = text_page.split('\n');

    #Peut-etre inutile de faire sur chaque ligne faire sur le text direct?
    for i in range(0,len(lignes)) :
        if (cherche_mot_cle_pour(lignes[i])[0][0] or cherche_mot_cle_contre(lignes[i])[0][0]
        or cherche_mot_cle_abstenu(lignes[i])[0][0] or cherche_mot_cle_pas_pris_part(lignes[i])[0][0]
        or cherche_mot_cle_absent(lignes[i])[0][0] or cherche_mot_cle_delegue(lignes[i])[0][0]):
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

    retour = cherche_mot_cle_abstenu_singulier(text)
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

def cherche_mot_cle_abstenu_singulier(text):
    mot_cherche = "S'est abstenu volontairement"
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



def add_infos_page(num,troiscol):
    global dico_infos_pages
    dico_infos_pages[num] = InfosDePage(num,troiscol)


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


def cherche_trois_colonnes_text(numpage,text,ecart,ratio):
    global helper
    dico_de_coord = {}

    ecart_entre_trois_et_quatre_minimum = ecart #au moins X de + dans la 3em que 4em (utile pour les petites page)
    difference_entre_trois_et_quatre = ratio #troisieme colonne > diff*4emcolonne. (pour 3, 3>4*3)
    #print("Cherche trois colonnes pour page ="+str(numpage))
    
    #text = nettoie_page(text);
    lignes = text.split('\n');
    for y in range(0,len(lignes)) :
        for x in range(0,len(lignes[y])-1) :
            if( lignes[y][x+1] != " " and lignes[y][x] == " ") :
                if x+1 in dico_de_coord:
                    dico_de_coord[x+1] += 1
                else:
                    dico_de_coord[x+1] = 1


    coords_triees = sorted(dico_de_coord.items(),key=itemgetter(1),reverse=True)

    if(len(coords_triees) < 3) :
        raise TroisColonnePasDistinctesError(filename+" page "+str(numpage))

        
    for i in range (0,len(coords_triees)) : #repasse les tuple en array (pour etre modifie)
        coords_triees[i] = list(coords_triees[i])
    
        
    # parcourir les coords_triees. et pour la 1, la 2, la 3...6, fusionner les voisines
    # ex, si la 1 est x = 94. et que dans la liste on a du x=93/95,
    # on additionne tout dans x=95 et supprime les autres.
    for i in range (0,3) :
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


    """print("y ="+str(coords_triees[0][0])+" num ="+str(coords_triees[0][1]))
    print("y ="+str(coords_triees[1][0])+" num ="+str(coords_triees[1][1]))
    print("y ="+str(coords_triees[2][0])+" num ="+str(coords_triees[2][1]))
    print("y ="+str(coords_triees[3][0])+" num ="+str(coords_triees[3][1]))"""
    if(len(coords_triees) < 4) :
        raise TroisColonnePasDistinctesError(filename+" page "+str(numpage))

    
    #verifie qu'il y a bien 3 distinct. On propose la 4em colonne doit etre au moins
    #ratio plus faible que la 4em.
    if(coords_triees[2][1] <= difference_entre_trois_et_quatre * coords_triees[3][1] or coords_triees[2][1] <= ecart_entre_trois_et_quatre_minimum+coords_triees[3][1]) :
        raise TroisColonnePasDistinctesError(filename+" page "+str(numpage))


    troiscolonnes = [coords_triees[0][0],coords_triees[1][0],coords_triees[2][0]]
    troiscolonnes.sort()

    logger_info.info("TROIS COLONNES TROUVEES: ")
    logger_info.info(coords_triees)

    return troiscolonnes




def sauvegarde_liste_deputes() :
    global Liste_de_deputes_a_enregistrer
    for i in range (len(Liste_de_deputes_a_enregistrer)) :
        #spamwriter.writerow([str(current_legislature), i]);
        spamwriter.writerow([filepath,str(current_legislature), "Date à ajouter",str(current_num_scrutin), "Nom à ajouter",Liste_de_deputes_a_enregistrer[i].parti, Liste_de_deputes_a_enregistrer[i].nom, Liste_de_deputes_a_enregistrer[i].prenom, Liste_de_deputes_a_enregistrer[i].vote]);
        #print("Enregistrement de "+str(current_legislature)+"-- Date à ajouter --"+str(current_num_scrutin)+"--Nom à ajouter--"+Liste_de_deputes_a_enregistrer[i].parti+"--"+Liste_de_deputes_a_enregistrer[i].nom+"--"+Liste_de_deputes_a_enregistrer[i].prenom+"--"+Liste_de_deputes_a_enregistrer[i].vote)
    print("Enregistrement de "+str(len(Liste_de_deputes_a_enregistrer))+" députés pour le scrutin "+str(current_num_scrutin))

def reinitialise_variables_de_scrutin() :
    global current_num_scrutin
    global current_nom_scrutin
    global current_vote
    global current_nb_votant
    global helper
    global Liste_de_deputes_a_enregistrer

    current_legislature = None
    current_num_scrutin = None
    current_nom_scrutin = None
    current_vote = None
    current_nb_votant = None
    Liste_de_deputes_a_enregistrer = []
    helper = []




def reinitialise_variables_de_document() :
    global infos_page
    global dico_infos_pages
    global filename
    
    reinitialise_variables_de_scrutin()
    filename = None
    infos_page = None
    dico_infos_pages = {}
    

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
Liste_de_deputes_a_enregistrer = []
dico_infos_pages = {}
helper = []

current_legislature = "4"
#logs
logging
logger_critic = logging.getLogger('myapp')
hdlr_critic = logging.FileHandler('./logs/'+current_legislature+'_reconstitues_critic_error.log')
formatter_critic = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr_critic.setFormatter(formatter_critic)
logger_critic.addHandler(hdlr_critic) 
logger_critic.setLevel(logging.NOTSET)


logger_grave = logging.getLogger('main')
hdlr_grave = logging.FileHandler('./logs/'+current_legislature+'_reconstitues_grave_error.log')
formatter_grave = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr_grave.setFormatter(formatter_grave)
logger_grave.addHandler(hdlr_grave) 
logger_grave.setLevel(logging.NOTSET)


logger_info = logging.getLogger('main')
hdlr_info = logging.FileHandler('./logs/'+current_legislature+'_reconstitues_info.log')
formatter_info = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr_info.setFormatter(formatter_info)
logger_info.addHandler(hdlr_info) 
logger_info.setLevel(logging.NOTSET)

nom_fichier_csv = 'votes'+current_legislature+'.csv'
fichier_csv = open(nom_fichier_csv, 'a', newline='')
spamwriter = csv.writer(fichier_csv, delimiter=',')


for root, subdirs, files in os.walk("4-reconstitues"):

    for nomfichier in files :
        filepath = root+"/"+nomfichier
        print("Fichier lu: "+filepath)
        
        fichierlayout = open(filepath).read()
        
        filename = nomfichier

        logger_grave.error("--- new fichier --- "+str(filepath))
        parcours_fichier(fichierlayout)


        sauvegarde_liste_deputes()
        reinitialise_variables_de_document()
        logger_info.info("\n\n\n")

"""
filename = "007.txt";
fichier = open(filename).read()
parcours_fichier(fichier)
"""

sauvegarde_liste_deputes()
fichier_csv.close()
"""
pagetest = pages[37];
pagetest= pagetest.replace('\n','')
lignes = pagetest.split('\n');
"""

