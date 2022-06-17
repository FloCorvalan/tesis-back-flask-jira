from flask import request, Response, Blueprint
from bson import json_util
from .methods import *

jira = Blueprint('jira', __name__)

###################################################################
########################## REGISTERS ##############################
###################################################################

# Obtiene los registros para Process Mining de Jira
@jira.route('/jira', methods=['POST'])
def get_registers():
    team_id = request.json['team_id']
    source_id = get_source_id(team_id)
    res = get_jira_data(team_id, source_id)
    return res

###################################################################
###################################################################
###################################################################
#------------------------------------------------------------------


###################################################################
################### ALL PARTICIPATION PROCESS #####################
###################################################################

# Obtiene la participacion de los integrantes del equipo
#obteniendo previamente la informacion 
#y calculando los porcentajes
@jira.route('/jira/participation', methods=['POST'])
def get_participation():
    team_id = request.json['team_id']
    source_id = get_source_id(team_id)
    # Se obtiene la informacion sobre la participacion de los desarrolladores
    get_participation_info(team_id, source_id)

    # Se obtiene la informacion sobre el proyecto (totales)
    calculate_totals(team_id, source_id)

    # Se calculan los porcentajes nuevamente
    calculate_percentages(team_id, source_id)
    
    # Independientemente si hay nuevos cambios, se obtiene los porcentajes para mostrarlos
    response = get_percentages(team_id, source_id)
    return response

###################################################################
###################################################################
###################################################################
#------------------------------------------------------------------


###################################################################
################### ALL PRODUCTIVITY PROCESS ######################
###################################################################

# Se obtiene la productividad grupal
@jira.route('/jira/prod', methods=['POST'])
def get_jira_productivity():
    team_id = request.json['team_id']
    source_id = get_source_id(team_id)
    prod = get_prod_info(team_id, source_id)
    response = json_util.dumps(prod)
    return Response(response, mimetype='application/json')

###################################################################
###################################################################
###################################################################
#------------------------------------------------------------------