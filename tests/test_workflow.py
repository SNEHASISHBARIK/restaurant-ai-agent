from app.agent.schemas import ComplaintClassification
from app.workflows.complaint_workflow import apply_priority_rules

def test_payment_priority_rule():
    c=ComplaintClassification(category='Payment',priority='Low',sentiment='Negative',summary='payment issue')
    assert apply_priority_rules(c,'My payment was deducted and the order failed.').priority=='High'
