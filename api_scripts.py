import requests
import json


def get_Token():
    with open('api_token.txt') as f:
        line = f.readline()
    return line


def api_get_distribution(taxon_name):
    token = get_Token()
    headers = {
        "X-Authentication-Token": token,
    }
    payload = {
        "taxon_concept_id": taxon_name,
    }
    url = "https://api.speciesplus.net/api/v1/taxon_concepts/"
    response = requests.get(url, params=payload, headers=headers)
    return response

def api_query(taxon_name):
    distribution_json = api_get_distribution(taxon_name)
    return distribution_json

test_reponse = api_query("Corallus hortulanus")

data = test_reponse.json()

json_formatted_str = json.dumps(data, indent=2)

print(json_formatted_str)