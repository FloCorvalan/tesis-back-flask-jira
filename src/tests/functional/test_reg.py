from json import loads
from bson import ObjectId

def test_get_registers_jira(test_client):
    'HU6 - Escenario 1'
    'Dado que se ha generado un dashboard asociado a un equipo de desarrollo'
    'Cuando el líder de proyectos selecciona un proyecto'
    'Entonces el sistema genera un modelo de proceso en notación BPMN a partir de los datos extraídos desde las fuentes de información asociadas al proyecto'

    team_id = '629f6ff71785c7fd81349a17'

    client, mongo = test_client

    response = client.post('/jira', json={
        'team_id': team_id, 
    })

    data_str = response.data.decode('utf8')

    data = loads(data_str)

    assert response.status_code == 200