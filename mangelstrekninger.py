# -*- coding: utf-8 -*-
"""
Created on Wed Aug  7 08:09:48 2024

@author: andryg
"""

import nvdbapiv3
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely import wkt
from datetime import datetime
import intervals as I

def download_vegnett():
    vegnett = pd.DataFrame(nvdbapiv3.nvdbVegnett(filter={'vegsystemreferanse':['E','R'],'veglenketype':'hoved','trafikantgruppe':'K'}).to_records())
    vegnett = vegnett[(vegnett['typeVeg'] == 'Enkel bilveg') | (vegnett['typeVeg'] == 'Kanalisert veg')]
    vegnett = vegnett[vegnett['fase'] == 'V']
    vegnett['geometry'] = vegnett['geometri'].apply(wkt.loads)
    vegnett = gpd.GeoDataFrame(vegnett, geometry='geometry', crs=5973)
    
    vegnett.to_excel("vegnett.xlsx")
    return True

def download_heldekkende_data(nvdbid):
    fagdata = nvdbapiv3.nvdbFagdata(nvdbid)
    fagdata.filter({'vegsystemreferanse':['E','R'],'veglenketype':'hoved','trafikantgruppe':'K'})
    fagdata = pd.DataFrame(fagdata.to_records())
    fagdata = fagdata[fagdata['veglenkeType'] == 'HOVED']
    fagdata = fagdata[(fagdata['typeVeg'] == 'Enkel bilveg') | (fagdata['typeVeg'] == 'Kanalisert veg')]
    fagdata = fagdata[fagdata['fase'] == 'V']
    fagdata['geometry'] = fagdata['geometri'].apply(wkt.loads)
    fagdata = gpd.GeoDataFrame(fagdata, geometry='geometry', crs=5973)
    
    fagdata.to_excel(f"{nvdbid}_{str(datetime.now()).split()[0]}.xlsx")
    
def grupper_på_veglenke(dataframe):
    dataframe['posisjon'] = dataframe.apply(lambda x: str(x.startposisjon) + '--' + str(x.sluttposisjon),axis=1)
    dataframe = dataframe.groupby('veglenkesekvensid')[['veglenkesekvensid','posisjon','lengde']].agg({
            'posisjon': lambda x: list(x),
            'lengde': 'sum'
        })
    
    return dataframe

def finn_manglende_strekning(row):
    intervals_x = [I.closed(float(posisjon.split("--")[0]),float(posisjon.split("--")[1])) for posisjon in row.posisjon_x]
    if row.isnull().any():
        interval_x = intervals_x[0]
        for interval in intervals_x:
            interval_x = interval_x | interval
        return interval_x
    intervals_y = [I.closed(float(posisjon.split("--")[0]),float(posisjon.split("--")[1])) for posisjon in row.posisjon_y]
    
    rest_interval_x = I.closed(0,1)
    for interval in intervals_x:
        rest_interval_x = rest_interval_x - interval
        
    rest_interval_y = I.closed(0,1)
    for interval in intervals_y:
        rest_interval_y = rest_interval_y - interval
    
    return rest_interval_y - rest_interval_x

def main():
    #download_heldekkende_data(639)
    vegnett_df = pd.read_excel("vegnett.xlsx")
    fagdata_df = pd.read_excel("639_2024-08-07.xlsx")
    fagdata_df = fagdata_df.rename(columns={'segmentlengde':'lengde'})
    
    vegnett_df = grupper_på_veglenke(vegnett_df)
    fagdata_df = grupper_på_veglenke(fagdata_df)
    
    merged_df = pd.merge(vegnett_df, fagdata_df, how='left', on='veglenkesekvensid')
    merged_df['manglende_lengde'] = merged_df.apply(lambda x: float(x.lengde_x)-float(x.lengde_y) if pd.notna(x.lengde_y) else x.lengde_x,axis=1)
    merged_df['manglende_strekninger'] = merged_df.apply(lambda x: finn_manglende_strekning(x),axis=1)
    merged_df.to_excel("rapport.xlsx")
    
if __name__ == "__main__":
    main()