from json import loads
from bson import ObjectId

def test_participation_jira(test_client):
    'HU5 - Escenario 1 parte 2'
    'Dado que existe al menos un proyecto asociado al equipo de desarrollo y está registrada la fuente de información de Jira'
    'Cuando el líder de proyectos accede al dashboard del equipo de desarrollo'
    'Entonces se genera el dashboard a partir de los datos extraídos de las fuentes de información registradas'

    team_id = '629f6ff71785c7fd81349a17'

    client, mongo = test_client

    response = client.post('/jira/participation', json={
        'team_id': team_id, 
    })

    data_str = response.data.decode('utf8')

    data = loads(data_str)

    assert 'developers' in data.keys()

    assert len(data['developers']) == 6
    
    assert 'Created issues' in data['developers'].keys()
    assert ['Florencia Corvalan', 0] in data['developers']['Created issues']
    assert ['Florencia Corvalan Lillo', 100] in data['developers']['Created issues']
    
    assert 'Updated issues' in data['developers'].keys()
    assert ['Florencia Corvalan', 30] in data['developers']['Updated issues']
    assert ['Florencia Corvalan Lillo', 70] in data['developers']['Updated issues']
    
    assert 'Story point estimate' in data['developers'].keys()
    assert ['Florencia Corvalan', 0] in data['developers']['Story point estimate']
    assert ['Florencia Corvalan Lillo', 100] in data['developers']['Story point estimate']

    assert 'resolution' in data['developers'].keys()
    assert ['Florencia Corvalan', 50] in data['developers']['resolution']
    assert ['Florencia Corvalan Lillo', 50] in data['developers']['resolution']

    assert 'status' in data['developers'].keys()
    assert ['Florencia Corvalan', 50] in data['developers']['status']
    assert ['Florencia Corvalan Lillo', 50] in data['developers']['status']

    assert 'Sprint' in data['developers'].keys()
    assert ['Florencia Corvalan', 0] in data['developers']['Sprint']
    assert ['Florencia Corvalan Lillo', 100] in data['developers']['Sprint']

    assert 'totals' in data.keys()

    assert 'total_created' in data['totals'].keys()
    assert 'total_updated' in data['totals'].keys()
    assert 'Story point estimate' in data['totals'].keys()
    assert 'resolution' in data['totals'].keys()
    assert 'status' in data['totals'].keys()
    assert 'Sprint' in data['totals'].keys()

    assert data['totals']['total_created'] == 4
    assert data['totals']['total_updated'] == 20
    assert data['totals']['Story point estimate'] == 4
    assert data['totals']['resolution'] == 4
    assert data['totals']['status'] == 8
    assert data['totals']['Sprint'] == 4
