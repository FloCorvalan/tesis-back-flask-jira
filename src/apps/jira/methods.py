import requests
import json
from bson import json_util
from datetime import datetime
from requests.auth import HTTPBasicAuth
from .db_methods import *

# Para obtener informacion desde una url con autenticacion
def get_jira(url, email, token):
    # Se crea el objecto de autenticacion
    auth = HTTPBasicAuth(email,
                        token)

    headers = {
        "Accept": "application/json"
    }

    # Se hace la consulta
    response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth
    )
    return response.text

# Para obtener el case id que se debe asignar
def get_actual_case_id(team_project_id, last_case_id, timestamp):
    last_case_id_jira = get_last_case_id_jira(team_project_id)
    cont = last_case_id_jira
    case_id = None
    while(cont < last_case_id):
        ant = cont - 1
        ini, fin = search_timestamps(cont, ant, team_project_id)
        if(timestamp > ini and timestamp <= fin):
            case_id = cont
            return case_id
        cont += 1
    ini, fin = search_timestamps(last_case_id, last_case_id - 1, team_project_id)
    if(timestamp > ini):
        return last_case_id
    return 0

# Para obtener los registros sobre los changelogs de las issues
def analize_changelog(data, team_project_id, last_date):
    data_form = json.loads(json.dumps(json.loads(data),
						indent=4,
						separators=(",", ": ")))
    tag_db = find_tag(team_project_id)
    for issue in data_form['issues']:
        iss = issue['key']
        histories = issue['changelog']['histories']
        tag = issue['fields']['summary'].split(' ')[0]
        if histories != [] and tag == tag_db:
            for item in histories:
                author = item['author']['displayName']
                time = datetime.strptime(item['created'].split(".")[0], "%Y-%m-%dT%H:%M:%S").timestamp()
                items = item['items']
                # Si last_date es None significa que no se ha analizado antes
                #por lo que se analiza independiente de la fecha de actualizacion (changelog)
                if last_date == None:
                    for i in items:
                        if i['field'] == 'status' and i['toString'] != 'Done':
                            # Si es cambio de estado de una issue se guarda como registro
                            activity = 'SEGUIMIENTO_' + i['toString']
                            last_case_id = get_last_case_id(team_project_id)
                            case_id = get_actual_case_id(team_project_id, last_case_id, time)
                            save_register(team_project_id, case_id, activity, time, author, iss, i)
                # Si last_date existe, se ha analizado antes y se debe considerar solo las
                #actualizaciones que ocurrieron despues del ultimo analisis
                elif datetime.strptime(str(last_date).split(".")[0], "%Y-%m-%d %H:%M:%S").timestamp() < time: # Se compara en segundos
                    for i in items:
                        if i['field'] == 'status' and i['toString'] != 'Done':
                            # Si es cambio de estado de una issue se guarda como registro
                            activity = 'SEGUIMIENTO_' + i['toString']
                            last_case_id = get_last_case_id(team_project_id)
                            case_id = get_actual_case_id(team_project_id, last_case_id, time)
                            save_register(team_project_id, case_id, activity, time, author, iss, i)
    return

# Para obtener los registros de las issues creadas
def analize_created(data, team_project_id, last_date):
    data_form = json.loads(json.dumps(json.loads(data),
						indent=4,
						separators=(",", ": ")))
    tag_db = find_tag(team_project_id)
    for issue in data_form['issues']:
        iss = issue['key']
        tag = issue['fields']['summary'].split(' ')[0]
        time = datetime.strptime(issue['fields']['created'].split(".")[0], "%Y-%m-%dT%H:%M:%S").timestamp()
        author = issue['fields']['creator']['displayName']
        if last_date == None:
            if tag == tag_db:
                last_case_id = get_last_case_id(team_project_id)
                case_id = get_actual_case_id(team_project_id, last_case_id, time)
                save_register(team_project_id, case_id, 'PLANIFICACION', time, author, iss, None)
        elif datetime.strptime(str(last_date).split(".")[0], "%Y-%m-%d %H:%M:%S").timestamp() < time: # Se compara en segundos
            if tag == tag_db:
                last_case_id = get_last_case_id(team_project_id)
                case_id = get_actual_case_id(team_project_id, last_case_id, time)
                save_register(team_project_id, case_id, 'PLANIFICACION', time, author, iss, None)

# Se obtienen los registros (de Jira) para process mining
def get_jira_data(team_id, source_id):
    # Se obtienen las credenciales y datos de la fuenta
    url, project, email, token = get_jira_data_info(source_id, team_id)

    # Se buscan los team project id asociados al proyecto
    tag_dict = get_tag_dict(team_id)
    for team_project in tag_dict.keys():
        team_project_id = tag_dict[team_project]
        jira_info, last_date_exists = get_jira_last_date_collection(team_project_id, source_id)
        if jira_info == None or last_date_exists == None:
            #### Se analizan todos los datos existentes
            # Se registran las issues creadas
            # Se registran los cambios de status en las issues
            last_date = None
            changelog_url = url + '/rest/api/2/search?jql=project=' + project + '&expand=changelog'
            created_url = url + '/rest/api/2/search?jql=project=' + project + '&maxResults=500&startAt=0&fields=key&fields=created&fields=creator&fields=summary'
        else:
            # Si se han analizado datos ya
            # Se genera una lista de las issues creadas y actualizadas despues de la ultima
            #fecha de revision
            # Se registran las issues credas despues de es fecha
            # Se registran los cambios de status en las issues actualizadas
            last_date = jira_info['last_date']
            last_date_str = str(jira_info['last_date']).split(" ")[0]
            changelog_url = url + '/rest/api/2/search?jql=(updated>' + last_date_str + ')AND(project=' + project + ')&expand=changelog'
            created_url = url + '/rest/api/2/search?jql=(created>' + last_date_str + ')AND(project=' + project + ')&maxResults=500&startAt=0&fields=key&fields=created&fields=creator&fields=summary'

        data_changelog = get_jira(changelog_url, email, token)
        analize_changelog(data_changelog, team_project_id, last_date)
        data_created = get_jira(created_url, email, token)
        analize_created(data_created, team_project_id, last_date)

        update_last_date(jira_info, team_project_id, team_id, project, source_id) # Si no existe, la crea


###################################
########## PARTICIPACION ##########
###################################

# Se obtiene la informacion del proyecto sobre las actualizaciones
def get_project_info_changelog(data, team_id, last_date, project, source_id):
    data_form = json.loads(json.dumps(json.loads(data),
						indent=4,
						separators=(",", ": ")))
    if data_form['issues'] == []:
        return 0
    for issue in data_form['issues']:
        iss = issue['key']
        histories = issue['changelog']['histories']
        story_points = issue['fields']['customfield_10016']
        tag = issue['fields']['summary'].split(' ')[0]
        if histories != []:
            for item in histories:
                author = item['author']['displayName']
                time = datetime.strptime(item['created'].split(".")[0], "%Y-%m-%dT%H:%M:%S").timestamp()
                items = item['items']
                # Si last_date es None significa que no se ha analizado antes
                #por lo que se analiza independiente de la fecha de actualizacion (changelog)
                if last_date == None:
                    for i in items:
                        save_jira_project_info(team_id, author, iss, i, project, source_id, time, story_points, tag)
                # Si last_date existe, se ha analizado antes y se debe considerar solo las
                #actualizaciones que ocurrieron despues del ultimo analisis
                elif datetime.strptime(str(last_date).split(".")[0], "%Y-%m-%d %H:%M:%S").timestamp() < time: # Se compara en segundos
                    for i in items:
                        save_jira_project_info(team_id, author, iss, i, project, source_id, time, story_points, tag)
    return 1

# Se obtiene la informacion del proyecto sobre las issues creadas
def get_project_info_created(data, team_id, last_date, project, source_id):
    data_form = json.loads(json.dumps(json.loads(data),
						indent=4,
						separators=(",", ": ")))
    if data_form['issues'] == []:
        return 0
    for issue in data_form['issues']:
        iss = issue['key']
        time = datetime.strptime(issue['fields']['created'].split(".")[0], "%Y-%m-%dT%H:%M:%S").timestamp()
        author = issue['fields']['creator']['displayName']
        if last_date == None:
            save_jira_project_info(team_id, author, iss, 'Create issue', project, source_id, time, None, None)
        elif datetime.strptime(str(last_date).split(".")[0], "%Y-%m-%d %H:%M:%S").timestamp() < time: # Se compara en segundos
            save_jira_project_info(team_id, author, iss, 'Create issue', project, source_id, time, None, None)
    return 1


# Se obtiene la informacion sobre la participacion de el source de Jira para un team_id
def get_participation_info(team_id, source_id):
    # Se obtienen las credenciales y datos de la fuente
    url, project, email, token = get_jira_data_info(source_id, team_id)

    jira_info, last_date_part_exists = get_jira_info_collection(team_id, source_id, 'last_date_part')
    if jira_info == None or last_date_part_exists == None:
        last_date = None
        #### Se analizan todos los datos existentes
        changelog_url = url + '/rest/api/2/search?jql=project=' + project + '&expand=changelog'
        created_url_info = url + '/rest/api/2/search?jql=project=' + project + '&maxResults=500&startAt=0&fields=key&fields=created&fields=creator'

    else:
        # Si se han analizado datos ya
        # Se genera una lista de las issues creadas y actualizadas despues de la ultima
        last_date = jira_info['last_date_part']
        last_date_part = str(jira_info['last_date_part']).split(" ")[0]
        changelog_url = url + '/rest/api/2/search?jql=(updated>' + last_date_part + ')AND(project=' + project + ')&expand=changelog'
        created_url_info = url + '/rest/api/2/search?jql=(created>' + last_date_part + ')AND(project=' + project + ')&maxResults=500&startAt=0&fields=key&fields=created&fields=creator'

    # Se obtienen los datos para obtener la informacion de las actualizaciones
    data_changelog = get_jira(changelog_url, email, token)

    # Se obtienen los datos para obtener la informacion sobre las issues creadas
    data_created_info = get_jira(created_url_info, email, token)

    # Se guarda en la bd la informacion del proyecto
    changelog_info = get_project_info_changelog(data_changelog, team_id, last_date, project, source_id)
    created_info = get_project_info_created(data_created_info, team_id, last_date, project, source_id)
    
    # Si jira_info es None, significa que no se ha creado la instancia (para ese team_id
    # con ese source_id)
    update_last_date_part(jira_info, team_id, project, source_id) # Si no existe, la crea
    if changelog_info == 0 and created_info == 0:
        return {'message': 'Unchanged data'}
    return {'message': 'Successfully extracted data'}

# Se calculan los porcentajes totales de las issues creadas, actualizaciones a las issues y de los eventos
def calculate_totals(team_id, source_id):
    totals = calculate_totals_db(team_id, source_id)
    updated_events = {}
    new_total_updated = 0
    for t in totals:
        if t['_id'] != 'Create issue':
            updated_events[t['_id']] = t['count']
            new_total_updated += t['count']
        else:
            new_total_created = t['count']
    update_totals_jira_info(team_id, source_id, new_total_created, new_total_updated, updated_events)

# Se calculan los porcentajes de participacion
def calculate_percentages(team_id, source_id):
    calculate_percentages_db(team_id, source_id)

# Se obtienen los porcentajes de participacion de los desarrolladores y los totales de cada metrica
# (issues creadas, actualizaciones a las issues y eventos)
def get_percentages(team_id, source_id):
    developers = get_percentages_db(team_id, source_id)
    totals = get_totals(team_id, source_id)

    participation = {
        'developers': developers,
        'totals': totals
    }

    response = json_util.dumps(participation)
    return response

# Se obtiene el id del source de jira de un equipo segun su id
def get_source_id(team_id):
    source_id = get_source_id_db(team_id)
    return source_id


#################################################
############### PRODUCTIVITY ####################
#################################################

# Se obtiene el id del tablero/proyecto de Jira a partir del json obtenido
def get_board_id(board_info):
    data_form = json.loads(json.dumps(json.loads(board_info),
						indent=4,
						separators=(",", ": ")))
    board_id = data_form['values'][0]['id']
    return board_id

# Se formatea la informacion de velocidad (story points estimados vs completados)
# para enviarlos al frontend
def format_vel_info(vel_info):
    data_form = json.loads(json.dumps(json.loads(vel_info),
						indent=4,
						separators=(",", ": ")))

    sprints = []
    names = []
    for sprint in data_form['sprints']:
        sprints.append(sprint['id'])
        names.append(sprint['name'])
    
    sprint_dic = {}
    i = 0
    while i < len(sprints):
        sprint_dic[sprints[i]] = {
            'name': names[i],
            'estimated': data_form['velocityStatEntries'][str(sprints[i])]['estimated']['value'],
            'completed': data_form['velocityStatEntries'][str(sprints[i])]['completed']['value']
        }
        i += 1

    return sprint_dic

# Se obtiene la informacion de productividad grupal desde Jira
def get_prod_info(team_id,  source_id):

    # Se obtienen las credenciales y datos de la fuenta
    url, project, email, token = get_jira_data_info(source_id, team_id)

    # Se obtiene el id del tablero del proyecto
    url_id = url + "/rest/agile/1.0/board?projectKeyOrId=" + project
    board_info = get_jira(url_id, email, token)
    board_id = get_board_id(board_info)

    vel_url = url + "/rest/greenhopper/1.0/rapid/charts/velocity?rapidViewId=" + str(board_id)
    vel_info = get_jira(vel_url, email, token)

    velocity = format_vel_info(vel_info)

    return velocity

# Para obtener los ids de los sprints
def get_id_info(info):
    data_form = json.loads(json.dumps(json.loads(info),
						indent=4,
						separators=(",", ": ")))

    ids = []
    for sprint in data_form['sprints']:
        ids.append(sprint['id'])
    
    return ids


# Para obtener los timestamps minimo y maximo entre los sprints desde los ids
def get_dates_info(base_url, ids, email, token):

    start_timestamps_list = []
    end_timestamps_list = []

    for i in ids:
        url = base_url + str(i)
        info = get_jira(url, email, token)

        data_form = json.loads(json.dumps(json.loads(info),
						indent=4,
						separators=(",", ": ")))
        
        start_date = data_form['startDate']
        end_date = data_form['endDate']

        start_timestamp = datetime.strptime(start_date.split(".")[0], "%Y-%m-%dT%H:%M:%S").timestamp()
        end_timestamp = datetime.strptime(end_date.split(".")[0], "%Y-%m-%dT%H:%M:%S").timestamp()

        start_timestamps_list.append(start_timestamp)
        end_timestamps_list.append(end_timestamp)

    start_send = -1
    end_send = -1

    if len(start_timestamps_list) != 0 and len(end_timestamps_list) != 0:
        start_send = min(start_timestamps_list)
        end_send = max(end_timestamps_list)

    return start_send, end_send


# Para obtener los timestamps minimo y maximo entre los sprints
def get_prod_names_info(team_id,  source_id):

    # Se obtienen las credenciales y datos de la fuenta
    url, project, email, token = get_jira_data_info(source_id, team_id)

    # Se obtiene el id del tablero del proyecto
    url_id = url + "/rest/agile/1.0/board?projectKeyOrId=" + project
    board_info = get_jira(url_id, email, token)
    board_id = get_board_id(board_info)

    ids_url = url + "/rest/greenhopper/1.0/rapid/charts/velocity?rapidViewId=" + str(board_id)
    ids_info = get_jira(ids_url, email, token)

    ids = get_id_info(ids_info)

    sprint_url = url + '/rest/agile/1.0/sprint/'

    start_send, end_send = get_dates_info(sprint_url, ids, email, token)

    timestamps = {
        'start_timestamp': start_send, 
        'end_timestamp': end_send
    }

    return timestamps
    