if __package__ is None or __package__ == '':
    # uses current directory visibility
    from ...database.database import mongo
else:
    # uses current package visibility
    from database.database import mongo
from bson.objectid import ObjectId
from datetime import datetime
import pymongo

# Se obtiene el ultimo case id de un proyecto
def get_last_case_id(team_id):
    team = mongo.db.get_collection('team_project').find_one({'_id': ObjectId(team_id)})
    case_id = team['case_id']
    return case_id

# Se buscan los timestamps minimo y maximo segun case id (los limites para decidir a que case id
# pertenece el nuevo registro)
def search_timestamps(case_id, ant, team_project_id):
    team_project_min = mongo.db.get_collection('registers').find({'team_project_id': team_project_id, 'case_id': ant}).sort('timestamp', pymongo.DESCENDING)
    team_project_max = mongo.db.get_collection('registers').find({'team_project_id': team_project_id, 'case_id': case_id}).sort('timestamp', pymongo.DESCENDING)
    if(team_project_max.count() > 0):
        max = team_project_max[0]['timestamp']
    else:
        max = 0
    if(team_project_min.count() > 0):
        min = team_project_min[0]['timestamp']
    else:
        min = 0
    return min, max

# Se obtiene el ultimo case id asociado a un registro de Jira
def get_last_case_id_jira(team_project_id):
    team_project = mongo.db.get_collection('registers').find({'team_project_id': ObjectId(team_project_id), 'tool': 'jira'}).sort('case_id', pymongo.DESCENDING)
    if(team_project.count() == 0):
        return 0
    case_id = team_project[0]['case_id']
    return case_id

# Se guarda un registro de Jira para process mining
def save_register(team_id, case_id, activity, time, author, iss, i):
    if i == None:
            mongo.db.get_collection('registers').insert_one({
                                    'team_project_id': team_id,
                                    'case_id': case_id,
                                    'activity': activity, 
                                    'timestamp': time,
                                    'resource': author,
                                    'tool': 'jira',
                                    'userName': author,
                                    'issue': iss
                                })
    else:
        mongo.db.get_collection('registers').insert_one({
                                    'team_project_id': team_id,
                                    'case_id': case_id,
                                    'activity': activity, 
                                    'timestamp': time,
                                    'resource': author,
                                    'tool': 'jira',
                                    'userName': author,
                                    'issue': iss, 
                                    'field': i['field']
                                })

# Se obtiene la informacion de la fuenta de informacion de Jira
def get_jira_data_info(source_id, team_id):
    source = mongo.db.get_collection('source').find_one({'_id': ObjectId(source_id), 'team_id': team_id})
    url = source['ip_port']
    project = source['name']
    email = source['user']
    token = source['token']
    return url, project, email, token

# Se obtiene informacion de la coleccion jira_info para un equipo
def get_jira_info_collection(team_id, source_id, last_date_type):
    jira_info = mongo.db.get_collection('jira_info').find_one({'team_id': team_id, 'source_id': source_id})
    last_date_exists = mongo.db.get_collection('jira_info').find_one({'team_id': team_id, 'source_id': source_id, last_date_type: {'$exists': True}})
    return jira_info, last_date_exists

# Se obtiene informacion de la coleccion jira_last_date para un proyecto
def get_jira_last_date_collection(team_project_id, source_id):
    jira_info = mongo.db.get_collection('jira_last_date').find_one({'team_project_id': team_project_id, 'source_id': source_id})
    last_date_exists = mongo.db.get_collection('jira_last_date').find_one({'team_project_id': team_project_id, 'source_id': source_id, 'last_date': {'$exists': True}})
    return jira_info, last_date_exists

# Se actualiza o se crea un documento en la coleccion jira_last_date
def update_last_date(jira_info, team_project_id, team_id, project, source_id):
    # Si no existe, se crea
    if jira_info == None:
        mongo.db.get_collection('jira_last_date').insert_one({
            'team_id': team_id,
            'team_project_id': team_project_id,
            'project': project, 
            'last_date': datetime.now(),
            'source_id': source_id
        })
    # Se actualiza el last_date (ultima fecha de revision)
    else:
        mongo.db.get_collection('jira_last_date').update_one({'team_project_id': team_project_id, 'source_id': source_id}, {'$set': {
            'last_date': datetime.now()
        }})

# Se guarda un documento en la coleccion jira_project_info
def save_jira_project_info(team_id, author, iss, i, project, source_id, timestamp, story_points, tag):
    if type(i) == str:
            mongo.db.get_collection('jira_project_info').insert_one({
                                'team_id': team_id,
                                'userName': author,
                                'issue': iss, 
                                'field': i,
                                'name': project,
                                'source_id': source_id, 
                                'timestamp': timestamp
                            })
    else:
        mongo.db.get_collection('jira_project_info').insert_one({
                                'team_id': team_id,
                                'userName': author,
                                'issue': iss, 
                                'field': i['field'],
                                'name': project,
                                'source_id': source_id,
                                'timestamp': timestamp,
                                'story_points': story_points, 
                                'tag': tag
                            })

# Se actualiza la fecha de revision de participacion
def update_last_date_part(jira_info, team_id, project, source_id):
    if jira_info == None:
        mongo.db.get_collection('jira_info').insert_one({
            'team_id': team_id,
            'project': project, 
            'last_date_part': datetime.now(),
            'source_id': source_id, 
        })
    # Si no hay cambios solo se actualiza la ultima fecha de revision
    else:
        mongo.db.get_collection('jira_info').update_one({'team_id': team_id, 'source_id': source_id}, {'$set': {
            'last_date_part': datetime.now()
        }})

# Se obtiene el tag de Jira para un proyecto
def find_tag(id):
    project = mongo.db.get_collection('team_project').find_one({'_id': ObjectId(id)})
    tag = project['tag']
    return tag

# Se actualizan los totales de las issues creadas, las actualizaciones realizadas a las issues
# y los eventos
def update_totals_jira_info(team_id, source_id, new_total_created, new_total_updated, updated_events):
    mongo.db.get_collection('jira_info').update_one({'team_id': team_id, 'source_id': source_id}, {'$set': {
            'last_date_info': datetime.now(), 
            'total_created': new_total_created,
            'total_updated': new_total_updated, 
            'total_events': updated_events
        }})

# Se crea un diccionario de eventos con su cuenta
def to_dict(events):
    dic = {}
    for event in events:
        dic[event['field']] = event['count']
    return dic

# Se calculan los totales de issues creadas, actualizaciones a las issues y eventos
def calculate_totals_db(team_id, source_id):
    totals = mongo.db.get_collection('jira_project_info').aggregate([
        {
            '$match': {
                'team_id': team_id,
                'source_id': source_id, 
            }
        },
        {
            '$group': {
                '_id': '$field',
                'count': {'$sum':1}
            }
        },
    ])
    return totals

# Se calculan los porcentajes de la participacion en Jira para cada desarrollador
def calculate_percentages_db(team_id, source_id):
    developers = mongo.db.get_collection('jira_project_info').aggregate([
        {
            '$match': {
                'team_id': team_id,
                'source_id': source_id, 
            }
        },
        {
            '$group': {
                '_id': {
                    'userName': '$userName', 
                    'field': '$field'
                },
                'count': {'$sum':1}
            }
        },
        {
            '$group': {
                '_id': '$_id.userName',
                'events': {
                    '$push': {
                        'field': '$_id.field',
                        'count': '$count'
                    }
                }
            }
        }
    ])
    jira_project = mongo.db.get_collection('jira_info').find_one({'team_id': team_id, 'source_id': source_id})
    total_events = jira_project['total_events']
    total_created = jira_project['total_created']
    total_updated = 0
    for key in total_events.keys():
        total_updated += total_events[key]
    developer_dic = {}
    for developer in developers:
        developer_events = to_dict(developer['events'])
        for key in total_events.keys():
            if key in developer_events.keys():
                developer_dic[key] = round(developer_events[key]/total_events[key]*100)
            else:
                developer_dic[key] = 0
        if 'Create issue' in developer_events.keys():
            created_per = round(developer_events['Create issue']/total_created*100)
        else: 
            created_per = 0
        updated = 0
        for key in developer_dic.keys():
            if key in developer_events.keys():
                updated += developer_events[key]
        updated_per = round(updated/total_updated*100)
        dev = mongo.db.get_collection('jira_participation').find_one({'team_id': team_id, 'source_id': source_id, 'name': developer['_id']})
        if dev == None:
            mongo.db.get_collection('jira_participation').insert_one({
                'team_id': team_id, 
                'source_id': source_id, 
                'name': developer['_id'], 
                'events_per': developer_dic, 
                'created_per': created_per, 
                'updated_per': updated_per
            })
        else:
            mongo.db.get_collection('jira_participation').update_one({'team_id': team_id, 'source_id': source_id, 'name': developer['_id']}, {'$set': {
                'events_per': developer_dic,
                'created_per': created_per, 
                'updated_per': updated_per
            }})
        developer_dic = {}
        updated = 0
    return

# Se obtienen los porcentajes de participacion
def get_percentages_db(team_id, source_id):
    developers = mongo.db.get_collection('jira_participation').find({'team_id': team_id, 'source_id': source_id})
    participation = {}
    participation['Created issues'] = []
    participation['Updated issues'] = []
    for event in developers[0]['events_per'].keys():
        participation[event] = []
    for developer in developers:
        for e in developer['events_per'].keys():
            participation[e].append([developer['name'],developer['events_per'][e]])
        participation['Created issues'].append([developer['name'],developer['created_per']])
        participation['Updated issues'].append([developer['name'],developer['updated_per']])
    return participation

# Se obtienen los totales de las issues creadas, las actualizaciones de las issues y los eventos
def get_totals(team_id, source_id):
    totals = mongo.db.get_collection('jira_info').find_one({'team_id': team_id, 'source_id': source_id})
    totals_send = {}
    if totals != None:
        totals_send['total_created'] = totals['total_created']
        totals_send['total_updated'] = totals['total_updated']
        for key in totals['total_events'].keys():
            totals_send[key] = totals['total_events'][key]
    return totals_send

# Se obtiene un diccionario con los tags segun proyecto
def get_tag_dict(team_id):
    team = mongo.db.get_collection('team').find_one({'_id': ObjectId(team_id)})
    projects_id = team['projects']
    tag_dict = {}
    for id in projects_id:
        project = mongo.db.get_collection('team_project').find_one({'_id': ObjectId(id)})
        tag = project['tag']
        tag_dict[tag] = id
    return tag_dict

# Se obtiene el id del source de jira segun el equipo por su id
def get_source_id_db(team_id):
    source_id = mongo.db.get_collection('team').find_one({'_id': ObjectId(team_id)})['jira_source']
    return source_id
