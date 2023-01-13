import pandas as pd

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
dat = dat.astype({'Sector':'int'})
dat["Sector"] = dat.Sector.map(dic_dac)

#Get the start and end year for each activity:
dat["Startyear"] = pd.DatetimeIndex(dat[dat.columns[10]]).year
dat["Endyear"] = pd.DatetimeIndex(dat[dat.columns[11]]).year

#Create column with recipients and add countries and map categories: 
dat["Recipient"] = dat[dat.columns[3]]
dat["Category"] = dat["Recipient"].map(country)
#For Regions add category name "Region" and fill entry:
dat.loc[dat.Recipient.isnull() == True, "Category"] = "Region"
dat.loc[dat.Recipient.isnull() == True, "Recipient"] = dat[dat.columns[0]]
#Add for remaining countries category:
dat.loc[dat.Category.isnull() == True,  "Category"] = "Kein Partnerland"
#Simplify column names for disbursement and commitment:
dat["Disbursement"] = dat[dat.columns[37]]
dat["Commitment"] = dat[dat.columns[36]]

dat = dat[["Startyear", "Endyear", "Disbursement", "Commitment", "Purpose Code", 
"Sector", "Recipient", "Category", "Maßnahmenstatus"]]
#Discard years before 2013:
dat = dat[dat["Startyear"] > 2012]
dat["Value"] = dat["Disbursement"]
dat.to_csv("appdata.csv", index=False)