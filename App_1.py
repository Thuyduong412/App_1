import pandas as pd
import folium
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import folium_static
import streamlit.components.v1 as components
import requests
from io import BytesIO
from geopy.geocoders import Nominatim
page_bg_image = """
<style>
[data-testid="stAppViewContainer"] {
    background-image: url("https://www.123rf.com/photo_120426802_the-world-logistics-there-are-world-map-with-logistic-network-distribution-on-background-and.html");
    background-size: cover;
    background-position: center;
}
</style>
"""
st.set_page_config(layout="wide")

st.markdown(page_bg_image, unsafe_allow_html=True)
file_path = 'https://github.com/Thuyduong412/App-Demo/blob/main/Trade_Map_-_DataSet_Cinnamom.xlsx'

# Read the sheets from the Excel file
import_file = pd.read_excel(file_path, sheet_name='Trade_Map_List_of_supplying')
export_file = pd.read_excel(file_path, sheet_name='Trade_Map_-_List_of_importing_m')
# Xây dựng các hàm tính toán, các select box:
# Hàm tính giá trị xuất khẩu:
def total_export_value(export_file):
    export_file['Total Export Value'] = export_file[
        ['Exported value in 2013', 'Exported value in 2014',
         'Exported value in 2015', 'Exported value in 2016',
         'Exported value in 2017', 'Exported value in 2018',
         'Exported value in 2019', 'Exported value in 2020',
         'Exported value in 2021', 'Exported value in 2022']
    ].sum(axis=1)
    return export_file
# Hàm tính giá trị nhập khẩu:
def total_import_value(import_file):
    import_file['Total Import Value'] = import_file[
        ['Imported value in 2013', 'Imported value in 2014',
         'Imported value in 2015', 'Imported value in 2016',
         'Imported value in 2017', 'Imported value in 2018',
         'Imported value in 2019', 'Imported value in 2020',
         'Imported value in 2021', 'Imported value in 2022']
    ].sum(axis=1)
    return import_file
# Hàm tính giá trị xuất khẩu theo năm:
def total_export_by_year(export_file):
    years = range(2013, 2023)
    total_export_values = [export_file[f'Exported value in {year}'].sum() for year in years]
    return np.array(total_export_values)
# Hmà tính giá trị nhập khẩu theo năm:
def total_import_by_year(import_file):
    years = range(2013, 2023)
    total_import_values = [import_file[f'Imported value in {year}'].sum() for year in years]
    return np.array(total_import_values)
# Hàm tính phần trăm xuất theo năm:
def export_percent_by_year(export_file):
    total_export_values = total_export_by_year(export_file)
    export_percent = (total_export_values / total_export_values.sum()) * 100
    return export_percent
# Hàm tính phần trăm nhập khẩu theo năm:
def import_percent_by_year(import_file):
    total_import_values = total_import_by_year(import_file)
    import_percent = (total_import_values / total_import_values.sum()) * 100
    return import_percent

export_file = total_export_value(export_file)
import_file = total_import_value(import_file)

export_values_by_year = total_export_by_year(export_file)
import_values_by_year = total_import_by_year(import_file)

export_percentage_by_year = export_percent_by_year(export_file)
import_percentage_by_year = import_percent_by_year(import_file)
# Hàm lấy năm xuất/nhập khẩu:
def get_year():
    years = [col.split() [-1] for col in export_file.columns if 'Exported value in' in col]
    return years
# Hàm lấy danh sách các quốc gia xuất khẩu:
def get_export_countries():
    export_countries = export_file['Importers'].unique().tolist()
    return[importers for importers in export_countries if importers != 'World']

# Hàm lấy danh sách các quốc gia nhập khẩu:
def get_import_countries():
    import_countries = import_file['Exporters'].unique().tolist()
    return[exporters for exporters in import_countries if exporters != 'World']
# Hàm lấy danh sách các mặt hàng xuất /nhập khẩu:
def get_products():
    products = export_file['Product Description'].unique()
    return products
# Hàm để tạo select box chọn Import hoặ Export:
def select_import_export(key = 'import_export'):
    option = st.selectbox('Select Import or Export', ['Import', 'Export'], key = key )
    return option
# Hàm tính total value cho mỗi quốc gia(groupby theo quốc gia):
def total_value_by_country(selected_import_export):
    if selected_import_export == 'Export':
        total_value = export_file.groupby('Importers')['Total Export Value'].sum().reset_index()
    else:
        total_value = import_file.groupby('Exporters')['Total Import Value'].sum().reset_index()
    return total_value
def filter_data_by_export(selected_products, selected_year=None):
    if isinstance(selected_products, str):
        selected_products = [selected_products]
    elif not isinstance(selected_products, list):
        selected_products = list(selected_products)
    
    filtered_data  = export_file[export_file['Product Description'].isin(selected_products)]
    if not filtered_data.empty:
       values_col = [col for col in filtered_data.columns if 'exported value' in col.lower()]
       melted_data = pd.melt(
            filtered_data,
            id_vars=['Importers', 'Product Description'],
            value_vars=values_col,
            var_name='Year',
            value_name='Value'
             )
       melted_data['Year'] = melted_data['Year'].str.extract(r'(\d{4})')
       melted_data = melted_data.dropna(subset='Year')
       melted_data['Year'] = melted_data['Year'].astype(int)
        
       if selected_year:
            filtered_data = melted_data[melted_data['Year'] == int(selected_year)]
       else:
            aggregated_data = melted_data.groupby(['Year', 'Product Description'])['Value'].sum().reset_index()
            filtered_data = aggregated_data.pivot(index='Year', columns='Product Description', values='Value')
        
       return filtered_data
    else:
        return None

# Filter data for import:
def filter_data_by_import(selected_products, selected_year=None):
    if isinstance(selected_products, str):
        selected_products = [selected_products]
    elif not isinstance(selected_products, list):
        selected_products = list(selected_products)
    
    filtered_data = import_file[import_file['Product Description'].isin(selected_products)]
    if not filtered_data.empty:
        values_col = [col for col in filtered_data.columns if 'imported value' in col.lower()]
        melted_data = pd.melt(
            filtered_data,
            id_vars=['Exporters', 'Product Description'],
            value_vars=  values_col,
            var_name= 'Year',
            value_name= 'Value'
        )
        
        melted_data['Year'] = melted_data['Year'].str.extract(r'(\d{4})')
        melted_data = melted_data.dropna(subset=['Year'])
        melted_data['Year'] = melted_data['Year'].astype(int)

        if selected_year:
            filtered_data = melted_data[melted_data['Year']== int(selected_year)]
        else:
            aggregated_data = melted_data.groupby(['Year', 'Product Description'])['Value'].sum().reset_index()
            filtered_data = aggregated_data.pivot(index = 'Year', columns = 'Product Description', values = 'Value')
        return filtered_data
    else:
        return None

 # set title cho all:
st.markdown(
    "<h1 style='text-align: center; color: #0f466b; font-size: 40px;'>ANALYSIS OF VIETNAM'S IMPORT-EXPORT OF CINNAMON</h1>", 
    unsafe_allow_html=True)
with st.expander('OVERVIEW'):
    st.markdown(
        "<h2 style='color:#0f466b; font-size:20px;'>1. Total Eport/Import overtime<h2>",
        unsafe_allow_html=True
    )
    # Sử dụng biểu đồ cột ghép để visualize tổng giá trị xuất/nhập khẩu qua từng năm:
    fig = go.Figure()
    # Add cột export:
    fig.add_trace(go.Bar(
        x = get_year(),
        y = total_export_by_year(export_file),
        name = 'Export Values',
        marker_color = 'rgb(55,83,109)',
    ))
    #Add cột import:
    fig.add_trace(go.Bar(
        x = get_year(),
        y = total_import_by_year(import_file),
        name= 'Import Values',
        marker_color = 'rgb(26,118,255)',       
    ))
    #Upadte layout
    fig.update_layout(
        title = {
        'text': 'Total Export/Import Value Over Time',
        'x': 0.5,  # Centers the title
        'xanchor': 'center',  # Ensures the anchor is the center of the title
        'font': {'size': 20,
                 'color':'#0f466b' }  # Optional: Adjust the font size as needed
    },
        xaxis_tickfont_size =14,
        yaxis = dict(
            title = 'Value',
            tickfont_size = 14
        )
    )
    st.plotly_chart(fig)
    # Sử dụng line chart để thể hiện %:
    st.markdown(
        " <h2 style = 'color: #0f466b; font_size:20px;'>2. Export/Import Percentage Over Time<h2>",
        unsafe_allow_html= True
    )
    fig = go.Figure()

# Add export percentage line
    fig.add_trace(go.Scatter(
    x=get_year(), 
    y=export_percentage_by_year,
    mode='lines+markers',
    name='Export Percentage',
    line=dict(color='rgb(55,83,109)') 
    ))
# Add import percentage line
    fig.add_trace(go.Scatter(
    x=get_year(),
    y=import_percentage_by_year,
    mode='lines+markers',
    name='Import Percentage',
    line=dict(color='rgb(26,118,255)')  
))

# Update layout
    fig.update_layout(
    title={
        'text': 'Export/Import Percentage Over Time',
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 20, 'color': '#0f466b'}
    },
    xaxis=dict(
        title='Year',
        tickfont_size=14
    ),
    yaxis=dict( 
        title='Percentage',
        tickfont_size=14
    )
)

    # Display the plot in Streamlit
    st.plotly_chart(fig)
    # Sử dụng stackes bar chart để visualize theo mặt hàng gồm 2 cột xuất và nhập khẩu:
    
    st.markdown(
    "<h2 style='color: #0f466b; font-size:20px;'>3. Export/Import Value by Product</h2>",
    unsafe_allow_html=True
     )
    selected_products = st.multiselect(
    "Select products to display", 
    options=get_products(), 
    default=get_products()  # Set default to all products
)
    filtered_export_data = filter_data_by_export(selected_products)
    filtered_import_data = filter_data_by_import(selected_products)
    custom_colors = {
            'Cinnamomum zeylanicum Blume': '#104E8B',
            'Cinnamon and Cinnamon-tree flowers': '#0033cc',
            'Crushed or ground cinnamon and cinnamon-tree flowers': '#5CACEE'
        }
    col1, col2 = st.columns(2)
    with col1:
      if filtered_export_data is not None:
        export_data_melted = filtered_export_data.reset_index().melt(id_vars='Year', var_name='Product', value_name='Value')
        fig_export = px.bar(
            export_data_melted,
            x='Year',
            y='Value',
            color='Product',
            barmode='stack',
            title='Export Value by Year',
            labels={'Value': 'Total Export Value', 'Year': 'Year'},
            color_discrete_map=custom_colors  # Apply custom colors
        )
        fig_export.update_layout(
            title={'text': 'Export Value by Year', 'x': 0.5, 'xanchor': 'center'}
        )
        st.plotly_chart(fig_export)
      else:
        st.write('No export data to display.')

    with col2:
      if filtered_import_data is not None:
        import_data_melted = filtered_import_data.reset_index().melt(id_vars='Year', var_name='Product', value_name='Value')
        fig_import = px.bar(
            import_data_melted,
            x='Year',
            y='Value',
            color='Product',
            barmode='stack',
            title='Import Value by Year',
            labels={'Value': 'Total Import Value', 'Year': 'Year'},
            color_discrete_map=custom_colors  # Apply custom colors
        )
        fig_import.update_layout(
            title={'text': 'Import Value by Year', 'x': 0.5, 'xanchor': 'center'}
        )
        st.plotly_chart(fig_import)
      else:
        st.write('No import data to display.')
# Phần 2: Country Overview:
# Create 2 cột country trong 2 file :
import_file['Country'] = import_file['Exporters'].copy().str.strip() # Create 'Country' column for import data
export_file['Country'] = export_file['Importers'].copy().str.strip()
#st.write("Unique countries in Import File:", import_file['Country'].unique())
#st.write("Unique countries in Export File:", export_file['Country'].unique())
import_file = import_file[import_file['Country'] != 'World']
export_file = export_file[export_file['Country'] != 'World']
# Lọc data cho export/import distribution:
def filter_data_by_product_and_trade(data, selected_products, selected_import_export):
    data = data.dropna(subset=['Country'])
    if selected_import_export == 'Export':
        value_cols = [col for col in data.columns if 'Exported value in' in col]
    else:
        value_cols = [col for col in data.columns if 'Imported value in' in col]
    
    filtered_data = data[['Country', 'Product Description'] + value_cols]
    melted_data = pd.melt(
        filtered_data,
        id_vars=['Country', 'Product Description'],
        value_vars=value_cols,
        var_name='Year',
        value_name='Value'
    )

    filtered_data = melted_data[melted_data['Product Description'].isin(selected_products)]
    return filtered_data
def create_geo_map(filtered_data):
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="cartodb positron")

    geo_data_url = "http://geojson.xyz/naturalearth-3.3.0/ne_50m_admin_0_countries.geojson"
    response = requests.get(geo_data_url)
    geo_data = response.json()

    choropleth_data = filtered_data.groupby('Country')['Value'].sum().reset_index()

    folium.Choropleth(
        geo_data=geo_data,
        data=choropleth_data,
        columns=['Country', 'Value'],
        key_on='feature.properties.name',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Total Value'
    ).add_to(m)

    folium.GeoJson(
        geo_data,
        name='geojson',
        tooltip=folium.features.GeoJsonTooltip(
            fields=['name'],
            aliases=['Country:'],
            localize=True,
            labels=True
        )
    ).add_to(m)

    return m._repr_html_()
# Hmà lấy top10 quốc gia nhập khẩu từ việt nam trừ world:
def top_10_import_country(export_file):
    data_filtered = export_file[export_file['Importers'] != 'World']
    grouped_data = data_filtered.groupby('Importers')['Total Export Value'].sum().reset_index()
    top_10_import_country = grouped_data.sort_values('Total Export Value', ascending=False).head(10)
    return top_10_import_country
# Hàm lấy top 10 quốc gia xuất khẩu sang Việt Nam trừ world:
def top_10_export_country(import_file):
    data_filtered = import_file[import_file['Exporters'] != 'World']
    grouped_data = data_filtered.groupby('Exporters')['Total Import Value'].sum().reset_index()
    top_10_export_country = grouped_data.sort_values('Total Import Value', ascending=False).head(10)
    return top_10_export_country
with st.expander('COUNTRY OVERVIEW'):
    st.markdown(
        "<h2 style='color : #0f466b; font-size:20px;'>1.Export/Import Value Distribution by Country</h2>",
        unsafe_allow_html=True
    )

    # Select trade type and products
    selected_import_export = st.radio('Trade Type', ['Export', 'Import'])
    selected_products = st.multiselect('Select Product', get_products(), key='country_overview', default=get_products())

    # Filter and prepare data
    filtered_data = filter_data_by_product_and_trade(
        export_file if selected_import_export == 'Export' else import_file,
        selected_products,
        selected_import_export
    )

    # Display map
    if not filtered_data.empty:
        components.html(
            f"""
            <div style="width: 100%; height: 100vh;">
                {create_geo_map(filtered_data)}
            </div>
            """,
            height=650  # Đặt giá trị height đủ lớn để phần tử iframe có thể điều chỉnh kích thước
        )
    else:
        st.write('No data available for the selected criteria.')
# Cần fix lại vì chart ko hiện =))
# Top 10 Export/Import Country, biểu đồ cột ngang:
    st.markdown(
    "<h2 style='color: #0f466b; font-size:20px;'>2.Top 10 Export/Import Countries</h2>",
    unsafe_allow_html=True
)

# Assume import_file and export_file are already loaded
    top_10_export_countries = top_10_export_country(import_file)
    top_10_import_countries = top_10_import_country(export_file)

    col1, col2 = st.columns(2)
    with col1:
      fig_export = go.Figure(go.Bar(
        y=top_10_export_countries['Exporters'],  # y-axis for countries
        x=top_10_export_countries['Total Import Value'],  # x-axis for values
        orientation='h',
        marker_color='rgb(55,83,109)'
    ))
      fig_export.update_layout(
        title={
            'text': 'Top 10 Export Countries to VietNam',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#0f466b'}
        },
        xaxis=dict(
            title='Total Import Value',
            tickfont_size=14
        )
    )
      st.plotly_chart(fig_export)
      st.markdown(
        f"""
        <div style="text-align: center;">
            {top_10_export_countries.to_html(index=False, classes='table table-striped')}
        </div>
        """,
        unsafe_allow_html=True
    )

    with col2:
      fig_import = go.Figure(go.Bar(
        y=top_10_import_countries['Importers'],  # y-axis for countries
        x=top_10_import_countries['Total Export Value'],
        orientation='h',
        marker_color='rgb(55,83,109)'
    ))
      fig_import.update_layout(
        title={
            'text': 'Top 10 Import Countriesfrom VietNam',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#0f466b'}
        },
        xaxis=dict(
            title='Total Export Value',
            tickfont_size=14
        )
    )
      st.plotly_chart(fig_import)
      st.markdown(
        f"""
        <div style="text-align: center;">
            {top_10_import_countries.to_html(index=False, classes='table table-striped')}
        </div>
        """,
        unsafe_allow_html=True
    )
# Phần 3: Deep analysis by country:

def filter_data_for_country_export(selected_country, selected_products, selected_year=None):
    if isinstance(selected_country, str):
        selected_country = [selected_country]
    if not isinstance(selected_country, list):
        selected_country = list(selected_country)

    filtered_data = export_file[export_file['Product Description'].isin(selected_products)]
    
    if not filtered_data.empty:
        filtered_data = filtered_data[filtered_data['Importers'].isin(selected_country)]
        values_col = [col for col in filtered_data.columns if 'exported value' in col.lower()]

        melted_data = pd.melt(
            filtered_data,
            id_vars=['Importers', 'Product Description'],
            value_vars=values_col,
            var_name='Year',
            value_name='Value'
        )

        melted_data['Year'] = melted_data['Year'].str.extract(r'(\d{4})')
        melted_data = melted_data.dropna(subset=['Year'])
        melted_data['Year'] = melted_data['Year'].astype(int)

        if selected_year:
            filtered_data = melted_data[melted_data['Year'] == int(selected_year)]
        else:
            aggregated_data = melted_data.groupby(['Year', 'Product Description'])['Value'].sum().reset_index()
            filtered_data = aggregated_data.pivot(index='Year', columns='Product Description', values='Value')

        # Get the value for the nearest year
        latest_year = melted_data['Year'].max()
        latest_value = melted_data[melted_data['Year'] == latest_year].groupby('Product Description')['Value'].sum()
        latest_value_summary = latest_value.to_dict()

        return filtered_data, latest_year, latest_value_summary
    else:
        return None, None, {}

def filtered_data_for_country_import(selected_country, selected_products, selected_year=None):
    if isinstance(selected_country, str):
        selected_country = [selected_country]
    if not isinstance(selected_country, list):
        selected_country = list(selected_country)

    filtered_data = import_file[import_file['Product Description'].isin(selected_products)]
    
    if not filtered_data.empty:
        filtered_data = filtered_data[filtered_data['Exporters'].isin(selected_country)]
        values_col = [col for col in filtered_data.columns if 'imported value' in col.lower()]

        melted_data = pd.melt(
            filtered_data,
            id_vars=['Exporters', 'Product Description'],
            value_vars=values_col,
            var_name='Year',
            value_name='Value'
        )

        melted_data['Year'] = melted_data['Year'].str.extract(r'(\d{4})')
        melted_data = melted_data.dropna(subset=['Year'])
        melted_data['Year'] = melted_data['Year'].astype(int)

        if selected_year:
            filtered_data = melted_data[melted_data['Year'] == int(selected_year)]
        else:
            aggregated_data = melted_data.groupby(['Year', 'Product Description'])['Value'].sum().reset_index()
            filtered_data = aggregated_data.pivot(index='Year', columns='Product Description', values='Value')

        # Get the value for the nearest year
        latest_year = melted_data['Year'].max()
        latest_value = melted_data[melted_data['Year'] == latest_year].groupby('Product Description')['Value'].sum()
        latest_value_summary = latest_value.to_dict()

        return filtered_data, latest_year, latest_value_summary
    else:
        return None, None, {}
# Growth rate of each product by country:
def calculate_growth_rates_export(selected_country, selected_products, selected_year=None):
    # Ensure selected_country is a list
    if isinstance(selected_country, str):
        selected_country = [selected_country]
    if not isinstance(selected_country, list):
        selected_country = list(selected_country)

    # Filter data for the selected products and country
    filtered_data = export_file[
        (export_file['Product Description'].isin(selected_products)) &
        (export_file['Importers'].isin(selected_country))
    ]

    # Check if filtered data is empty
    if filtered_data.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Select columns containing 'exported value'
    values_col = [col for col in filtered_data.columns if 'exported value' in col.lower()]
    #st.write(filtered_data)
    # Check if there are columns to process
    if not values_col:
        return pd.DataFrame(), pd.DataFrame()

    # Reshape the data to have 'Year' as a column
    melted_data = pd.melt(
        filtered_data,
        id_vars=['Importers', 'Product Description'],
        value_vars=values_col,
        var_name='Year',
        value_name='Value'
    )

    # Extract the year from the column names
    melted_data['Year'] = melted_data['Year'].str.extract(r'(\d{4})')
    melted_data = melted_data.dropna(subset=['Year'])
    melted_data['Year'] = melted_data['Year'].astype(int)

    # Sort data by Product Description and Year
    melted_data = melted_data.sort_values(by=['Product Description', 'Year'])
    #st.write(melted_data)

    # Calculate the growth rate
    melted_data['Growth Rate (%)'] = melted_data.groupby('Product Description')['Value'].transform(lambda x: x.pct_change() * 100)
    melted_data['Growth Rate (%)'] = melted_data['Growth Rate (%)'].fillna(0)
    st.write(f"Growth Rates Data Import:", melted_data)

    # Filter data by selected year if provided
    if selected_year:
        filtered_data = melted_data[melted_data['Year'] == int(selected_year)]
    else:
        # Aggregate data by year and product description
        aggregated_data = melted_data.groupby(['Year', 'Product Description'])['Value'].sum().reset_index()
        filtered_data = aggregated_data

    return filtered_data, melted_data
# calculate growth rate for import:
def calculate_growth_rates_import(selected_country, selected_products, selected_year=None):
    if isinstance(selected_country, str):
        selected_country = [selected_country]
    if not isinstance(selected_country, list):
        selected_country = list(selected_country)
    filtered_data = import_file[
        (import_file['Product Description'].isin(selected_products)) &
        (import_file['Exporters'].isin(selected_country))
    ]
    if filtered_data.empty:
        return pd.DataFrame(), pd.DataFrame()
    values_col = [col for col in filtered_data.columns if 'imported value' in col.lower()]
    if not values_col:
        return pd.DataFrame(), pd.DataFrame()
    melted_data = pd.melt(
        filtered_data,
        id_vars=['Exporters', 'Product Description'],
        value_vars=values_col,
        var_name='Year',
        value_name='Value'
    )
    melted_data['Year'] = melted_data['Year'].str.extract(r'(\d{4})')
    melted_data = melted_data.dropna(subset=['Year'])
    melted_data['Year'] = melted_data['Year'].astype(int)
    melted_data = melted_data.sort_values(by=['Product Description', 'Year'])
    melted_data['Growth Rate (%)'] = melted_data.groupby('Product Description')['Value'].transform(lambda x: x.pct_change() * 100)
    melted_data['Growth Rate (%)'] = melted_data['Growth Rate (%)'].fillna(0)
    st.write(f"Growth Rates Data Export:", melted_data)
    if selected_year:
        filtered_data = melted_data[melted_data['Year'] == int(selected_year)]
    else:
        aggregated_data = melted_data.groupby(['Year', 'Product Description'])['Value'].sum().reset_index()
        filtered_data = aggregated_data
    return filtered_data, melted_data

with st.expander("DEEP ANALYSIS BY COUNTRY"):
    st.markdown(
        "<h2 style='color: #0f466b; font-size:20px;'>1. Export/Import Value by Country</h2>",
        unsafe_allow_html=True
    )

    selected_country = st.selectbox('Select Country', get_export_countries(), key="deep_analysis_by_country")
    selected_products = st.multiselect('Select Product', get_products(), key="deep_analysis_by_country_1", default=get_products())
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_data, latest_export_year, latest_export_value = filter_data_for_country_export(selected_country, get_products())

        custom_colors = {
            'Cinnamomum zeylanicum Blume': '#104E8B',
            'Cinnamon and Cinnamon-tree flowers': '#00688B',
            'Crushed or ground cinnamon and cinnamon-tree flowers': '#5CACEE'
        }

        if export_data is not None:
            export_data_melted = export_data.reset_index().melt(id_vars='Year', var_name='Product', value_name='Value')
            fig_export = px.bar(
                export_data_melted,
                x='Year',
                y='Value',
                color='Product',
                barmode='stack',
                title='Export Value by Year',
                labels={'Value': 'Total Export Value', 'Year': 'Year'},
                color_discrete_map=custom_colors  # Apply custom colors
            )
            fig_export.update_layout(
                title={'text': 'Export Value by Year', 'x': 0.5, 'xanchor': 'center'}
            )
            st.plotly_chart(fig_export)
            
            # Display latest export value
            if latest_export_year is not None:
                st.write(f"Export value for {selected_country} in {latest_export_year}:")
                for product, value in latest_export_value.items():
                    st.write(f"- {product}: ${value:,.2f}")
        else:
            st.write('No export data to display.')
    
    with col2:
        import_data, latest_import_year, latest_import_value = filtered_data_for_country_import(selected_country, get_products())

        if import_data is not None:
            import_data_melted = import_data.reset_index().melt(id_vars='Year', var_name='Product', value_name='Value')
            custom_colors = {
                'Cinnamomum zeylanicum Blume': '#104E8B',
                'Cinnamon and Cinnamon-tree flowers': '#00688B',
                'Crushed or ground cinnamon and cinnamon-tree flowers': '#5CACEE'
            }

            fig_import = px.bar(
                import_data_melted,
                x='Year',
                y='Value',
                color='Product',
                barmode='stack',
                title='Import Value by Year',
                labels={'Value': 'Total Import Value', 'Year': 'Year'},
                color_discrete_map=custom_colors  # Apply custom colors
            )
            fig_import.update_layout(
                title={'text': 'Import Value by Year', 'x': 0.5, 'xanchor': 'center'}
            )
            st.plotly_chart(fig_import)
            
            # Display latest import value
            if latest_import_year is not None:
                st.write(f"Import value for {selected_country} in {latest_import_year}:")
                for product, value in latest_import_value.items():
                    st.write(f"- {product}: ${value:,.2f}")
        else:
            st.write('No import data to display.')
    st.markdown(
    "<h2 style='color: #0f466b; font-size:20px;'>2. Export/Import Growth Rate by Country</h2>",
    unsafe_allow_html=True
)
    custom_colors = {
            'Cinnamomum zeylanicum Blume': '#104E8B',
            'Cinnamon and Cinnamon-tree flowers': '#00688B',
            'Crushed or ground cinnamon and cinnamon-tree flowers': '#5CACEE'
        }
    col1, col2 = st.columns(2)


    with col1:
      filtered_data, growth_data = calculate_growth_rates_export(selected_country,selected_products, selected_year = None )
    # Check if there is data to display
      if not filtered_data.empty:
        # Plot the growth rates
        fig = px.line(
            growth_data,
            x='Year',
            y='Growth Rate (%)',
            color='Product Description',
            title='Export Growth Rate by Country',
            labels={'Growth Rate (%)': 'Growth Rate (%)', 'Year': 'Year'},
            color_discrete_map=custom_colors
        )
        fig.update_layout( 
            title={'text': 'Export Growth Rate by Country', 'x': 0.5, 'xanchor': 'center'}
        )
        st.plotly_chart(fig)
        # wite the value and growth rate for the latest year
      else:
        st.write('No data available for the selected criteria.')
    with col2:
        filtered_data, growth_data = calculate_growth_rates_import(selected_country, selected_products, selected_year=None)
        if not filtered_data.empty:
            fig = px.line(
                growth_data,
                x='Year',
                y='Growth Rate (%)',
                color='Product Description',
                title='Import Growth Rate by Country',
                labels={'Growth Rate (%)': 'Growth Rate (%)', 'Year': 'Year'},
                color_discrete_map=custom_colors)
            fig.update_layout(
                title={'text': 'Import Growth Rate by Country', 'x': 0.5, 'xanchor': 'center'}
            )
            st.plotly_chart(fig)

        else:
            st.write('No data available for the selected criteria.')
# feedback:
with st.form(key='feedback_form'):
    st.write("If you have any feedback or suggestions, please feel free to share with us.")
    feedback_text = st.text_area("Your feedback:", placeholder="Type your feedback here...")
    
    # Form Submit Button
    submit_button = st.form_submit_button(label='Submit Feedback')
    
    if submit_button:
        if feedback_text:
            st.success("Thank you for your feedback!")
        else:
            st.error("Please enter your feedback before submitting.")



        

    
