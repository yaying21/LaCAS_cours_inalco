#!/usr/bin/env python3
# coding=utf-8

import unidecode
from multiprocessing.connection import answer_challenge
import pandas as pd
import rdflib
from rdflib import Namespace, URIRef, RDFS, Literal,RDF
import regex as re
from okapi_api import okapi_login, okapi_logout, sparql_search, sparql_admin_internal, set_individual


listNone = []  # a list for the result "None" of sparql i.e. the person does not exist in LaCAS ==> create an account 
listError = [] # a list of names for the result  sparql "error"  i.e. either the person has two uris or there are homonyms
listPb = []   # a list of names that the program cannot treat


base_url_pro = "https://lacas.inalco.fr/portals"
okapi_url = base_url_pro
core = Namespace("http://www.ina.fr/core#")
login = ""
passwd = ""
opener = okapi_login(okapi_url, login, passwd)

#####################################################################################################################
################### find teachers' uri by first and last name #######################################################

def find_individual(okapi_url, opener, firstname, lastname): #  
    """
    query to find the uri using the first name and last name of enseignant
    """
    answer = sparql_search(okapi_url, """
	      PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
	      PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	      PREFIX owl: <http://www.w3.org/2002/07/owl#>
	      PREFIX core: <http://www.ina.fr/core#>
	      SELECT distinct ?individual 
          WHERE {
		    ?individual a core:PhysicalPerson OPTION (inference "http://campus-aar/owl") .
		    ?individual a core:CommonKnowledge .
		    ?individual rdfs:label ?lab .

		    ?lab bif:contains "'""" + lastname + """' AND '"""+firstname+"""'".                             
            
}	      """, opener)
      
    if len(answer) == 0:  
        return None
    elif len(answer) > 1: # find more than one uri for a teacher    
        return "duplicate"
    else :   
        return answer[0]['individual']['value'] #return individual uri


#########################################################################################################
##################### find uri of teachers by last name #################################################

def find_individual_lastname(okapi_url, opener, lastname):  
    """
    query to find uri of teachers by last name
    """
    answer = sparql_search(okapi_url, """
	      PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
	      PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	      PREFIX owl: <http://www.w3.org/2002/07/owl#>
	      PREFIX core: <http://www.ina.fr/core#>
	      SELECT distinct ?individual 
          WHERE {
		    ?individual a core:PhysicalPerson OPTION (inference "http://campus-aar/owl") .
		    ?individual a core:CommonKnowledge .
		    ?individual rdfs:label ?lab .

		    ?lab bif:contains "'""" +lastname+""" '" .
    }	      
    """, opener)
   
    if len(answer) == 0:  # 0 means this person does not exist on site lacas
        return None
    elif len(answer) > 1:  # more than 1 URI, two possibilities. Either the perosn has two URIs or the same name exists
        return "duplicate"
    else :
        return answer[0]['individual']['value'] 
        
        
########################################################################################################################
###################################################### find URI of other properties ####################################

def find_uri(okapi_url, opener, label, type):
    """
    type : classe cible
    query to find uri for others propreties

    """
    answer = sparql_search(okapi_url, """
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX core: <http://www.ina.fr/core#>
                SELECT distinct ?uri_niveau
                WHERE {
                ?uri_niveau a <"""+type+"""> OPTION (inference "http://campus-aar/owl").
                ?uri_niveau rdfs:label ?lab.
                FILTER(CONTAINS(lcase(?lab), lcase(\"""" +label+"""\"))) 
                }
    """, opener)
    if len(answer) == 0:
        return None
    else :
        return answer[0]['uri_niveau']['value']


##########################################################################################################################
#################### def separately extracted the first nad last name of six columns of teachers #########################
##########################################################################################################################
def find_last_first_name (row_name,first_name = "None", last_name = "None"):
    """
    def separately extracted the first nad last name of six columns of teachers
    """
    #matchNorComp match cases except those with capitalized last name, cases starting with initial letter and abnormal cases
    matchNorComp = re.search(r'(((\p{Lu}\p{Ll}+)|(\p{Lu}\p{Ll}+-\p{Lu}{Ll}+)))(\s)+(.*)', str(row[row_name]).strip())
    if matchNorComp :
        first_name = matchNorComp.group(1)#### group(1) : ((\p{Lu}\p{Ll}+)|(\p{Lu}\p{Ll}+-\p{Lu}{Ll}+)))
        last_name = matchNorComp.group(6) ## group(6) : (.*)
    
    #matchLettre match  cases starting with initial letter
    matchLettre =re.search (r'(\p{Lu}.*\.)(\s)*(.*)', str(row[row_name]).strip()) #O.Duvallon; M.-C. Saglio-Yatzimirsky; J.-L. Martineau
    if matchLettre :
        first_name = matchLettre.group(1)
        last_name = matchLettre.group(3)

    # matchMjucu match cases with capitalized last name
    matchMajucu = re.search(r'(^\p{Lu}+(( |(\s)*-(\s)*)\p{Lu}+)*)(\s)+(.*)', str(row[row_name]).strip()) #KELEDJIAN Mélanie; 
    if matchMajucu :
        last_name = matchMajucu.group(1)
        first_name = matchMajucu.group(7)

    # matchAnormal match cases with only last name or first name
    matchAnormal = re.search(r'^(\s)*((\p{Lu}\p{Ll}+)|(\p{Lu}\p{Ll}+-\p{Lu}{Ll}+)|(\p{Lu}+)|(\p{Lu}+-\p{Lu}+))(\s)*$', str(row[row_name])) # Germanos; Massoud;SILBERZTEIN;VIDAL-GORENE
    if matchAnormal :
        last_name = matchAnormal.group(0) # group(0) = last name or first name 
    
    # list for cases that cant be separately extracted
    if last_name == "None" and str(row[row_name]).strip() != "nan" and str(row[row_name]).strip() != "-" and str(row[row_name]).strip() != "N.N" and str(row[row_name]).strip() != "M.N":
        listPb.append(row[row_name])
   
    return first_name, last_name
   
############################################################################################################################################
#################### def retrieve the firstname and lastname and create URIs for those people dont exist on lacase #########################
############################################################################################################################################

def uri_enseignant (colonne) :
    cours_uri = "http://lacas.inalco.fr/cours/" + str(row["CODE"])
    
    first_name, last_name = find_last_first_name(colonne) # get first name and last name separately
    #print('ENSEIGNANT_firstname :',first_name, 'ENSEIGNANT1_lastname :',last_name)

    uri_personne = find_individual(okapi_url, opener, first_name, last_name) # get uri of the person with fisrt name and last name
    if uri_personne != None and uri_personne != "duplicate":                  # check query find-individual yields results
        kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_1450771976'), URIRef(uri_personne), URIRef(cours_uri))) # add triplet to knowledge base
    else :                                                                                                                          
        uri_personne = find_individual_lastname(okapi_url, opener, last_name) # get uri only with last name
        if uri_personne != None and uri_personne != "duplicate":
            kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_1450771976'), URIRef(uri_personne), URIRef(cours_uri))) 

        ############################# create uri for teachers who dont exist on lacas #####################################
        elif uri_personne == None and (first_name and last_name) != "None": # exist a number of values for None in the excel sheet
            listNone.append(first_name+" "+last_name) 

            ##### standardize first and last names
            first_name_norma = unidecode.unidecode(first_name) # remove accents of first name 
            first_name_norma = first_name.lower().strip() # lower letter of first name and  remove the espace
            first_name_norma = re.sub(' ', '_', first_name_norma) ## add "_" for hyphenated last names

            last_name_norma =  unidecode.unidecode(last_name)
            last_name_norma = last_name.lower().strip()
            last_name_norma = re.sub(' ', '_', last_name_norma)

            ############################################ create triplet for the teachers non-existant #######################################################################

            uri_personne_iconnue = "http://lacas.inalco.fr/resource/" + first_name_norma + "_" + last_name_norma  # sujet of triplet
            kb.add((URIRef(uri_personne_iconnue), RDF.type, URIRef('http://www.campus-AAR.fr/resource_1271554455'), URIRef(uri_personne_iconnue))) #
            kb.add((URIRef(uri_personne_iconnue), RDF.type, URIRef('http://campus-aar.fr/asa#693279f0-2e16-45f6-aea5-98c48840a2da'), URIRef(uri_personne_iconnue)))
            kb.add((URIRef(uri_personne_iconnue), RDF.type, URIRef('http://www.ina.fr/core#CommonKnowledge'), URIRef(uri_personne_iconnue)))
            kb.add((URIRef(uri_personne_iconnue), URIRef('http://campus-aar.fr/asa#forname'), Literal(str(first_name).strip()), URIRef(uri_personne_iconnue)))
            kb.add((URIRef(uri_personne_iconnue), URIRef('http://campus-aar.fr/asa#lastname'), Literal(str(last_name).strip()), URIRef(uri_personne_iconnue)))
            kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_1450771976'), URIRef(uri_personne_iconnue), URIRef(cours_uri)))

        ########################### add names of teachers who have more than one uri on lacas to list  #########################################################################
        elif uri_personne == "duplicate": 
            listError.append(first_name+" "+last_name) 

    return uri_personne      

kb = rdflib.Dataset(default_union=True) # create an empty knowledge base
#file2 = "BDD EXHAUSTIVE FORMATIONS - NOV 2022.xlsx"
file2 = "test_novo.xlsx"
dict_sheets =pd.read_excel(io=file2, sheet_name=None, keep_default_na=False)  # resultats = dict  keep_default_na=False les celles vide isnull() 
#df = dict_sheets["Feuille 1"]
df = dict_sheets["Sheet1"]
#print(df.keys())

#################################################################################################################
############################### create database RDF from Sheet 1 ################################################

for index, row in df.iterrows():
    if str(row["NIVEAU"]).strip() == "M2" or str(row["NIVEAU"]).strip() == "M1":
        cours_uri = "http://lacas.inalco.fr/cours/" + str(row["CODE"])
        kb.add((URIRef(cours_uri), RDF.type, URIRef('http://www.campus-AAR.fr/resource_1334577479'), URIRef(cours_uri))) 
        kb.add((URIRef(cours_uri), RDF.type, URIRef('http://www.campus-AAR.fr/resource_1798461775'), URIRef(cours_uri))) 
        kb.add((URIRef(cours_uri), RDF.type, URIRef('http://www.ina.fr/core#CommonKnowledge'), URIRef(cours_uri)))
        if str(row["CODE"]) !=  "-" :
            kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_268607413') , Literal((str(row["CODE"])).strip()), URIRef(cours_uri)))
        
        if str(row['NIVEAU']) !=  "-" :
            label = str(row['NIVEAU']).strip()
            type = "http://www.campus-AAR.fr/resource_286128949" # uri of target class
            niveau_uri = find_uri(okapi_url, opener, label, type)
            if niveau_uri != None :      # != None query find uri of value 
                kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_97869557'), URIRef(niveau_uri), URIRef(cours_uri)))
            else:
                kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_97869557'), Literal((str(row["NIVEAU"])).strip()), URIRef(cours_uri))) # if query cant find uri of the value, creat triple with the string

        if str(row["DPT/FIL/THD"]) !=  "-" :
            label = str(row['DPT/FIL/THD']).strip()
            type= "http://www.campus-AAR.fr/resource_1411661759"
            dpt_uri = find_uri(okapi_url, opener, label, type)
            if dpt_uri != None :
                kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_641782260'), URIRef(dpt_uri), URIRef(cours_uri)))
            else:
                kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_641782260'), Literal((str(row["DPT/FIL/THD"])).strip()), URIRef(cours_uri)))

        if str(row["DIPLÔME NATIONAL"]) !=  "-" :
            label = str(row['DIPLÔME NATIONAL']).strip()
            type= "http://www.campus-AAR.fr/resource_523369576"
            dplomN_uri = find_uri(okapi_url, opener, label, type)
            if dplomN_uri != None :
                kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_1357774698'), URIRef(dplomN_uri), URIRef(cours_uri)))
            else :
                kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_1357774698'), Literal((str(row["DIPLÔME NATIONAL"])).strip()), URIRef(cours_uri)))

        if str(row["DIPLÔME ETAB"]) !=  "-" :
            label = str(row['DIPLÔME ETAB']).strip()
            type= "http://www.campus-AAR.fr/resource_523369576"
            dplomE_uri = find_uri(okapi_url, opener, label, type)
            if dplomE_uri != None :
                kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_1357774698'), URIRef(dplomE_uri), URIRef(cours_uri)))
            else:
                kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_1357774698'), Literal((str(row["DIPLÔME ETAB"])).strip()), URIRef(cours_uri)))

        if str(row["RATTACHEMENT"]) !=  "-" :
            label = str(row['RATTACHEMENT']).strip()
            type= "http://www.campus-AAR.fr/resource_1550876036"
            rattach_uri = find_uri(okapi_url, opener, label, type)
            #print(rattach_uri)
            if rattach_uri != None :
                kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_1278616783'), URIRef(rattach_uri), URIRef(cours_uri)))
            else :
                kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_1278616783'), Literal((str(row["RATTACHEMENT"])).strip()), URIRef(cours_uri)))

        if str(row["Libellé long"]) !=  "-" :
            kb.add((URIRef(cours_uri), RDFS.label, Literal((str(row["Libellé long"])).strip()), URIRef(cours_uri)))

        if str(row["ELP - Nature"]) !=  "-" :   
            label = str(row['ELP - Nature']).strip()
            type= "http://www.campus-AAR.fr/resource_576746240"
            elp_uri = find_uri(okapi_url, opener, label, type)
            if elp_uri != None :
                kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_462657612'), URIRef(elp_uri), URIRef(cours_uri)))
            else :
                kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_462657612'), Literal((str(row["ELP - Nature"])).strip()), URIRef(cours_uri))) 

        if str(row["ECTS"]) !=  "-" :
            kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_1614333279') , Literal((str(row["ECTS"])).strip()), URIRef(cours_uri)))
        if str(row["Langue utilisée"]) !=  "-" :
            kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_1550876036') , Literal((str(row["Langue utilisée"])).strip()), URIRef(cours_uri)))
        #     ############ Enseignant 1 2 ...
        if str(row["VOL. HORAIRE SEMESTRE"]) !=  "-" :
            kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_728184693') , Literal((str(row["VOL. HORAIRE SEMESTRE"])).strip()), URIRef(cours_uri))) 
        if str(row["MOT-CLEF 1"]) !=  "-" :
            kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_1096865541') , Literal((str(row["MOT-CLEF 1"])).strip()), URIRef(cours_uri))) #KeyError: 'MOT-CLEF 1'
        if str(row["MOT-CLEF 2"]) !=  "-" :
            kb.add((URIRef(cours_uri), URIRef('http://campus-aar.fr/asa#589f6f72-1998-40b2-ad58-8f2c3d2c68c1') , Literal((str(row["MOT-CLEF 2"])).strip()), URIRef(cours_uri)))   
        if str(row["DESCRIPTIF"]) !=  "-" : 
            kb.add((URIRef(cours_uri), URIRef('http://campus-aar.fr/asa#description'), Literal((str(row["DESCRIPTIF"])).strip()), URIRef(cours_uri))) # http://campus-aar.fr/asa#description  does not look like a valid URI, trying to serialize this will break.
        if str(row["APPROCHE PEDAGOGIQUE"]) !=  "-" :    
            kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_1567819022'), Literal((str(row["APPROCHE PEDAGOGIQUE"])).strip()), URIRef(cours_uri))) # nan toujours 
        
        if str(row["NATURE DES COURS bis (extraction)"]) !=  "-" :
            label = str(row['NATURE DES COURS bis (extraction)']).strip()
            type= "http://www.campus-AAR.fr/resource_759713400"
            natureCours_uri = find_uri(okapi_url, opener, label, type)
            if natureCours_uri != None :
                kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_980724250'), URIRef(natureCours_uri), URIRef(cours_uri)))
            else :
                kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_980724250'), Literal((str(row["NATURE DES COURS bis (extraction)"])).strip()), URIRef(cours_uri))) # nan toujours 

        if str(row["PREREQUIS DE LANGUE"]) !=  "-" :
            if str(row['PREREQUIS DE LANGUE']).strip() == "NON" :  # NON means the course has no requirements for students
                prerequis_uri = 'http://www.campus-AAR.fr/entity_1645425016'
                kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_2009619886'), URIRef(prerequis_uri), URIRef(cours_uri)))
            else :
                prerequis_uri = 'http://www.campus-AAR.fr/entity_1620445026'
                kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_2009619886'), URIRef(prerequis_uri), URIRef(cours_uri)))
        if str(row["EVALUATION"]) !=  "-" :
            kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_1878344084'), Literal((str(row["EVALUATION"])).strip()), URIRef(cours_uri)))
        if str(row["LIEN BROCHURE"]) !=  "-" :
            kb.add((URIRef(cours_uri), URIRef('http://campus-aar.fr/asa#d106dccf-e288-4a8a-aa4e-d17748e28158-prop'), Literal((str(row["LIEN BROCHURE"])).strip()), URIRef(cours_uri)))
        if str(row["COMMENTAIRE"]) !=  "-" :
            kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_776553740'), Literal((str(row["COMMENTAIRE"])).strip()), URIRef(cours_uri)))

        if str(row["COURS PRES/HYBR/DIST."]) !=  "-" :
            label = str(row['COURS PRES/HYBR/DIST.']).strip()
            type= "http://www.campus-AAR.fr/resource_831669783"
            preHybr_uri = find_uri(okapi_url, opener, label, type)
            if preHybr_uri != None :
                kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_709471563'), URIRef(preHybr_uri), URIRef(cours_uri)))
            else :   
                kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_709471563'), Literal((str(row["COURS PRES/HYBR/DIST."])).strip()), URIRef(cours_uri)))

        if str(row["TOURNANT (O/N)"]) !=  "-" :
            kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_1529319551'), Literal((str(row["TOURNANT (O/N)"])).strip()), URIRef(cours_uri)))
        if str(row["OUVERT EN PASSEPORT ?"]) !=  "-" :
            kb.add((URIRef(cours_uri), URIRef('http://www.campus-AAR.fr/resource_765118808'), Literal((str(row["OUVERT EN PASSEPORT ?"])).strip()), URIRef(cours_uri)))

        uri_enseignant("ENSEIGNANT 1")
        uri_enseignant("ENSEIGNANT 2")
        uri_enseignant("ENSEIGNANT 3")
        uri_enseignant("ENSEIGNANT 4")
        uri_enseignant("ENSEIGNANT 5")
        uri_enseignant("ENSEIGNANT 6")



    # TODO: complete course metadata thanks to the mapping "
    # handle the "intervenant" column : retrieve the firstname and lastname and use find_individual(okapi_url, opener, firstname, lastname) 
    # save individual to database: set_individual(okapi_url, cours_uri, kb, opener)
kb.serialize("test_uripreson" + '.trig', format='trig', encoding='utf-8')# ajouter uen
