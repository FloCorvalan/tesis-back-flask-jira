from re import S
from flask import request, jsonify, Response, Blueprint
from bson import json_util
from bson.objectid import ObjectId
from numpy import source
from .methods import *

jira = Blueprint('jira', __name__)

###################################################################
########################## REGISTERS ##############################
###################################################################

# Obtiene los registros para Process Mining de Jira
@jira.route('/jira', methods=['POST'])
def get_registers():
    team_id = request.json['team_id']
    #source_id = request.json['source_id']
    #team_id = '6241fad36d714f635bafbc9f'
    source_id = get_source_id(team_id)
    res = get_jira_data(team_id, source_id)
    return res

###################################################################
###################################################################
###################################################################
#------------------------------------------------------------------

# Obtiene la informacion sobre la participacion en el proyecto
@jira.route('/jira/info', methods=['GET'])
def get_jira_project_info():
    #team_id = request.json['team_id']
    #source_id = request.json['source_id']
    team_id = '6241fad36d714f635bafbc9f'
    source_id = '6245c4a05d2241ee765cccad'
    res = get_project_info(team_id, source_id)
    return res

###################################################################
################### ALL PARTICIPATION PROCESS #####################
###################################################################

# Obtiene la participacion de los integrantes del equipo
#obteniendo previamente la informacion 
#y calculando los porcentajes
@jira.route('/jira/participation', methods=['POST'])
def get_participation():
    team_id = request.json['team_id']
    #source_id = request.json['source_id']
    #team_id = '6241fad36d714f635bafbc9f'
    source_id = get_source_id(team_id)
    # Se obtiene la informacion sobre la participacion de los desarrolladores
    get_participation_info(team_id, source_id)

    # Se obtiene la informacion sobre el proyecto (totales)
    calculate_totals(team_id, source_id)

    # Se calculan los porcentajes nuevamente
    calculate_percentages(team_id, source_id)
    
    # Independientemente si hay nuevos cambios, se obtiene los porcentajes para mostrarlos
    response = get_percentages(team_id, source_id)
    return Response(response, 'application/json')

###################################################################
###################################################################
###################################################################
#------------------------------------------------------------------

@jira.route('/jira-test', methods=['GET'])
def test2():
    team_id = '62702b09e2115db94f9d2d41'
    source_id = '62702d03a987d71a15d3ed0b'
    total = mongo.db.get_collection('jira_project_info').aggregate([
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
    response = json_util.dumps(total)
    return Response(response, 'application/json')

@jira.route('/jira-test-3', methods=['GET'])
def test3():
    team_id = '62702b09e2115db94f9d2d41'
    source_id = '62702d03a987d71a15d3ed0b'
    calculate_totals(team_id, source_id)
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
    response = json_util.dumps(developers)
    return Response(response, 'application/json')

###################################################################
################### ALL PRODUCTIVITY PROCESS ######################
###################################################################

@jira.route('/jira/prod', methods=['POST'])
def get_jira_productivity():
    team_id = request.json['team_id']
    #source_id = request.json['source_id']
    #team_id = '6241fad36d714f635bafbc9f'
    #team_project_id = '625f1e47bffb6a90d59d3e06'
    source_id = get_source_id(team_id)
    prod = get_prod_info(team_id, source_id)
    response = json_util.dumps(prod)
    return Response(response, mimetype='application/json')

###################################################################
###################################################################
###################################################################
#------------------------------------------------------------------