if __package__ is None or __package__ == '':
    # uses current directory visibility
    from ...database.database import mongo
else:
    # uses current package visibility
    from database.database import mongo
    #print(__package__)
from bson.objectid import ObjectId
from datetime import datetime
import pymongo

def get_last_case_id(team_id):
    team = mongo.db.get_collection('team_project').find_one({'_id': ObjectId(team_id)})
    case_id = team['case_id']
    return case_id

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

def get_last_case_id_jira(team_project_id):
    team_project = mongo.db.get_collection('registers').find({'team_project_id': ObjectId(team_project_id), 'tool': 'jira'}).sort('case_id', pymongo.DESCENDING)
    if(team_project.count() == 0):
        return 0
    case_id = team_project[0]['case_id']
    return case_id

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

def get_jira_data_info(source_id, team_id):
    source = mongo.db.get_collection('source').find_one({'_id': ObjectId(source_id), 'team_id': team_id})
    url = source['ip_port']
    project = source['name']
    email = source['user']
    token = source['token']
    return url, project, email, token

def get_jira_info_collection(team_id, source_id, last_date_type):
    jira_info = mongo.db.get_collection('jira_info').find_one({'team_id': team_id, 'source_id': source_id})
    last_date_exists = mongo.db.get_collection('jira_info').find_one({'team_id': team_id, 'source_id': source_id, last_date_type: {'$exists': True}})
    return jira_info, last_date_exists

def get_jira_last_date_collection(team_project_id, source_id):
    jira_info = mongo.db.get_collection('jira_last_date').find_one({'team_project_id': team_project_id, 'source_id': source_id})
    last_date_exists = mongo.db.get_collection('jira_last_date').find_one({'team_project_id': team_project_id, 'source_id': source_id, 'last_date': {'$exists': True}})
    return jira_info, last_date_exists

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


def find_tag(id):
    project = mongo.db.get_collection('team_project').find_one({'_id': ObjectId(id)})
    tag = project['tag']
    return tag

def update_events(new, old):
    if new == {} and old == {}:
        return {}
    if new == {}:
        return old
    if old == {}:
        return new
    for key in old.keys():
        if key in new.keys():
            old[key] += new[key]
        else:
            old[key] = new[key]
    return old

def insert_one_jira_info(team_id, project, source_id, total_created, total_updated, new_events):
    mongo.db.get_collection('jira_info').insert_one({
            'team_id': team_id,
            'project': project, 
            'last_date_info': datetime.now(),
            'source_id': source_id, 
            'total_created': total_created,
            'total_updated': total_updated, 
            'total_events': new_events
        })

def get_old_totals(team_id, source_id, jira_info):
    total_created_exists = mongo.db.get_collection('jira_info').find_one({'team_id': team_id, 'source_id': source_id, 'total_created': {'$exists': True}})
    total_updated_exists = mongo.db.get_collection('jira_info').find_one({'team_id': team_id, 'source_id': source_id, 'total_updated': {'$exists': True}})
    if total_created_exists == None:
        old_total_created = 0
    else:
        old_total_created = jira_info['total_created'] 
        
    if total_updated_exists == None:
        old_total_updated = 0
    else:
        old_total_updated = jira_info['total_updated']
    return old_total_created, old_total_updated

def get_old_events(team_id, source_id, jira_info):
    total_events_exists = mongo.db.get_collection('jira_info').find_one({'team_id': team_id, 'source_id': source_id, 'total_events': {'$exists': True}})
    if total_events_exists == None:
        old_events = {}
    else:
        old_events = jira_info['total_events']
    return old_events

def update_totals_jira_info(team_id, source_id, new_total_created, new_total_updated, updated_events):
    mongo.db.get_collection('jira_info').update_one({'team_id': team_id, 'source_id': source_id}, {'$set': {
            'last_date_info': datetime.now(), 
            'total_created': new_total_created,
            'total_updated': new_total_updated, 
            'total_events': updated_events
        }})

def update_last_date_info(team_id, source_id):
    mongo.db.get_collection('jira_info').update_one({'team_id': team_id, 'source_id': source_id}, {'$set': {
            'last_date_info': datetime.now()
        }})

def to_dict(events):
    dic = {}
    for event in events:
        dic[event['field']] = event['count']
    return dic

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
    print(developers)
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
        created_per = round(developer_events['Create issue']/total_created*100)
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


'''def get_percentages2(team_id, source_id):
    participation = mongo.db.get_collection('jira_participation').find({'team_id': team_id, 'source_id': source_id})
    response = json_util.dumps(participation)
    return response'''

def translate_name(db_developers, part_name):
    for dev in db_developers:
        if(dev['jira'] == part_name):
            return dev['name'], dev
    return None, None

def get_percentages_db_2(team_id, source_id):
    developers = mongo.db.get_collection('jira_participation').find({'team_id': team_id, 'source_id': source_id})
    developers_db = mongo.db.get_collection('team').find_one({'_id': ObjectId(team_id)})
    developers_db_names = []
    if(developers_db != None):
        developers_db = developers_db['developers']
        print(developers_db)
        for dev in developers_db:
            developer = mongo.db.get_collection('developer').find_one({'_id': ObjectId(dev)})
            developers_db_names.append(developer)
    participation = {}
    participation['Created issues'] = []
    participation['Updated issues'] = []
    if(developers.count() != 0):
        for event in developers[0]['events_per'].keys():
            participation[event] = []
    for developer in developers:
        name, dev = translate_name(developers_db_names, developer['name'])
        if(name == None):
            name = developer['name']
        else:
            developers_db_names.remove(dev)
        for e in developer['events_per'].keys():
            participation[e].append([name, developer['events_per'][e]])
        participation['Created issues'].append([name, developer['created_per']])
        participation['Updated issues'].append([name, developer['updated_per']])
    for developer in developers_db_names:
        name = developer['name']
        for e in participation.keys():
            participation[e].append([name, 0])
    return participation

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

def get_totals(team_id, source_id):
    totals = mongo.db.get_collection('jira_info').find_one({'team_id': team_id, 'source_id': source_id})
    totals_send = {}
    if totals != None:
        totals_send['total_created'] = totals['total_created']
        totals_send['total_updated'] = totals['total_updated']
        for key in totals['total_events'].keys():
            totals_send[key] = totals['total_events'][key]
    return totals_send

def get_tag_dict(team_id):
    team = mongo.db.get_collection('team').find_one({'_id': ObjectId(team_id)})
    projects_id = team['projects']
    tag_dict = {}
    for id in projects_id:
        project = mongo.db.get_collection('team_project').find_one({'_id': ObjectId(id)})
        tag = project['tag']
        tag_dict[tag] = id
    return tag_dict

def get_source_id_db(team_id):
    source_id = mongo.db.get_collection('team').find_one({'_id': ObjectId(team_id)})['jira_source']
    return source_id

#################################################
############### PRODUCTIVITY ####################
#################################################

def get_tag(team_project_id):
    project = mongo.db.get_collection('team_project').find_one({'_id': ObjectId(team_project_id)})
    tag = project['tag']
    return tag

def get_prod_docs(team_id, tag):
    docs = mongo.db.get_collection('jira_project_info').find({'team_id': team_id, 'tag': tag, 'field': 'resolution'})
    if docs.count() != 0:
        return docs
    return None