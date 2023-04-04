from dash import Dash, html, dcc, Input, Output, State
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

dat = pd.read_csv("https://github.com/datenlabor01/TreemapDashboard/blob/main/df_oda_ges.csv?raw=true")
dat["Value"] = dat["USD_Disbursement"]

#Build two-year average
def avg(dat, year):

   dat_mean = dat.groupby(["YEAR", "Purpose Code", "Sector", "Category", "Recipient"]).Commitment.sum()
   dat_mean = dat_mean.reset_index()
   df_avg = dat_mean[dat_mean.YEAR == 2022]
   for i in range(dat_mean.YEAR.min(), dat_mean.YEAR.max()):
      df = dat_mean[(dat_mean.YEAR == i)|(dat_mean.YEAR == i+1)]
      df = df.groupby(["Purpose Code", "Sector", "Category", "Recipient"]).Commitment.sum()
      df = df.reset_index()
      df.Commitment = df.Commitment/2 
      df["YEAR"] = i
      df_avg = pd.concat([df_avg, df])
   
   df_avg["Value"] = df_avg["Commitment"]
   if year != "all":
      df_avg = df_avg[df_avg.YEAR == year]
   else:
      df_avg = df_avg
   
   return df_avg
   
app = Dash(external_stylesheets = [dbc.themes.LUX])

#Slider for year:
year_slider = dcc.Slider(
   2012, dat.YEAR.max(), step=None,
   marks = {
      2012: "Alle", 2013: "2013", 2014: "2014", 2015: "2015", 2016: "2016", 2017: "2017",
      2018: "2018", 2019: "2019", 2020: "2020", 2021: "2021", 2022: "2022"  
   }, value = 2012, included = False)

#Dropdown for value:
value_dropdown = dcc.Dropdown(options=["ODA-Zusagen", "Auszahlungen"],
                              value="ODA-Zusagen", style = {"textAlign": "center"}, clearable=False)

#Dropdown for country category:                            
category_dropdown = dcc.Dropdown(options=sorted(dat['Category'].unique()),
                                value="All", style = {"textAlign": "center"}, clearable=True,
                                searchable= True, placeholder='Alle Partnerkategorien')                            

text = "Das Dashboard stellt die ODA-Daten des BMZ nach Empfänger und Sektoren in Mio. EUR dar. Zusagen bezieht sich auf Commitments nach ODA-Systematik, Auszahlungen stellt die Brutto-ODA dar. Bitte beachten Sie die Hinweise unter 'Über diese App'."
text2 = "Diese Anwendung wird als Prototyp vom BMZ Datenlabor angeboten. Sie kann Fehler enthalten und it als alleinige Entscheidungsgrundlage nicht geeignet. Außerdem können Prototypen ausfallen oder kurzfristig von uns verändert werden. Sichern Sie daher wichtige Ergebnisse per Screenshot oder Export. Die Anwendung ist vorerst intern und sollte daher nicht ohne Freigabe geteilt werden. Wenden Sie sich bei Fragen gerne an datenlabor@bmz.bund.de"

app.layout = dbc.Container([
      dbc.Row([
         html.Div(html.Img(src="https://raw.githubusercontent.com/datenlabor01/TreemapDashboard/main/logo.png", style={'height':'80%', 'width':'20%'})
         )], style={'textAlign': 'center'}),
      
      dbc.Row([
         dbc.Col([ 
         html.H2(children='Treemap-Dashboard', style={'textAlign': 'center'}),
         dbc.Badge(text, className="text-wrap", style={"width": "50%", 'textAlign': 'center'})], style={'textAlign': 'center'}
         )]),

      dbc.Row([
         dbc.Button(children = "Über diese App", id = "textbutton", color = "light", className = "me-1",
                    n_clicks=0, style={'textAlign': 'center', "width": "30rem"})
      ], justify = "center"),

      dbc.Row([
            dbc.Collapse(dbc.Card(dbc.CardBody([
               dbc.Badge(text2, className="text-wrap"),
               ])), id="collapse", style={'textAlign': 'center', "width": "40rem"}, is_open=False),
      ], justify = "center"),
      
      dbc.Row([
         dbc.Col([
         category_dropdown, html.Br(), value_dropdown,
         ], width = 6),
         ], justify = "center"),

      dbc.Row([
         dbc.Col([year_slider],  width = 6),
      ], justify = 'center'),

      dbc.Row([
       dcc.Graph(id = "map")
      ]),

      dbc.Row([
         dbc.Col([
         html.P("Auswahl Empfänger für Filtern der Treemap:", style={'textAlign': 'center'}),
         dcc.Dropdown(id="country_dd", placeholder='Alle Empfänger',
         style = {"textAlign": "center"}, clearable=True), html.Br()],
         width = 6)], justify = "center"),

      dbc.Row([
         dbc.Col([
            dbc.Card(
             dbc.CardBody([
               html.H4("Anzahl der Projekte:", className="card-title"),
               html.H5(id="number_projects", style={"fontWeight": "bold", "border-radius": "2%"}),
             ]),
            ), 
      ], width = 5),
      
         dbc.Col([
            dbc.Card(
               dbc.CardBody([
               html.H4("Summe der Projekte:", className="card-title"),
               html.H5(id="sum_projects", style={"fontWeight": "bold"}),
             ]),
            ),
      ], width = 6),
      ], justify = "center"),

      dbc.Row([ 
         dcc.Graph(id = "tree")]),
    ])

#Für Anzeigen des Textes:
@app.callback(
    Output("collapse", "is_open"),
    [Input("textbutton", "n_clicks")],
    [State("collapse", "is_open")],
)

def collapse(n, is_open):
   if n:
      return not is_open
   return is_open

#Funktion um nur Länder anzuzeigen, die in gewählter Kategorie sind:
@app.callback(
    Output("country_dd", "options"),
    [Input(category_dropdown, "value")],
)

def country_options(category_dropdown ):
    if (category_dropdown is None) | (category_dropdown == "All"):
      return sorted(dat['RecipientName'].unique())
    else:
      df_temp = dat[dat.Category == category_dropdown]
      return sorted(df_temp['RecipientName'].unique())

#Hauptfunktion, um Grafiken anzuzeigen:
@app.callback(
    [Output('map', 'figure'), Output("tree", "figure"), 
    Output("number_projects", "children"), Output("sum_projects", "children")],
    [Input(year_slider, 'value'), Input(category_dropdown, "value"), Input(value_dropdown, "value"), Input("country_dd", "value")]
)

def update_graph(year_slider, category_dropdown, value_dropdown, selected_country):

   if year_slider == 2012:
      dat_fil = dat
   else:
      dat_fil = dat[dat["YEAR"] == year_slider]

   if (category_dropdown == "All") | (category_dropdown == None):
      dat_fil = dat_fil
   else:
      dat_fil = dat_fil[dat_fil["Category"] == category_dropdown]

   #Treemap for sectors:
   if value_dropdown == "Auszahlungen":
      dat_fil["Value"] = dat_fil["USD_Disbursement"]
      df = dat_fil
   else:
      dat_fil["Value"] = dat_fil["USD_Commitment"]
      df = dat_fil

   dat_tree = df.groupby(["Sector", "Purpose", "RecipientName"])[["Value"]].sum()
   dat_tree = dat_tree.reset_index()

   if selected_country == None:
      figTree = px.treemap(dat_tree[dat_tree.Value > 0.01], path=[px.Constant("Total"), 'Sector', 'Purpose'], 
                 values='Value', color='Sector')
   else:
      figTree = px.treemap(dat_tree[dat_tree["RecipientName"] == selected_country], 
      path=[px.Constant("Total"), 'Sector', 'Purpose'], values='Value', color='Sector')

   #Prepare data for map and display:
   dat_map = df.groupby(["RecipientName"])[["Value"]].sum()
   dat_map = dat_map.reset_index()
   figMap = px.choropleth(dat_map, locations ="RecipientName", locationmode="country names", 
   color_continuous_scale="Viridis", color="Value", range_color=(min(dat_map["Value"]), max(dat_map["Value"]*0.05)))

   if selected_country == None:
      num_projects = len(df)
      string_projects = "{} für alle Empfänger".format(num_projects)
      sum_projects = round(df["Value"].sum(),2)
      string_projects_sum = "{} Mio. EUR für alle Empfänger nach {}".format(sum_projects, value_dropdown)
   else:
      num_projects = len(df[df["RecipientName"] == selected_country])
      string_projects = "{} in {}".format(num_projects, selected_country)
      sum_projects = round(df["Value"][df["RecipientName"] == selected_country].sum(),2)
      string_projects_sum = "{} Mio. EUR in {} nach {}".format(sum_projects, selected_country, value_dropdown)

   return (figMap, figTree, string_projects, string_projects_sum)

if __name__ == '__main__':
    app.run_server(debug=True)
