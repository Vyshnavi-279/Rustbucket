from app.manifest_parser import parse_package_json, parse_requirements_txt

def test_parse_package_json():
    content = '{"dependencies": {"lodash": "^4.17.15"}}'
    deps = parse_package_json(content)
    assert len(deps) == 1
    assert deps[0]["name"] == "lodash"
    assert deps[0]["version"] == "4.17.15"

def test_parse_requirements_txt():
    content = "flask==2.0.1\nrequests>=2.25.0"
    deps = parse_requirements_txt(content)
    assert len(deps) == 2
    assert deps[0]["name"] == "flask"
    assert deps[0]["version"] == "2.0.1"