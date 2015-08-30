liste_repertoires=`find 6-pdf -type d`
for rep in $liste_repertoires
do
	dest=`echo $rep | cut -d'/' -f 2-`
	mkdir -m 777 "6-layout/$dest"
done
liste_fichiers=`find 6-pdf -name "*.pdf"`

for fichier in $liste_fichiers
do
	dest=`echo $fichier | cut -d'/' -f 2- | cut -d'.' -f 1`
	pdftotext -layout $fichier "6-layout/$dest.txt"
	chmod og+r "6-layout/$dest.txt"
done

