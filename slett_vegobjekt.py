# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 12:15:11 2024

@author: andryg
"""

import argparse
import getpass
import requests
import datetime
import json
from pathlib import Path

def fjern_vegobjekt(id):
    
    return True

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1', 'j', 'ja'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')
        
def hent_vegobjekt_info(vegobjektid, miljø):
    if miljø == 'utv':
        r = requests.get(f"https://nvdbapiles-v3.utv.atlas.vegvesen.no/vegobjekt", params={'id':vegobjektid}, headers={'X-client':'Andryg - python Slett enkelt vegobjekt'})
    elif miljø == 'stm':
        r = requests.get(f"https://nvdbapiles-v3-stm.utv.atlas.vegvesen.no/vegobjekt", params={'id':vegobjektid}, headers={'X-client':'Andryg - python Slett enkelt vegobjekt'})
    elif miljø == 'test':
        r = requests.get(f"https://nvdbapiles-v3.test.atlas.vegvesen.no/vegobjekt", params={'id':vegobjektid}, headers={'X-client':'Andryg - python Slett enkelt vegobjekt'})
    else:
        r = requests.get(f"https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekt", params={'id':vegobjektid}, headers={'X-client':'Andryg - python Slett enkelt vegobjekt'})
    if r.status_code == 200:
        return r.json()
    else:
        print("Error: "+str(r.content))
        return {}
    
def skriv(username, password, endringssett, miljø):
    session = requests.session()
    if miljø == 'utv':
        url = "https://nvdbapiskriv.utv.atlas.vegvesen.no/rest/v1/oidc/authenticate"
    elif miljø == 'stm':
        url = "https://nvdbapiskriv-stm.utv.atlas.vegvesen.no/rest/v1/oidc/authenticate"
    elif miljø == 'test':
        url = "https://nvdbapiskriv.test.atlas.vegvesen.no/rest/v1/oidc/authenticate"
    else:
        url = "https://nvdbapiskriv.atlas.vegvesen.no/rest/v1/oidc/authenticate"
        
    

def lag_endringssett(vegobjektid, kaskadelukking, miljø):
    vegobjekt = hent_vegobjekt_info(vegobjektid, miljø)
    versjon = vegobjekt.get('metadata').get('versjon')
    typeid = vegobjekt.get('metadata').get('type').get('id')
    print(versjon, typeid)
    
    status = requests.get("https://nvdbapiles-v3.atlas.vegvesen.no/status", headers={'X-client':'Andryg - python Slett enkelt vegobjekt'})
    if status.status_code == 200:
        print(status.json())
        datakatalogversjon = status.json().get('datagrunnlag').get('datakatalog').get('versjon')
    else:
        print("Error: "+str(status.content))
        datakatalogversjon = "2.37"
    
    return {
        "lukk": {
            "vegobjekter": [
                {
                    "lukkedato": str(datetime.datetime.now()).split(" ")[0],
                    "kaskadelukking": "JA" if kaskadelukking else "NEI",
                    "typeId": typeid,
                    "nvdbId": vegobjektid,
                    "versjon": versjon
                    }
                ]
            },
        "datakatalogversjon": datakatalogversjon
        }

def main(vegobjektid, lukke_objekt, kaskadelukking, miljø):
    print(vegobjektid, lukke_objekt, miljø)
    username = input("Brukernavn: ")
    password = getpass.getpass("Passord: ")
    print(password)
    
    endringssett = lag_endringssett(vegobjektid, kaskadelukking, miljø)

    with open(f"slett_{vegobjektid}.json", "w") as fp:
        json.dump(endringssett, fp, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    miljøer = ['prod', 'test', 'utv', 'stm']
    parser = argparse.ArgumentParser(description='Fjern NVDB objekt.')
    parser.add_argument('vegobjektid', type=int, help='Id til vegobjekt som skal slettes.')
    parser.add_argument('lukke_objekt', type=str2bool, help='Skal vegobjektet lukkes (Ja) eller slettes (Nei)?')
    parser.add_argument('kaskadelukking', type=str2bool, help='Skal barnobjekter også slettes?')
    parser.add_argument('miljø', help='Miljø vegobjektet skal slettes i: prod, test, utv eller stm', choices = miljøer)
    args = parser.parse_args()
    main(args.vegobjektid, args.lukke_objekt, args.kaskadelukking, args.miljø)