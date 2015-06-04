liste_repertoires=`find 4-pdf -type d`
for rep in $liste_repertoires
do
	dest=`echo $rep | cut -d'/' -f 2-`
	mkdir -m 777 "4-layout/$dest"
done
liste_fichiers=`find 4-pdf -name "*.pdf"`

for fichier in $liste_fichiers
do
	dest=`echo $fichier | cut -d'/' -f 2- | cut -d'.' -f 1`
	pdftotext -layout $fichier "4-layout/$dest.txt"
	chmod og+r "4-layout/$dest.txt"
done

