
from depute import DeputeIntrouvableError
from depute import Liste_deputes
from depute import Depute_modele
from depute import Depute


liste_incomplete = Liste_deputes() #peut etre passé en globale fixe
liste_incomplete.init_from_file("./6-deputes/liste.txt")

liste_complete = open("./6-deputes/liste_complete.txt").read()

liste_complete = ''.join(i for i in liste_complete if not i.isdigit())
liste_complete = liste_complete.replace("/","")

lignes = liste_complete.split("\n")


"""for depute in liste_incomplete.liste :
    print("PRENOM = "+depute.prenom)
    print("NOM = "+depute.nom)
"""
for ligne in lignes :
    le_nom = ligne.split()[-1]
    le_nom = le_nom.lower()
    nom = le_nom[0].upper() + le_nom[1:]

    #print("chercher nom = "+nom)
    try :
        retour = liste_incomplete.cherche_depute(nom,0)
        #print("distance = "+str(retour[0])+" vrai nom="+str(retour[1].nom)+" et nom cherche="+str(nom))
    except DeputeIntrouvableError as e :
        print("PAS DEDANS = ("+nom+")"+ligne)
