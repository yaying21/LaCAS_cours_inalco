### Importation des cours d'Inalco sur la plateforme LaCAS ###

Mots-clés : Python(Pandas), SPARQL, Ontologie, Excel, RDFs, Regex

### Objectifs du projet ####
1. Conversion des données d'excel des cours d'Inalco

2. Importation données convertes sur la plateforme

### Structure du code ####

. Nettoyer des données d'excel


. Créer des regex pattern afin de récupérer le nom et prénom d'enseignants

  1. Prénom (première lettre majuscule) +Nom de famille(première lettre majuscule), par exemple, « Michel Blanchard »

  2. Nom de famille (première lettre majuscule) + Prénom(première lettre majuscule), par exemple, « Ville Jean-Luc »
     
  3. Initiale + Nom de famille(première lettre majuscule), par exemple, « L. Pourchez », « J.-L. Ville », « S.S. Hnin Tun »
     
  4. Nom de famille en majuscule + Prénom(première lettre majuscule), par exemple, « KELEDJIAN Mélanie »
     
  5. Nom de famille, par exemple, « Germanos », « Massoud », « SILBERZTEIN »
     
  6. Plusieurs noms d'enseignants, par exemple, « Fathi/ Massoud »
     
  7. Erreur entre nom et prénom, par exemple, « LIWEN Chen »

    Exemple d'un regex pattern :  def find_last_first_name (row_name,first_name = "None", last_name = "None") :

                                      matchNorComp = re.search(r'(((\p{Lu}\p{Ll}+)|(\p{Lu}\p{Ll}+-\p{Lu}{Ll}+)))(\s)+(.*)', str(row[row_name]).strip())
                                      
                                      if matchNorComp :
                                      
                                        first_name = matchNorComp.group(1)#### group(1) : ((\p{Lu}\p{Ll}+)|(\p{Lu}\p{Ll}+-\p{Lu}{Ll}+)))
                                        
                                        last_name = matchNorComp.group(6) ## group(6) : (.*)

  
. Recupérer des URIs d'enseignants avec des requêtes SPARQL de nom et prénom  : 

    def find_individual(okapi_url, opener, firstname, lastname) 

    def find_individual_lastname(okapi_url, opener, lastname)


. Avec Pandas lire des données d'excel et créer des triplets pour chaque donnée

  



