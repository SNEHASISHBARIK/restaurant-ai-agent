import re
import pytest
from app.agent.router import route_message
from app.agent.schemas import ComplaintClassification
from app.workflows.complaint_workflow import apply_priority_rules


def chat(client, customer, message, session):
    return client.post('/api/agent/chat', json={'session_id': session, 'customer_id': customer, 'message': message})


@pytest.mark.parametrize('text,intent', [
    ('Where is my order ORD-1001?', 'order_status'),
    ('Tell me the details of ORD-1002.', 'order_details'),
    ("What's in my order ORD-1005?", 'order_details'),
    ('What is your cancellation policy?', 'rag'),
    ('What is the policy on late deliveries?', 'rag'),
    ('I was charged twice for my order. Please help me.', 'complaint'),
    ('I want a refund, I was charged twice', 'complaint'),
    ('My order is very late. I want to raise a complaint.', 'complaint'),
    ('hello there', 'general'),
])
def test_routing(text, intent):
    assert route_message(text) == intent


@pytest.mark.parametrize('category,msg,expected', [
    ('Payment', 'I was charged twice', 'High'),
    ('Payment', 'my payment page looks odd', 'Medium'),
    ('Delivery', 'my order is late', 'Medium'),
    ('Delivery', 'still waiting after 2 hours', 'High'),
    ('Order', 'I am allergic and the food had nuts', 'High'),
    ('Technical', 'app is slow', 'Low'),
])
def test_priority_rules(category, msg, expected):
    c = ComplaintClassification(category=category, priority='Low', sentiment='Neutral', summary='summary')
    assert apply_priority_rules(c, msg).priority == expected


def test_details_intent_end_to_end(client):
    r = chat(client, 'CUS-005', 'Tell me the details of ORD-1005.', 'fix-details')
    assert r.json()['tool_calls'][0]['tool'] == 'get_order_details' and 'Masala Dosa' in r.json()['answer']


def test_details_without_order_id_asks(client):
    r = chat(client, 'CUS-005', 'Show me the order details', 'fix-details-noid')
    assert 'order ID' in r.json()['answer'] and not r.json()['tool_calls']


def test_other_customers_order_looks_like_missing(client):
    a = chat(client, 'CUS-005', 'Where is my order ORD-1001?', 'fix-auth-1').json()['answer']
    b = chat(client, 'CUS-005', 'Where is my order ORD-9999?', 'fix-auth-2').json()['answer']
    assert a == b and 'not found' in a.lower()


def test_charged_twice_is_high_and_linked(client):
    d = chat(client, 'CUS-005', 'I was charged twice for my order. Please help me.', 'fix-pay').json()
    assert d['category'] == 'Payment' and d['priority'] == 'High'
    assert re.fullmatch(r'TICKET-\d{8}-[0-9A-F]{6}', d['ticket_id']) and 'ORD-1005' in d['answer']


def test_late_complaint_links_active_order(client):
    d = chat(client, 'CUS-005', 'My order is very late. I want to raise a complaint.', 'fix-late').json()
    assert d['category'] == 'Delivery' and d['priority'] == 'Medium' and 'ORD-1005' in d['answer']


def test_ticket_never_links_another_customers_order(client):
    d = chat(client, 'CUS-005', 'Payment failed for ORD-1001', 'fix-foreign').json()
    assert 'ORD-1001' not in d['answer'] and 'ORD-1005' in d['answer']


def test_policy_answer_is_multiline(client):
    d = chat(client, 'CUS-005', 'What is your cancellation policy?', 'fix-policy').json()
    assert d['source'] == 'knowledge_base' and d['answer'].count('\n') >= 2
