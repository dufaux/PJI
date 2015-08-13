from Levenshtein import distance

####################################################
#################### EXCEPTIONS ####################
####################################################
class DeputeIntrouvableError(Exception) :

    def __init__(self, nom) :
        self.nom = nom

    def get_nom(self) :
        return self.nom


    



class Depute :

    def __init__(self, param_nom, param_prenom, param_parti, param_vote) :
        self.nom = param_nom
        self.prenom = param_prenom
        self.parti = param_parti
        self.vote = param_vote




class Depute_modele :

    def __init__(self, param_nom, param_prenom, param_parti, param_departement) :
        self.nom = param_nom
        self.prenom = param_prenom
        self.parti = param_parti
        self.departement = param_departement

    # retourne "nom" et "nom (prenom)" et si nom commence par du/de "nom (de/du)" avec nom sans le de/du
    def get_liste_exemples_de_nom(self) :
        les_mots = []
        les_mots.append(self.nom)
        les_mots.append(self.nom+" ("+self.prenom+")")
        if(self.nom.split()[0].lower() == "du" or self.nom.split()[0].lower() == "de" or self.nom.split()[0].lower() == "des") :
            les_mots.append(" ".join(self.nom.split()[1:len(self.nom)])+" ("+self.nom.split()[0].lower()+")")
        if(self.nom.split()[0].lower()[0:2] == "d'") :
            les_mots.append(self.nom[2:]+ " (d')")
        if(self.nom.lower()[0:5] == "de la") :
            les_mots.append(self.nom[5:]+ " (de la)")
        
        return les_mots







class Liste_deputes :

    def __init__(self) :
        self.liste = []
        self.partis_cherches = ["UDR","RI","FGDS","S","C","PDM","NI","PSRG","RDS","UC"]
        #comprend les partis de la 4em et la 5em.


    #chaque ligne: nom_parfois_plusieurs_mots prenom groupe departement_parfois_plusieurs_mots
    def init_from_file(self, name_file) :
        fichier = open(name_file).read()
        lst = fichier.split("\n")

        for i in range(len(lst)) :
            if lst[i] :
                ligne = lst[i].split()
                for j in range(len(ligne)) :
                    if(ligne[j] in self.partis_cherches) :
                        depute = Depute_modele(" ".join(ligne[1:j]),ligne[0],ligne[j]," ".join(ligne[j+1:len(ligne)]))
                        self.liste.append(depute)

    def cherche_depute(self, text, ratio) :
        
        distance_minim = None
        depute_minim = None
        
        for i in range(len(self.liste)) :
            modeles = self.liste[i].get_liste_exemples_de_nom()
            for j in range(len(modeles)) :
                dist = distance(modeles[j],text)
                if(distance_minim == None or dist < distance_minim) :
                    distance_minim = dist
                    depute_minim = self.liste[i]

        if(len(text)*ratio < distance_minim) :
            raise DeputeIntrouvableError(text)
        
        return (distance_minim,depute_minim)


