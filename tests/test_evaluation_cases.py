import json
from pathlib import Path

def test_evaluation_file():
    cases=json.loads((Path(__file__).parent/'evaluation_cases.json').read_text())
    assert len(cases)==8
