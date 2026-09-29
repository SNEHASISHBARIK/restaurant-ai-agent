def test_health(client):
    assert client.get('/health').status_code == 200

def test_order_status(client):
    r=client.get('/api/orders/ORD-1005/status', headers={'X-Customer-ID':'CUS-005'})
    assert r.status_code == 200 and r.json()['status'] == 'Out for Delivery'

def test_order_details(client):
    r=client.get('/api/orders/ORD-1005', headers={'X-Customer-ID':'CUS-005'})
    assert r.status_code == 200 and 'Masala Dosa' in r.json()['items']

def test_invalid_order(client):
    assert client.get('/api/orders/ABCXYZ/status', headers={'X-Customer-ID':'CUS-005'}).status_code == 400

def test_unknown_order(client):
    assert client.get('/api/orders/ORD-9999/status', headers={'X-Customer-ID':'CUS-005'}).status_code == 404

def test_unauthorized(client):
    assert client.get('/api/orders/ORD-1005/status', headers={'X-Customer-ID':'CUS-001'}).status_code == 404  # same as unknown: no ID probing
