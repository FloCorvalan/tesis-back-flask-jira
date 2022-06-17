from json import loads

def test_team_productivity(test_client):
    'HU8 - Escenario 1'
    'Dado que existe información sobre al menos 1 Sprint'
    'Cuando el líder de proyectos accede al dashboard asociado a un equipo de desarrollo'
    'Y se ha generado el dashboard a partir de los datos extraídos de las fuentes de información registradas'
    'Entonces el sistema entrega información sobre la productividad grupal de los desarrolladores'

    team_id = '629f6ff71785c7fd81349a17'

    client, mongo = test_client

    response = client.post('/jira/prod', json={
        'team_id': team_id, 
    })

    data_str = response.data.decode('utf8')

    data = loads(data_str)

    assert response.status_code == 200

    assert '24' in data.keys()
    assert '22' in data.keys()
    
    assert 'name' in data['24'].keys()
    assert 'estimated' in data['24'].keys()
    assert 'completed' in data['24'].keys()

    assert 'name' in data['22'].keys()
    assert 'estimated' in data['22'].keys()
    assert 'completed' in data['22'].keys()

    assert data['24']['name'] == 'Tablero Sprint 2'
    assert data['24']['estimated'] == 35.0
    assert data['24']['completed'] == 35.0

    assert data['22']['name'] == 'Tablero Sprint 1'
    assert data['22']['estimated'] == 20.0
    assert data['22']['completed'] == 20.0
