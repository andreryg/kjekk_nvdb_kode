# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 14:29:43 2024

@author: andryg
"""

import nvdbapiv3
import pandas as pd
import argparse
import os
import requests

def download_data(vegobjekttypeid, fylkesnummer, vegkategorier):
    objekt = nvdbapiv3.nvdbFagdata(vegobjekttypeid)
    if vegkategorier:
        objekt.filter({'vegsystemreferanse':vegkategorier})
    objekt.filter({'fylke':fylkesnummer})
    df = pd.DataFrame(objekt.to_records(geometri=True, geometrikvalitet=True))
    
    return df

def main(vegobjekttypeid, vegkategorier):
    vegobjekttype = requests.get(f"https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekttyper/{vegobjekttypeid}")
    if vegobjekttype.status_code == 200:
        vegobjekttype = vegobjekttype.json().get('navn')
    else:
        print("Error: "+str(vegobjekttype.content))
    parent_dir = "C:/Users/andryg/Documents/Python Scripts/kjekk_nvdb_kode"
    head_directory = f"{vegobjekttypeid}_{vegobjekttype}"
    path = os.path.join(parent_dir, head_directory)
    os.mkdir(path)
    
    fylkesnummer = [3,11,15,18,31,32,33,34,39,40,42,46,50,55,56]
    
    if 'F'.casefold() in vegkategorier:
        f_veg_dir = 'F_veger'
        f_veg_path = os.path.join(path, f_veg_dir)
        os.mkdir(f_veg_path)
        
        for nr in fylkesnummer:
            download_data(vegobjekttypeid, nr, ['f']).to_excel(f"{head_directory}/F_veger/{vegobjekttypeid}_{nr}.xlsx")
        
    if 'E'.casefold() in vegkategorier or 'R'.casefold() in vegkategorier:
        er_veg_dir = 'ER_veger'
        er_veg_path = os.path.join(path, er_veg_dir)
        os.mkdir(er_veg_path)
        
        for nr in fylkesnummer:
            download_data(vegobjekttypeid, nr, ['e','r']).to_excel(f"{head_directory}/ER_veger/{vegobjekttypeid}_{nr}.xlsx")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fylkesseparert excel utskrift.')
    parser.add_argument('vegobjekttypeid', type=int, help='Vegobjekttypeid')
    parser.add_argument('vegkategorier', nargs='+', help='Vegobjekttypeid')
    args = parser.parse_args()
    main(args.vegobjekttypeid, args.vegkategorier)