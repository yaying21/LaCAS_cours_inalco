import http.cookiejar
import json
import rdflib
import ssl
import urllib.error
import urllib.parse
import urllib.request
from rdflib import URIRef, Literal, Namespace, RDF

# login to Okapi through HTTPS, Apache Basic Authentification and Okapi authentification (mandatory to edit resources)
def okapi_login_old(base_url, login, passwd):
    cj = http.cookiejar.CookieJar()
    pro = urllib.request.HTTPCookieProcessor(cj)
    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, base_url + "/", login, passwd)
    auth_handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
    context = ssl._create_unverified_context()
    opener = urllib.request.build_opener(pro,urllib.request.HTTPSHandler(context=context),auth_handler)
    url = base_url + "/api/saphir/login?user=" + login + "&password=" + passwd
    op = opener.open(url)
    if op.msg == "OK":
        print("%s logged !!" %login)
    urllib.request.install_opener(opener)
    return opener

def okapi_login(base_url, login, passwd):
    cj = http.cookiejar.CookieJar()
    pro = urllib.request.HTTPCookieProcessor(cj)
    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, base_url + "/", login, passwd)
    auth_handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
    context = ssl._create_unverified_context()
    opener = urllib.request.build_opener(pro,urllib.request.HTTPSHandler(context=context),auth_handler)
    url = base_url + "/api/saphir/user/login?user=" + login + "&password=" + passwd
    op = opener.open(url)
    if op.msg == "OK":
        print("%s logged !!" %login)
    urllib.request.install_opener(opener)
    return opener


# logout from Okapi and Apache !
def okapi_logout(base_url, opener):
    url = base_url + "/api/saphir/user/logout"
    try:
        op = opener.open(url)
        print(op)
    except urllib.error.HTTPError:
        for h in opener.handlers :
            if isinstance(h,urllib.request.HTTPCookieProcessor):
                h.cookiejar.clear()
        for h in opener.handlers:
            if isinstance(h, urllib.request.HTTPBasicAuthHandler):
                h.add_password(None, base_url + "/", "fake", "fake")
        try:
            opener.open(base_url + "/api/saphir/user/login")
        except urllib.error.HTTPError:
            print("logged out !!")
    return opener


# logout from Okapi and Apache !
def okapi_logout_old(base_url, opener):
    url = base_url + "/api/saphir/user/logout"
    try:
        op = opener.open(url)
        print(op)
    except urllib.error.HTTPError:
        for h in opener.handlers :
            if isinstance(h,urllib.request.HTTPCookieProcessor):
                h.cookiejar.clear()
        for h in opener.handlers:
            if isinstance(h, urllib.request.HTTPBasicAuthHandler):
                h.add_password(None, base_url + "/", "fake", "fake")
        try:
            opener.open(base_url + "/api/saphir/login")
        except urllib.error.HTTPError:
            print("logged out !!")
    return opener


# get list of okapi users
def get_users(base_url, opener):
    url = base_url + "/api/saphir/get_users"
    response = opener.open(url).read().decode()
    parsed_json = json.loads(response),
    return parsed_json


# get neighbours (direct ones) of uri with labels for properties and classes
def get_neighbours(base_url, uri_ref, kb, opener, format="rdf"):
    url = base_url + "/api/saphir/get_neighbours" \
          + "?uri=" + urllib.parse.quote(uri_ref.toPython()) \
          + "&format=" + format
    response = opener.open(url).read().decode()
    if format == "rdf":
        kb.parse(format='trig', data=response, publicID="http://toDelete/")
        # update the fake uris with toDelete base by the initial empty one
        for (s, p, o, g) in kb.quads((None, URIRef("http://www.ina.fr/core#hasType"), None, None)):
            if o.toPython().startswith("http://toDelete/"):
                kb.add((s, p, URIRef(o.toPython().replace("http://toDelete/", "")), g))
                kb.remove((s, p, o, g))
    else:
        # todo MUST BE completed to handle typed literals !!!
        parsed_json = json.loads(response),
        for result in parsed_json[0]["results"]["bindings"]:
            kb.add((URIRef(result["s"]["value"]) if result["s"]["type"] == 'uri' else Literal(result["s"]["value"]),
                    URIRef(result["p"]["value"]) if result["p"]["type"] == 'uri' else Literal(result["p"]["value"]),
                    URIRef(result["o"]["value"]) if result["o"]["type"] == 'uri' else Literal(result["o"]["value"]),
                    URIRef(result["g"]["value"]) if result["g"]["type"] == 'uri' else Literal(result["g"]["value"])))
    return kb


# get a segment in read-only mode
def get_segment(base_url, segment_ref, kb, opener, media="false", labels="false", classes="false",
                properties="false", format="rdf"):
    url = base_url + "/api/saphir/get_segment?id="\
          + urllib.parse.quote(segment_ref.toPython())\
          + "&labels=" + labels \
          + "&media=" + media \
          + "&classes=" + classes \
          + "&properties=" + properties \
          + "&format=" + format
    response = opener.open(url).read().decode()
    if format == "rdf":
        kb.parse(format='trig', data=response, publicID="http://toDelete/")
        # update the fake uris with toDelete base by the initial empty one
        for (s, p, o, g) in kb.quads((None, URIRef("http://www.ina.fr/core#hasType"), None, None)):
            if o.toPython().startswith("http://toDelete/"):
                kb.add((s, p, URIRef(o.toPython().replace("http://toDelete/", "")), g))
                kb.remove((s, p, o, g))
    else:
        # todo MUST BE completed to handle typed literals !!!
        parsed_json = json.loads(response)
        for result in parsed_json[0]["results"]["bindings"]:
            kb.add((URIRef(result["s"]["value"]) if result["s"]["type"] == 'uri' else Literal(result["s"]["value"]),
                    URIRef(result["p"]["value"]) if result["p"]["type"] == 'uri' else Literal(result["p"]["value"]),
                    URIRef(result["o"]["value"]) if result["o"]["type"] == 'uri' else Literal(result["o"]["value"]),
                    URIRef(result["g"]["value"]) if result["g"]["type"] == 'uri' else Literal(result["g"]["value"])))
    return kb


def get_media(base_url, media_ref, kb, opener, write="false", format="rdf",  withComputed="false"):
    url = base_url + "/api/saphir/get_media?media="\
          + urllib.parse.quote(media_ref.toPython())\
          + "&lock=" + write \
          + "&withComputed=" + withComputed \
          + "&format=" + format
    response = opener.open(url).read().decode()
    if response != 'error_unknown_uri':
        if format == "rdf":
            kb.parse(format='trig', data=response, publicID="http://toDelete/")
            # update the fake uris with toDelete base by the initial empty one
            for (s, p, o, g) in kb.quads((None, URIRef("http://www.ina.fr/core#hasType"), None, None)):
                if o.toPython().startswith("http://toDelete/"):
                    kb.add((s, p, URIRef(o.toPython().replace("http://toDelete/", "")), g))
                    kb.remove((s, p, o, g))
        else:
            # todo MUST BE completed to handle typed literals !!!
            parsed_json = json.loads(response)
            for result in parsed_json[0]["results"]["bindings"]:
                kb.add((URIRef(result["s"]["value"]) if result["s"]["type"] == 'uri' else Literal(result["s"]["value"]),
                        URIRef(result["p"]["value"]) if result["p"]["type"] == 'uri' else Literal(result["p"]["value"]),
                        URIRef(result["o"]["value"]) if result["o"]["type"] == 'uri' else Literal(result["o"]["value"]),
                        URIRef(result["g"]["value"]) if result["g"]["type"] == 'uri' else Literal(result["g"]["value"])))

        # remove technical triples added by the server to specify editable layers
        for (s, p, o, g) in kb.quads((None, URIRef("http://www.ina.fr/core#is_editable"), None, None)):
                kb.remove((s, p, o, g))
        return True
    else:
        return False

# save or update media using the x-trig format
def set_media(base_url, media_ref, media_url, identifier, mimeType, segmentType, threshold, media_segment_ref,kb, opener,
              unlock="true"):
    url = base_url + "/api/saphir/set_media?uri=" + urllib.parse.quote(media_ref.toPython()) +\
          "&url=" + media_url +\
          "&identifier=" + identifier +\
          "&mimetype=" + mimeType +\
          "&segmenttype=" + urllib.parse.quote(segmentType) +\
          "&threshold=" + threshold +\
          "&unlock=" + unlock
    print("url:********************************************* " + url)
    trig_string = kb.graph(media_segment_ref.toPython()).serialize(format='trig', base='.', encoding='utf-8')
    req = urllib.request.Request(url, trig_string, {'Content-Type': 'application/trig; charset: UTF-8'})
    op = urllib.request.urlopen(req)
    return op.read().decode()

def get_media_instances(base_url, media_ref, kb, opener, format="rdf"):
    url = base_url + "/api/saphir/get_media_instances?media="\
          + urllib.parse.quote(media_ref.toPython())\
          + "&format=" + format
    response = opener.open(url).read().decode()
    if response != 'error_unknown_uri':
        if format == "rdf":
            kb.parse(format='trig', data=response, publicID="http://toDelete/")
            # update the fake uris with toDelete base by the initial empty one
            for (s, p, o, g) in kb.quads((None, None, None, None)):

                if (type(o) == URIRef) and (o.toPython().startswith("http://toDelete/")):
                    kb.add((s, p, URIRef(o.toPython().replace("http://toDelete/", "")), g))
                    kb.remove((s, p, o, g))

        else:
            # todo MUST BE completed to handle typed literals !!!
            parsed_json = json.loads(response)
            for result in parsed_json[0]["results"]["bindings"]:
                kb.add((URIRef(result["s"]["value"]) if result["s"]["type"] == 'uri' else Literal(result["s"]["value"]),
                        URIRef(result["p"]["value"]) if result["p"]["type"] == 'uri' else Literal(result["p"]["value"]),
                        URIRef(result["o"]["value"]) if result["o"]["type"] == 'uri' else Literal(result["o"]["value"]),
                        URIRef(result["g"]["value"]) if result["g"]["type"] == 'uri' else Literal(result["g"]["value"])))

        # remove technical triples added by the server to specify editable layers
        for (s, p, o, g) in kb.quads((None, URIRef("http://www.ina.fr/core#is_editable"), None, None)):
                kb.remove((s, p, o, g))
        return True
    else:
        return False


def get_individual(base_url, individual_ref, kb, opener, write="false", labels="false", format="rdf"):
    url = base_url + "/api/saphir/get_individual?uri="\
          + urllib.parse.quote(individual_ref.toPython())\
          + "&labels=" + labels \
          + "&lock=" + write \
          + "&format=" + format
    response = opener.open(url).read().decode()
    if response != 'error_unknown_uri':
        if format == "rdf":
            kb.parse(format='trig', data=response, publicID="http://toDelete/")
            # update the fake uris with toDelete base by the initial empty one
            for (s, p, o, g) in kb.quads((None, URIRef("http://www.ina.fr/core#hasType"), None, None)):
                if o.toPython().startswith("http://toDelete/"):
                    kb.add((s, p, URIRef(o.toPython().replace("http://toDelete/", "")), g))
                    kb.remove((s, p, o, g))
        else:
            # todo MUST BE completed to handle typed literals !!!
            parsed_json = json.loads(response)
            for result in parsed_json[0]["results"]["bindings"]:
                kb.add((URIRef(result["s"]["value"]) if result["s"]["type"] == 'uri' else Literal(result["s"]["value"]),
                        URIRef(result["p"]["value"]) if result["p"]["type"] == 'uri' else Literal(result["p"]["value"]),
                        URIRef(result["o"]["value"]) if result["o"]["type"] == 'uri' else Literal(result["o"]["value"]),
                        URIRef(result["g"]["value"]) if result["g"]["type"] == 'uri' else Literal(result["g"]["value"])))

        # remove technical triples added by the server to specify editable layers
        for (s, p, o, g) in kb.quads((None, URIRef("http://www.ina.fr/core#is_editable"), None, None)):
                kb.remove((s, p, o, g))
        return True
    else:
        return False


# save or update an analysis to Okapi using the x-trig format
def set_individual(base_url, individual_ref, kb, opener):
    url = base_url + "/api/saphir/set_individual?uri=" + urllib.parse.quote(individual_ref.toPython()) + "&unlock=true"
    trig_string = kb.graph(individual_ref.toPython()).serialize(format='trig', base='.', encoding='utf-8')
    req = urllib.request.Request(url, trig_string, {'Content-Type': 'application/trig; charset: UTF-8'})
    op = urllib.request.urlopen(req)
    # opener.addheaders.append(('Content-Type', 'text/plain'))
    # op = opener.open(url, data)
    return op.read().decode()


def delete_individual(base_url, individual_ref, opener):
    url = base_url + "/api/saphir/remove_individual?uri=" + urllib.parse.quote(individual_ref.toPython()) + "&force=true"
    answer = opener.open(url)
    return answer.read().decode()

def get_corpus(base_url, corpus_ref, kb, opener, write="false", labels="false", format="rdf"):
    url = base_url + "/api/saphir/get_corpus?uri="\
          + urllib.parse.quote(corpus_ref.toPython())\
          + "&labels=" + labels \
          + "&lock=" + write \
          + "&format=" + format
    print(url)
    response = opener.open(url).read().decode()
    if response != 'error_unknown_uri':
        if format == "rdf":
            kb.parse(format='trig', data=response, publicID="http://toDelete/")
            # update the fake uris with toDelete base by the initial empty one
            for (s, p, o, g) in kb.quads((None, URIRef("http://www.ina.fr/core#hasType"), None, None)):
                if o.toPython().startswith("http://toDelete/"):
                    kb.add((s, p, URIRef(o.toPython().replace("http://toDelete/", "")), g))
                    kb.remove((s, p, o, g))
        else:
            # todo MUST BE completed to handle typed literals !!!
            parsed_json = json.loads(response)
            for result in parsed_json[0]["results"]["bindings"]:
                kb.add((URIRef(result["s"]["value"]) if result["s"]["type"] == 'uri' else Literal(result["s"]["value"]),
                        URIRef(result["p"]["value"]) if result["p"]["type"] == 'uri' else Literal(result["p"]["value"]),
                        URIRef(result["o"]["value"]) if result["o"]["type"] == 'uri' else Literal(result["o"]["value"]),
                        URIRef(result["g"]["value"]) if result["g"]["type"] == 'uri' else Literal(result["g"]["value"])))

        # remove technical triples added by the server to specify editable layers
        for (s, p, o, g) in kb.quads((None, URIRef("http://www.ina.fr/core#is_editable"), None, None)):
                kb.remove((s, p, o, g))
        return True
    else:
        return False


# save or update an analysis to Okapi using the x-trig format
def set_corpus(base_url, corpus_ref, kb, opener):
    url = base_url + "/api/saphir/set_corpus?uri=" + urllib.parse.quote(corpus_ref.toPython()) + "&unlock=true"
    trig_string = kb.graph(corpus_ref.toPython()).serialize(format='trig', base='.', encoding='utf-8')
    req = urllib.request.Request(url, trig_string, {'Content-Type': 'application/trig; charset: UTF-8'})
    op = urllib.request.urlopen(req)
    # opener.addheaders.append(('Content-Type', 'text/plain'))
    # op = opener.open(url, data)
    return op.read().decode()

# save or update a thesaurus to Okapi using the x-trig format
def set_thesaurus(base_url, support_ref, kb, opener):
    url = base_url + "/api/saphir/set_thesaurus?support=" + urllib.parse.quote(support_ref.toPython()) + "&unlock=true"
    trig_string = kb.graph(support_ref.toPython()).serialize(format='trig', base='.', encoding='utf-8')
    req = urllib.request.Request(url, trig_string, {'Content-Type': 'application/trig; charset: UTF-8'})
    op = urllib.request.urlopen(req)
    # opener.addheaders.append(('Content-Type', 'text/plain'))
    # op = opener.open(url, data)
    return op.read().decode()

#get trigs from a SKOS schema and all the belongin concepts and collections.
def get_thesaurus(base_url, support_ref, kb, opener, write="false", format="rdf", support = "false"):
    url = base_url + "/api/saphir/get_thesaurus?support=" + urllib.parse.quote(support_ref.toPython()) \
          + "&write=" + write +"&withSupport=" + support
    response = opener.open(url).read().decode()
    if format == "rdf":
        kb.parse(format='trig', data=response, publicID="http://toDelete/")
        # update the fake uris with toDelete base by the initial empty one
        for (s, p, o, g) in kb.quads((None, URIRef("http://www.ina.fr/core#hasType"), None, None)):
            if o.toPython().startswith("http://toDelete/"):
                kb.add((s, p, URIRef(o.toPython().replace("http://toDelete/", "")), g))
                kb.remove((s, p, o, g))
    else:
        # todo MUST BE completed to handle typed literals !!!
        parsed_json = json.loads(response)
        for result in parsed_json[0]["results"]["bindings"]:
            kb.add((URIRef(result["s"]["value"]) if result["s"]["type"] == 'uri' else Literal(result["s"]["value"]),
                    URIRef(result["p"]["value"]) if result["p"]["type"] == 'uri' else Literal(result["p"]["value"]),
                    URIRef(result["o"]["value"]) if result["o"]["type"] == 'uri' else Literal(result["o"]["value"]),
                    URIRef(result["g"]["value"]) if result["g"]["type"] == 'uri' else Literal(result["g"]["value"])))


def delete_thesaurus(base_url, support_ref, opener):
    url = base_url + "/api/saphir/remove_thesaurus?support=" + urllib.parse.quote(support_ref.toPython()) + "&force=true"
    answer = opener.open(url)
    return answer.read().decode()


# get all graphs form an analysis, write=true
def get_analysis(base_url, analysis_ref, kb, opener, media="false", write="false", scenes="false", labels="false",
                 classes="false", properties="false", format="rdf"):
    url = base_url + "/api/saphir/get_analysis?id="\
          + urllib.parse.quote(analysis_ref.toPython())\
          + "&scenelayer=" + scenes \
          + "&labels=" + labels \
          + "&write=" + write \
          + "&media=" + media \
          + "&medialayer=" + media \
          + "&classes=" + classes \
          + "&properties=" + properties \
          + "&format=" + format
    response = opener.open(url).read().decode()
    if format == "rdf":
        kb.parse(format='trig', data=response, publicID="http://toDelete/")
        # update the fake uris with toDelete base by the initial empty one
        for (s, p, o, g) in kb.quads((None, URIRef("http://www.ina.fr/core#hasType"), None, None)):
            if o.toPython().startswith("http://toDelete/"):
                kb.add((s, p, URIRef(o.toPython().replace("http://toDelete/", "")), g))
                kb.remove((s, p, o, g))
    else:
        # todo MUST BE completed to handle typed literals !!!
        parsed_json = json.loads(response)
        for result in parsed_json[0]["results"]["bindings"]:
            kb.add((URIRef(result["s"]["value"]) if result["s"]["type"] == 'uri' else Literal(result["s"]["value"]),
                    URIRef(result["p"]["value"]) if result["p"]["type"] == 'uri' else Literal(result["p"]["value"]),
                    URIRef(result["o"]["value"]) if result["o"]["type"] == 'uri' else Literal(result["o"]["value"]),
                    URIRef(result["g"]["value"]) if result["g"]["type"] == 'uri' else Literal(result["g"]["value"])))

    # remove technical triples added by the server to specify editable layers
    for (s, p, o, g) in kb.quads((None, URIRef("http://www.ina.fr/core#is_editable"), None, None)):
            kb.remove((s, p, o, g))
    return kb


# cancel the edition of the analysis and give back the lock
def cancel_edit(base_url, analysis_ref, opener):
    url = base_url + "/api/saphir/unlock_resource?resource="\
          + urllib.parse.quote(analysis_ref.toPython())
    answer = opener.open(url)
    return answer

# cancel the edition of the analysis and give back the lock
def load_files(base_url, path, files, opener):
    url = base_url + "/api/saphir/load_files?path="\
         + urllib.parse.quote(path)
    for file in files:
        url += "&files=" + urllib.parse.quote(file)
    answer = opener.open(url).read().decode()
    return answer

# cancel the edition of the analysis and give back the lock
def add_user(base_url, userId, realName, pwd, rights, groups, opener):
    url = base_url + "/api/saphir/admin/addUser2?user="\
         + userId \
         + "&realname=" + urllib.parse.quote(realName)\
         + "&pwd1=" + pwd \
         + "&pwd2=" + pwd

    for right in rights:
        url += "&rights=" + right
    for group in groups:
        url += "&groups=" + group
    answer = opener.open(url)
    return answer

def change_user_passwd(base_url, userId, pwd, opener):
    url = base_url + "/api/saphir/admin/changePassword?user="\
         + userId \
         + "&pwd1=" + pwd \
         + "&pwd2=" + pwd
    answer = opener.open(url)
    return answer


def remove_user(base_url, userId, opener):
    url = base_url + "/api/saphir/admin/delUser?user="\
         + userId
    answer = opener.open(url)
    return answer


def edit_user(base_url, userId, opener, realName=None, rights=None, groups=None):
    url = base_url + "/api/saphir/admin/editUser2?user=" + userId
    if realName is not None:
        url += "&realname=" + urllib.parse.quote(realName)
    if rights is not None:
        for right in rights:
            url += "&rights=" + right
    if groups is not None:
        for group in groups:
            url += "&groups=" + group
    answer = opener.open(url)
    return answer


# save or update an analysis to Okapi using the x-trig format
def set_analysis(base_url, analysis_ref, kb, opener):
    url = base_url + "/api/saphir/set_analysis?uri=" + urllib.parse.quote(analysis_ref.toPython()) + "&unlock=true"
    trig_string = analysis2trig(analysis_ref, kb)
    req = urllib.request.Request(url, trig_string, {'Content-Type': 'application/trig; charset: UTF-8'})
    op = urllib.request.urlopen(req)
    # opener.addheaders.append(('Content-Type', 'text/plain'))
    # op = opener.open(url, data)
    return op

# save or update an analysis to Okapi using the x-trig format
def remove_analysis(base_url, analysis_ref, opener):
    url = base_url + "/api/saphir/remove_analysis?uri=" + urllib.parse.quote(analysis_ref.toPython())
    answer = opener.open(url)
    return answer


def get_model(base_url, model_ref, opener, write="false"):
    url = base_url + "/api/saphir/get_description_model?model=" + urllib.parse.quote(model_ref.toPython()) + "&write=true"
    answer = opener.open(url)
    return answer

# save or update a thesaurus to Okapi using the x-trig format
def set_model(base_url, ontology_ref, kb, opener):
    url = base_url + "/api/saphir/set_description_model?model=" + urllib.parse.quote(ontology_ref.toPython()) + "&unlock=true"
    trig_string = kb.graph(ontology_ref.toPython()).serialize(format='trig', base='.', encoding='utf-8')
    req = urllib.request.Request(url, trig_string, {'Content-Type': 'application/trig; charset: UTF-8'})
    op = urllib.request.urlopen(req)
    return op.read().decode()


def delete_model(base_url, model_ref, opener):
    url = base_url + "/api/saphir/remove_description_model?uri=" + urllib.parse.quote(model_ref.toPython()) + "&force=true"
    answer = opener.open(url)
    return answer


def add_media_dc(base_url, values, source=None):
    if source is not None:
        upload_media(base_url, source, values["identifier"] + ".mp4")
    url = base_url + "/api/saphir/add_media"
    data = urllib.parse.urlencode(values).encode()
    req = urllib.request.Request(url, data=data)
    return urllib.request.urlopen(req).read().decode()


# save or update an analysis to Okapi using the x-trig format
def set_transcription(base_url, media_ref, kb, opener):
    url = base_url + "/api/saphir/set_transcription?uri=" + urllib.parse.quote(media_ref.toPython())
    layer_ref = URIRef(media_ref + '/transcription')
    trig_string = layer2trig(layer_ref, kb)
    print(trig_string)
    req = urllib.request.Request(url, trig_string, {'Content-Type': 'application/trig; charset: UTF-8'})
    op = urllib.request.urlopen(req).read().decode()
    print(str(op))
    # opener.addheaders.append(('Content-Type', 'text/plain'))
    # op = opener.open(url, data)
    return op


# add navigation thumbnails and scenes to a media
def set_thumbnail_and_scene(base_url, media_ref, threshold, opener):
    url = base_url + "/api/saphir/set_thumb_and_scenes?uri=" + urllib.parse.quote(media_ref.toPython()) + "&threshold=" + threshold
    answer = opener.open(url)
    return answer


# add navigation thumbnails and scenes to a media
def backup_database(base_url, opener):
    url = base_url + "/api/saphir/backup_database"
    answer = opener.open(url)
    return answer


def remove_transcription(base_url, media_ref, opener):
    update_query = """
            PREFIX core: <http://www.ina.fr/core#>
            delete {graph ?g {?s ?p ?o}}
            where {
               <""" + media_ref + """/transcription> a core:ASRLayer .
               { graph <""" + media_ref + """/transcription> {?s ?p ?o}.
                 BIND (<""" + media_ref + """/transcription> as ?g)}
               UNION {
                 <""" + media_ref + """/transcription> core:segment ?g .
                 graph ?g {?s ?p ?o}}
            }"""
    answer = sparql_admin(base_url, update_query, opener)
    print(answer)

def upload_media(base_url, source, dest):
    urllib.request.urlretrieve(source, dest),
    url = base_url + "/api/saphir/upload_media?name=" + "/Media/"+ dest
    req = urllib.request.Request(url, data=open(dest, "rb"), headers={'Content-Type': 'video/mp4'})
    return urllib.request.urlopen(req)


# serialize an analysis including layers and segments to x-trig format
def analysis2trig(analysis_ref, kb):
    list_graphs = [kb.graph(analysis_ref.toPython())]
    # collect other graphs belonging to an analysis
    for layer in kb.graph(analysis_ref.toPython()).objects(analysis_ref, URIRef("http://www.ina.fr/core#layer")):
        list_graphs.append(kb.graph(layer.toPython()))
        for segment in kb.graph(layer.toPython()).objects(URIRef(layer), URIRef("http://www.ina.fr/core#segment")):
            list_graphs.append(kb.graph(segment.toPython()))
    aggregate = rdflib.Dataset()
    for g in list_graphs:
        aggregate.add_graph(g)
    trig_string = aggregate.serialize(format='trig', base='.', encoding='utf-8')
    # aggregate.serialize(analysis_ref.toPython().split('/')[-1] + '.trig', format='trig', base='.', encoding='utf-8')
    return trig_string

def layer2trig(layer_ref, kb):
    list_graphs = [kb.graph(layer_ref.toPython())]
    for segment in kb.graph(layer_ref.toPython()).objects(URIRef(layer_ref), URIRef("http://www.ina.fr/core#segment")):
        list_graphs.append(kb.graph(segment.toPython()))
    aggregate = rdflib.Dataset()
    for g in list_graphs:
        aggregate.add_graph(g)
    trig_string = aggregate.serialize(format='trig', base='.', encoding='utf-8')
    # aggregate.serialize(destination='analyse.trig', format='trig', encoding='utf-8')
    return trig_string


def sparql_search(base_url, query, opener, format='application/json'):
    url = base_url + "/api/saphir/sparql_search?query=" + urllib.parse.quote(query)+ "&format=" + format
    response = opener.open(url).read().decode()
    if format == 'application/json':
        return json.loads(response)["results"]["bindings"]
    else:
        return response


def sparql_search_post(base_url, query, opener):
    url = base_url + "/api/saphir/sparql_search"
    req = urllib.request.Request(url, data=query.encode(), headers={'Content-Type': 'application/text; charset: UTF-8'})
    response = urllib.request.urlopen(req).read().decode()
    jsonrep = json.loads(response)
    if "results" in jsonrep:
        return json.loads(response)["results"]["bindings"]
    else:
        return jsonrep


def sparql_construct(base_url, query, opener, format='application/json'):
    url = base_url + "/api/saphir/sparql_search?query=" + urllib.parse.quote(query) + "&format=" + format
    response = opener.open(url).read().decode()
    return response


def sparql_admin(base_url, query, opener):
    url = base_url + "/api/saphir/sparql_admin"
    req = urllib.request.Request(url, data=query.encode(), headers={'Content-Type': 'application/text; charset: UTF-8'})
    #data = urllib.parse.quote(query)
    #req = urllib.request.Request(url, data=data,
    #                            headers={'Content-Type': 'application/text; charset: UTF-8'})
    response = urllib.request.urlopen(req).read().decode()
    return response

def sparql_admin_internal(base_url, query, opener):
    url = base_url + "/api/private/sparql_admin"
    req = urllib.request.Request(url, data=query.encode(), headers={'Content-Type': 'application/text; charset: UTF-8'})
    response = urllib.request.urlopen(req).read().decode()
    return response


def sparql_admin2(base_url, query, opener):
    url = base_url + "/api/saphir/sparql_admin"

    req = urllib.request.Request(url, query, {'Content-Type': 'application/text; charset: UTF-8'})
    response = urllib.request.urlopen(req).read().decode()
    return response


def print_info(kb):
    print("graph has %s statements." % len(kb))
    print("graph has %s graphs." % len(list(kb.graphs())))