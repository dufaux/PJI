liste_repertoires=`find 5-pdf -type d`
for rep in $liste_repertoires
do
	dest=`echo $rep | cut -d'/' -f 2-`
	mkdir -m 777 "5-layout/$dest"
done
liste_fichiers=`find 5-pdf -name "*.pdf"`

for fichier in $liste_fichiers
do
	dest=`echo $fichier | cut -d'/' -f 2- | cut -d'.' -f 1`
	pdftotext -layout $fichier "5-layout/$dest.txt"
	chmod og+r "5-layout/$dest.txt"
done

