# -*- coding: utf-8 -*-
"""
Created on Wed Aug  7 08:09:48 2024

@author: andryg
"""

import nvdbapiv3
import pandas as pd
import intervals as I
import argparse

def download_vegnett():
    vegnett = pd.DataFrame(nvdbapiv3.nvdbVegnett(filter={'vegsystemreferanse':['E','R'],'veglenketype':'hoved','trafikantgruppe':'K'}).to_records())
    vegnett = vegnett[(vegnett['typeVeg'] == 'Enkel bilveg') | (vegnett['typeVeg'] == 'Kanalisert veg')]
    vegnett = vegnett[vegnett['fase'] == 'V']
    
    vegnett.to_excel("vegnett.xlsx")
    return vegnett

def download_heldekkende_data(nvdbid):
    fagdata = nvdbapiv3.nvdbFagdata(nvdbid)
    fagdata.filter({'vegsystemreferanse':['E','R'],'veglenketype':'hoved','trafikantgruppe':'K'})
    fagdata = pd.DataFrame(fagdata.to_records())
    fagdata = fagdata[fagdata['veglenkeType'] == 'HOVED']
    fagdata = fagdata[(fagdata['typeVeg'] == 'Enkel bilveg') | (fagdata['typeVeg'] == 'Kanalisert veg')]
    fagdata = fagdata[fagdata['fase'] == 'V']
    
    fagdata.to_excel(f"{nvdbid}.xlsx")
    return True
    
def grupper_på_strekning(dataframe):
    dataframe['strekning'] = dataframe['vref'].apply(lambda x: ' '.join(x.split()[:-1]))
    dataframe['meterverdi'] = dataframe['vref'].apply(lambda x: x.split()[-1][1:])
    dataframe = dataframe.groupby('strekning',as_index=False)[['strekning','meterverdi','lengde','kommune']].agg({
            'meterverdi': lambda x: list(x),
            'lengde': 'sum',
            'kommune': lambda x: set(x)
        })
    
    return dataframe

def finn_manglende_strekning(row):
    intervals_x = [I.closed(int(meterverdi.split("-")[0]),int(meterverdi.split("-")[1])) for meterverdi in row.meterverdi_x]
    if row.isnull().any():
        interval_x = intervals_x[0]
        for interval in intervals_x:
            interval_x = interval_x | interval
        return interval_x
    intervals_y = [I.closed(int(meterverdi.split("-")[0]),int(meterverdi.split("-")[1])) for meterverdi in row.meterverdi_y]
    
    rest_interval_x = I.closed(0,max([int(i.split("-")[1]) for i in row.meterverdi_x]))
    for interval in intervals_x:
        rest_interval_x = rest_interval_x - interval
        
    rest_interval_y = I.closed(0,max([int(i.split("-")[1]) for i in row.meterverdi_x]))
    for interval in intervals_y:
        rest_interval_y = rest_interval_y - interval
    
    return rest_interval_y - rest_interval_x

def main(vegobjektid):
    try:
        vegnett_df = pd.read_excel("vegnett.xlsx") #Fra download_vegnett
    except FileNotFoundError:
        print("Fil eksisterer ikke. Laster ned ny fil...")
        vegnett_df = download_vegnett()
        
    try:
        fagdata_df = pd.read_excel(f"{vegobjektid}.xlsx") #Fra download_heldekkende_data
    except FileNotFoundError:
        print("Fil eksisterer ikke. Laster ned ny fil...")
        fagdata_df = download_heldekkende_data(vegobjektid)
        
    fagdata_df = fagdata_df.rename(columns={'segmentlengde':'lengde'})
    
    vegnett_df = grupper_på_strekning(vegnett_df)
    fagdata_df = grupper_på_strekning(fagdata_df)
    
    merged_df = pd.merge(vegnett_df, fagdata_df[['strekning','meterverdi','lengde']], how='left', on='strekning')
    merged_df['manglende_lengde'] = merged_df.apply(lambda x: float(x.lengde_x)-float(x.lengde_y) if pd.notna(x.lengde_y) else x.lengde_x,axis=1)
    merged_df['manglende_strekninger'] = merged_df.apply(lambda x: finn_manglende_strekning(x),axis=1)
    merged_df.to_excel(f"rapport_{vegobjektid}.xlsx") #Legg til navn basert på nvdbid
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Finn strekninger med manglende data.')
    parser.add_argument('vegobjektid', type=int, help='Id til heldekkende vegobjekt.')
    args = parser.parse_args()
    main(args.vegobjektid)