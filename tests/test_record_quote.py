import json

from record_quote import record
from sz_config import Project


def test_quotes_are_appended_never_replaced(tmp_path):
    record(str(tmp_path), claim="raised $5M", url="https://x",
           quote="a total Series A raise of $5 million", method="browser")
    record(str(tmp_path), claim="raised $5M", url="https://x",
           quote="second read, same page", method="browser")
    path = Project(str(tmp_path)).state_path("quotes.json")
    data = json.load(open(path, encoding="utf-8"))
    assert len(data) == 2
