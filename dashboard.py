import streamlit as st
# import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd
from bus_history_data import get_bus_history_data
from incidence_data_preparation import get_incidence_df, get_incidence_predictions
from bus_dimensions import get_bus_dimensions

bus_history_df, components_to_replace = get_bus_history_data(1000)
incidens_df = get_incidence_df(bus_history_df, components_to_replace)
lidf = get_incidence_predictions(incidens_df)
lidf = lidf.drop(columns=['latest_incident_timestamp'])
dimensions_df = get_bus_dimensions(lidf.bus_id.unique())


# Function to highlight rows based on a condition
def highlight_row(row):
    if row['maintenance_issue'] == 'HIGH':
        return ['background-color: #FFB6C1'] * len(row)
    elif row['maintenance_issue'] == 'MEDIUM':
        return ['background-color: #FFFF99'] * len(row)
    else:
        return [''] * len(row)


# Apply the style to the DataFrame

# Define the columns you want to allow selection for
select_columns = ['bus_id', 'component_type', 'maintenance_issue']

# Create a selectbox widget for column selection
selected_column = st.selectbox('Select column', select_columns)

# Get unique values in the selected column
unique_values = lidf[selected_column].unique()

# Create a multiselect widget for value selection
selected_values = st.multiselect('Select value(s)', unique_values)

# Filter the DataFrame
if selected_values:
    filtered_df = lidf[lidf[selected_column].isin(selected_values)]
else:
    filtered_df = lidf

# Display the filtered DataFrame
styled_df = filtered_df.style.apply(highlight_row, axis=1)
st.dataframe(styled_df)


# Define the dimensions you want to allow selection for
dimensions = ['All', 'state', 'bus_vendor', 'region']

# Create a selectbox widget for dimension selection
selected_dimension = st.selectbox('Select dimension', dimensions)
with_dimensions_df = lidf.join(dimensions_df.set_index('bus_id'), on='bus_id')

## Calculate the percentage of buses with different maintenance issues
if selected_dimension == 'All':
    grouped_df = with_dimensions_df['maintenance_issue'].value_counts(normalize=True).reset_index()
    grouped_df.columns = ['maintenance_issue', 'percentage']
    grouped_df_long = grouped_df
else:
    grouped_df = with_dimensions_df.groupby([selected_dimension, 'maintenance_issue']).size().unstack(fill_value=0)
    grouped_df = grouped_df.divide(grouped_df.sum(axis=1), axis=0)
    grouped_df_long = grouped_df.reset_index().melt(id_vars=selected_dimension, var_name='maintenance_issue', value_name='percentage')

# Define the order of the maintenance issues
order = ['LOW', 'MEDIUM', 'HIGH']

# Convert the 'maintenance_issue' column to a categorical type with the specified order
grouped_df_long['maintenance_issue'] = pd.Categorical(grouped_df_long['maintenance_issue'], categories=order, ordered=True)

# Sort the DataFrame by the 'maintenance_issue' column
grouped_df_long = grouped_df_long.sort_values('maintenance_issue')

# Create a new column for the y-axis when selected_dimension is 'All'
if selected_dimension == 'All':
    grouped_df_long['y_axis'] = 'All'

# Create the bar chart
if selected_dimension == 'All':
    fig = px.bar(grouped_df_long, x='percentage', y='y_axis', color='maintenance_issue', orientation='h', 
                 hover_data={'percentage':True}, 
                 labels={'percentage':'Percentage', 'y_axis':'All'},
                 title='Maintenance Issues by All')
else:
    fig = px.bar(grouped_df_long, x='percentage', y=selected_dimension, color='maintenance_issue', orientation='h', 
                 hover_data={'percentage':True}, 
                 labels={'percentage':'Percentage'},
                 title='Maintenance Issues by '+selected_dimension)

# Display the chart in Streamlit
st.plotly_chart(fig)
