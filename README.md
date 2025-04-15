### Importation des cours d'Inalco sur la plateforme LaCAS ###

Mots-clés : Python(Pandas), SPARQL, Ontologie, Excel, RDFs, Regex

### Objectifs du projet ####
1. Conversion des données d'excel des cours d'Inalco

2. Importation données convertes sur la plateforme

### Structure du code ####

. Créer des regex pattern afin de récupérer le nom et prénom d'enseignants

  def find_last_first_name (row_name,first_name = "None", last_name = "None")


. Recupérer des URIs d'enseignants avec des requêtes SPARQL de nom et prénom  : 

  def find_individual(okapi_url, opener, firstname, lastname) 

  def find_individual_lastname(okapi_url, opener, lastname)


. Avec Pandas lire des données d'excel et créer des triplets pour chaque donnée



