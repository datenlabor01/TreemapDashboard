from dash import Dash, html, dcc, Input, Output, dash_table
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
from datetime import datetime

#Mapping-Dictionary für Förderbereichschlüssel:
keys_fbs = pd.read_excel("Purpose Codes Mapping.xlsx")
dic_dac = dict(zip(keys_fbs["DAC 5"], keys_fbs["DESCRIPTION"]))
dic_crs = dict(zip(keys_fbs["CRS"], keys_fbs["DESCRIPTION"]))

dat = pd.read_excel("DE-1-BMZ-Activities.xlsx")
rec_list = pd.read_excel("LänderlisteBMZ.xlsx")
country = dict(zip(rec_list["Country"], rec_list["Category"]))

#Convert numeric sector-codes to textform: 
dat["Purpose Code"] = dat[dat.columns[19]].map(dic_crs)
dat["Sector"] = dat[dat.columns[19]].astype(str).str[:3]
#dat["Sector"] = dat.Sector.map(dic_dac)

#Get the start and end year for each activity:
dat["Startyear"] = pd.DatetimeIndex(dat[dat.columns[10]]).year
dat["Endyear"] = pd.DatetimeIndex(dat[dat.columns[11]]).year

#Add regions to recipient column and map country categories: 
dat["Recipient"] = dat[dat.columns[3]]
dat.loc[dat.Recipient.isnull() == True, "Recipient"] = dat[dat.columns[0]]
dat["Category"] = dat["Recipient"].map(country)
dat.loc[dat.Category.isnull() == True,  "Category"] = "Kein Partnerland"
#Simplify column names for disbursement and commitment:
dat["Disbursement"] = dat[dat.columns[37]]
dat["Commitment"] = dat[dat.columns[36]]

dat = dat[["Startyear", "Endyear", "Disbursement", "Commitment", "Purpose Code", 
"Sector", "Recipient", "Category", "Maßnahmenstatus"]]
#Discard years before 2013:
dat = dat[dat["Startyear"] > 2012]
dat["Value"] = dat["Disbursement"]

#Build two-year average
def avg(dat, year):

   dat_mean = dat.groupby(["Startyear", "Purpose Code", "Sector", "Category", "Recipient"]).Commitment.sum()
   dat_mean = dat_mean.reset_index()
   df_avg = dat_mean[dat_mean.Startyear == 2022]
   for i in range(dat_mean.Startyear.min(), dat_mean.Startyear.max()):
      df = dat_mean[(dat_mean.Startyear == i)|(dat_mean.Startyear == i+1)]
      df = df.groupby(["Purpose Code", "Sector", "Category", "Recipient"]).Commitment.sum()
      df = df.reset_index()
      df.Commitment = df.Commitment/2 
      df["Startyear"] = i
      df_avg = pd.concat([df_avg, df])
   
   df_avg["Value"] = df_avg["Commitment"]
   if year != "all":
      df_avg = df_avg[df_avg.Startyear == year]
   else:
      df_avg = df_avg
   
   return df_avg
   
app = Dash(external_stylesheets = [dbc.themes.LUX])

#Slider for year:
year_slider = dcc.Slider(
   2012, dat.Startyear.max(), step=None,
   marks = {
      2012: "Alle", 2013: "2013", 2014: "2014", 2015: "2015", 2016: "2016", 2017: "2017",
      2018: "2018", 2019: "2019", 2020: "2020", 2021: "2021", 2022: "2022"  
   }, value = 2012)

#Dropdown for value:
value_dropdown = dcc.Dropdown(options=["Zusagen", "Auszahlungen"],
                              value="Zusagen", style = {"textAlign": "center"}, clearable=False)

#Dropdown for country category:                            
category_dropdown = dcc.Dropdown(options=sorted(dat['Category'].unique()),
                                value="All", style = {"textAlign": "center"}, clearable=True,
                                searchable= True, placeholder='Alle Partnerkategorien')                            

app.layout = dbc.Container([
      dbc.Row([
         html.H1(children='Dashboard', style={'textAlign': 'center'})
      ]),
   
      dbc.Row([
         dbc.Col([
         category_dropdown, html.Br(), value_dropdown
         ], width = 6),
         ], justify = "center"),

      dbc.Row([
         dbc.Col([
         year_slider,
         ],  width = 6),
      ], justify = 'center'),

      dbc.Row([
       dcc.Graph(id = "map"),
      ]),

      dbc.Row([
         dbc.Col([html.H4("Empfänger auswählen:", style={'textAlign': 'center'}),
         dcc.Dropdown(id="country_dd", placeholder='Land auswählen',
         style = {"textAlign": "center"}, clearable=True)],
         width = 6)], justify = "center"),

      dbc.Row([ 
         dcc.Graph(id = "tree")
      ]),

      dbc.Row([
         dbc.Col([
            dbc.Card(
             dbc.CardBody([
               html.H4("Projektanzahl:", className="card-title"),
               html.H5(id="number_projects", style={"fontWeight": "bold"}),
             ]),
            ),    
      ]),
         dbc.Col([
            dbc.Card(
               dbc.CardBody([
               html.H4("Summe aller Projekte:", className="card-title"),
               html.H5(id="sum_projects", style={"fontWeight": "bold"}),
             ]),
            ),
      ]),
      ]),
    ])

#Funktion um nur Länder anzuzeigen, die in gewählter Kategorie sind:
@app.callback(
    Output("country_dd", "options"),
    [Input(category_dropdown, "value")],
)

def country_options(category_dropdown ):
    if (category_dropdown is None) | (category_dropdown == "All"):
      return sorted(dat['Recipient'].unique())
    else:
      df_temp = dat[dat.Category == category_dropdown]
      return sorted(df_temp['Recipient'].unique())

#Hauptfunktion, um Grafiken anzuzeigen:
@app.callback(
    [Output('map', 'figure'), Output("tree", "figure"), 
    Output("number_projects", "children"), Output("sum_projects", "children")],
    [Input(year_slider, 'value'), Input(category_dropdown, "value"), Input(value_dropdown, "value"), Input("country_dd", "value")]
)

def update_graph(year_slider, category_dropdown, value_dropdown, selected_country):
   #Account for cleared dropdown by assigning value if menu is cleared:
   if category_dropdown == None:
      category_dropdown = "All"
   if selected_country == None:
      selected_country = "All"

   if (year_slider != 2012) & (category_dropdown == "All"):
      dat_fil = dat[dat["Startyear"] == year_slider]
      dat_com = avg(dat, year_slider)
   if (year_slider == 2012) & (category_dropdown == "All"):
      dat_fil = dat
      dat_com = avg(dat, "all")
   if (year_slider == 2012) & (category_dropdown != "All"):
      dat_fil = dat[dat["Category"] == category_dropdown]
      dat_com = avg(dat, "all")
      dat_com = dat_com[dat_com["Category"] == category_dropdown]
   if (year_slider != 2012) & (category_dropdown != "All"):
      dat_fil = dat[(dat["Startyear"] == year_slider)&(dat["Category"] == category_dropdown)]
      dat_com = avg(dat, year_slider)
      dat_com = dat_com[dat_com["Category"] == category_dropdown]

   #Treemap for sectors:
   if value_dropdown == "Auszahlungen":
      df = dat_fil
   else:
      df = dat_com

   dat_tree = df.groupby(["Sector", "Purpose Code", "Recipient"])[["Value"]].sum()
   dat_tree = dat_tree.reset_index()

   if "All" in selected_country:
      figTree = px.treemap(dat_tree, path=[px.Constant("all"), 'Sector', 'Purpose Code'], 
                 values='Value', color='Sector')
   else:
      figTree = px.treemap(dat_tree[dat_tree["Recipient"] == selected_country], 
      path=[px.Constant("all"), 'Sector', 'Purpose Code'], values='Value', color='Sector')

   #Prepare data for map and display:
   dat_map = df.groupby(["Recipient"])[["Value"]].sum()
   dat_map = dat_map.reset_index()
   figMap = px.choropleth(dat_map, locations ="Recipient", locationmode="country names", 
   color_continuous_scale="Viridis", color="Value", range_color=(0, max(dat_map["Value"]*0.05)))
   figMap.update_layout(coloraxis_showscale=False)

   if "All" in selected_country:
      num_projects = len(df)
      string_projects = "{} für alle Empfänger".format(num_projects)
      sum_projects = round(df["Value"].sum()/1000000,2)
      string_projects_sum = "{} Mio. USD für alle Projekte".format(sum_projects)
   else:
      num_projects = len(df[df["Recipient"] == selected_country])
      string_projects = "{} in {}".format(num_projects, selected_country)
      sum_projects = round(df["Value"][df["Recipient"] == selected_country].sum()/1000000,2)
      string_projects_sum = "{} Mio. USD in {}".format(sum_projects, selected_country)

   return (figMap, figTree, string_projects, string_projects_sum)

if __name__ == '__main__':
    app.run_server(debug=True)