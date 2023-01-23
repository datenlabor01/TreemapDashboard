from dash import Dash, html, dcc, Input, Output
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

dat = pd.read_csv("https://github.com/datenlabor01/app/blob/main/df_oda_ges.csv?raw=true")
dat["Value"] = dat["USD_Disbursement"]

app = Dash(external_stylesheets = [dbc.themes.LUX])

#Slider for year:
year_slider = dcc.Slider(
   2012, dat.YEAR.max(), step=None,
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

text = "Das Dashboard stellt die ODA-Daten des BMZ nach Empfänger und Sektoren für 2013-2021 in Mio. EUR dar. Auszahlung bezieht sich auf Disbursements und Zusage auf Commitments in der ODA-Methodik. Alle Projekte sind nach dem ODA-Melder BMZ gefiltert, was alle ODA-Leistungen umfasst, die mit Haushaltsmitteln des BMZ finanziert wurden."

app.layout = dbc.Container([
      dbc.Row([
         html.Div(html.Img(src="https://github.com/datenlabor01/app/blob/ba5a7436a77d273baf78108d13a288600abd66ee/logo.png?raw=true", style={'height':'80%', 'width':'20%'})
         )], style={'textAlign': 'center'}),

      dbc.Row([
         dbc.Col([
         html.H2(children='Dashboard', style={'textAlign': 'center'}),
         dbc.Badge(text, className="text-wrap", style={"width": "50%", 'textAlign': 'center'})], style={'textAlign': 'center'}
         )]),

      dbc.Row([
         dbc.Col([
         category_dropdown, html.Br(), value_dropdown, html.Br(),
         ], width = 6),
         ], justify = "center"),

      dbc.Row([
         dbc.Col([
         year_slider],  width = 6),
      ], justify = 'center'),

      dbc.Row([
       dcc.Graph(id = "map")
      ]),

      dbc.Row([
         dbc.Col([
         html.P("Auswahl Empfänger für Filtern der Treemap:", style={'textAlign': 'center'}),
         dcc.Dropdown(id="country_dd", placeholder='Alle Empfänger',
         style = {"textAlign": "center"}, clearable=True)],
         width = 6)], justify = "center"), html.Br(),

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
      ], width = 5),
      ], justify = "center"),

      dbc.Row([
         dcc.Graph(id = "tree")
      ]),
    ])

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
   #Account for cleared dropdown by assigning value if menu is cleared:
   if category_dropdown == None:
      category_dropdown = "All"
   if selected_country == None:
      selected_country = "All"

   if (year_slider != 2012) & (category_dropdown == "All"):
      dat_fil = dat[dat["YEAR"] == year_slider]
   if (year_slider == 2012) & (category_dropdown == "All"):
      dat_fil = dat
   if (year_slider == 2012) & (category_dropdown != "All"):
      dat_fil = dat[dat["Category"] == category_dropdown]
   if (year_slider != 2012) & (category_dropdown != "All"):
      dat_fil = dat[(dat["YEAR"] == year_slider)&(dat["Category"] == category_dropdown)]

   #Treemap for sectors:
   if value_dropdown == "Auszahlungen":
      dat_fil["Value"] = dat_fil["USD_Disbursement"]
      df = dat_fil
   else:
      dat_fil["Value"] = dat_fil["USD_Commitment"]
      df = dat_fil

   if (selected_country != "All") & (len(df[df["RecipientName"] == selected_country]["Category"] == category_dropdown) == 0) & (category_dropdown != "All"):
      selected_country = "All"

   dat_tree = df.groupby(["Sector", "Purpose", "RecipientName"])[["Value"]].sum()
   dat_tree = dat_tree.reset_index()

   if "All" in selected_country:
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
   #figMap.update_layout(coloraxis_showscale=False)

   if "All" in selected_country:
      num_projects = len(df)
      string_projects = "{} für alle Empfänger".format(num_projects)
      sum_projects = round(df["Value"].sum(),2)
      string_projects_sum = "{} Mio. EUR für alle Projekte".format(sum_projects)
   else:
      num_projects = len(df[df["RecipientName"] == selected_country])
      string_projects = "{} in {}".format(num_projects, selected_country)
      sum_projects = round(df["Value"][df["RecipientName"] == selected_country].sum(),2)
      string_projects_sum = "{} Mio. EUR in {}".format(sum_projects, selected_country)

   return (figMap, figTree, string_projects, string_projects_sum)

if __name__ == '__main__':
    app.run_server(debug=True)
