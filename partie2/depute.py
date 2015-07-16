

class Liste_deputes :

    def __init__(self) :
        self.liste = []
        self.partis_cherches = ["UDR","RI","FGDS","S","C","PDM","RI"]

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
                dist = distance(modele,text)
                if(not distance_minim or dist < distance_minim) :
                    distance_minim = dist
                    depute_minim = self.liste[i]
            


        

class Depute_modele :

    def __init__(self, param_nom, param_prenom, param_parti, param_departement) :
        self.nom = param_nom
        self.prenom = param_prenom
        self.parti = param_parti
        self.departement = param_departement

    # retourne "nom" et "nom (prenom)" et si nom commence par du/de "nom (de/du)" avec nom sans le de/du
    def get_liste_exemples_de_nom() :
        les_mots = []
        les_mots.append(self.nom)
        les_mots.append(self.nom+" ("+self.prenom+")")
        if(self.nom.split()[0].lower() == "du" or self.nom.split()[0].lower() == "de") :
            les_mots.append(" ".join(self.nom.split()[1:len(nom)])+" ("+self.nom.split()[0].lower()+")")

        return les_mots

class Depute :

    def __init__(self) :
        self.nom = None
        self.prenom = None
        self.parti = None
        self.vote = None


