import numpy as np
import pandas as pd
from bus_history_data import standard_mileages, avg_mileage_per_day

alert_levels = ["HIGH", "MEDIUM", "LOW"]

component_map = {
    1: 'engine',
    2: 'transmission',
    3: 'radiator',
    4: 'breaks'
}

def get_component_indecies(components_to_replace):
    component_indecies = []
    for i, row in enumerate(components_to_replace):
        component_indecies.append([component_map[v+1] for v in np.where(row == 1)[0]])
    return component_indecies

def get_incidence_df(df, components_to_replace):
    incident_component_type = get_component_indecies(components_to_replace)
    incident_data = []

    for i, components in enumerate(incident_component_type):
        for component in components:
            line = df.iloc[i][['bus_id', f'{component}_id', 'mileage', 'start_timestamp']].values
            line = [component] + list(line)
            incident_data.append(line)

    incident_columns=['component_type', 'bus_id', 'component_id', 'mileage','incident_timestamp']
    incident_df = pd.DataFrame(data=incident_data, columns=incident_columns)
    incident_df['incident_id'] = (incident_df['bus_id'].astype(str) + '_' +
                                incident_df['component_id'].astype(str) + '_' +
                                incident_df['component_type'].astype(str) + '_' +
                                incident_df['incident_timestamp'].astype(str)
                                )
    return incident_df

def get_latest_incident_df(incident_df):
    latest_incident_df = (incident_df.groupby(['bus_id', 'component_type'])
                                     .agg({
                                         'incident_timestamp': 'max',
                                         'mileage': 'max',
                                         'component_id': 'count'
                                         })
                                     .rename(columns={
                                         'component_id': 'records',
                                         'incident_timestamp': 'latest_incident_timestamp'
                                         })
                                     .reset_index()
                        )

    current_mileage = (latest_incident_df.groupby('bus_id')
                                        .agg({'mileage': 'max'})
                                        .rename(columns={'mileage': 'current_mileage'})
                                        .reset_index()
                    )
    standard_mileages_df = (pd.DataFrame.from_dict(standard_mileages, orient='index')
                                        .reset_index()
                                        .rename(columns={'index': 'component_type', 0: 'standard_mileage'})
                            )
    latest_incident_df = (latest_incident_df.join(current_mileage.set_index('bus_id'), on='bus_id')
                                            .join(standard_mileages_df.set_index('component_type'), on='component_type')
                        )
    return latest_incident_df

def get_incidence_predictions(incident_df):
    lidf = get_latest_incident_df(incident_df)

    lidf['mileage_to_replace'] = (lidf['standard_mileage'] + lidf['mileage'] - lidf['current_mileage']).clip(lower=0)
    lidf['days_to_replace'] = ( lidf['mileage_to_replace'] / avg_mileage_per_day).astype(int)
    lidf['part_wear'] = (lidf['current_mileage'] - lidf['mileage']) / lidf['standard_mileage']


    conditions = [
        (lidf['days_to_replace'] == 0),
        (lidf['days_to_replace'] < 150),
        (lidf['days_to_replace'] >= 150)
    ]    

    # Create the 'maintenance_issue' column using numpy.select
    lidf['maintenance_issue'] = np.select(conditions, alert_levels, default=np.nan)
    return lidf
