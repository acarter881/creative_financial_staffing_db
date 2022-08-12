import matplotlib.pyplot as plt
import pandas as pd
import sqlite3
import datetime
from mpl_toolkits.basemap import Basemap

today = datetime.date.today().strftime('%B %d, %Y')

# DataFrame of Latitude and Longitude
columns = [
    'Latitude',
    'Longitude',
]

con = sqlite3.connect(r'C:\Users\Alex\Desktop\hello\Python\cfs\cfs_1.db')
cur = con.cursor()

cur.execute('''SELECT 
                   latitude,
                   longitude  
               FROM 
                   cfs_jobs
               WHERE
                   job_industry = 'Information Technology'
                   AND job_salary_range_low != ''
                   AND latitude != -999;
           ''')

data = cur.fetchall()

con.close()

df = pd.DataFrame(data=data, columns=columns)

fig = plt.figure(figsize=(15,12))

m = Basemap(
    projection='mill',
    llcrnrlat=14,
    urcrnrlat=56,
    llcrnrlon=-140,
    urcrnrlon=-52,
    resolution='c'
    )

m.drawcoastlines()
m.drawcountries(color='black', linewidth=1)
m.drawstates(color='black', linewidth=1)
m.drawmapboundary(fill_color='aqua')
m.fillcontinents(color='lightgreen', lake_color='aqua')

# m.etopo()
m.scatter(df['Longitude'].tolist(), df['Latitude'].tolist(), latlon=True, s=30, c='red', marker='.', edgecolor='k')
# m.bluemarble()
# m.drawcounties(color='orange')
# m.drawrivers(color='blue')

plt.title(label=f'CFS Jobs (Salaried) - As of {today}', fontsize=20, color='white')
plt.show()
