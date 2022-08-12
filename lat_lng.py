import requests
import json
import sqlite3
import os

class Geometry:
    def __init__(self) -> None:
        self.db = r'C:\Users\Alex\Desktop\hello\Python\cfs\cfs_1.db'
        self.table_1 = 'cfs_jobs'
        self.API_KEY = os.environ.get(key='GOOGLE_MAPS_API_KEY')
        self.added_data = 0

    def connect_and_scrape(self) -> None:
        con = sqlite3.connect(self.db)
        cur = con.cursor()

        # Select only the jobs with no latitude and longitude data
        cur.execute('''SELECT 
                            job_id,
                            job_city,
                            job_state,
                            job_postal_code 
                        FROM 
                            cfs_jobs
                        WHERE
                            latitude = -999;                        
                    ''')

        data = cur.fetchall()

        # Close the database connection
        con.close()

        for i in range(len(data)):
            self.job_id = data[i][0]

            job_city, job_state, job_postal_code = data[i][1], data[i][2], str(data[i][3])

            job_concat = job_city + ' ' + job_state + ' ' + job_postal_code

            my_search_term = '%20'.join(job_concat.split(' '))

            self.get_lat_lng(s=my_search_term)

    def get_lat_lng(self, s: str) -> None:
        url = f'https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={s}&inputtype=textquery&fields=geometry&key={self.API_KEY}'

        r = requests.get(url=url)

        my_json = json.loads(s=r.text)

        if my_json['candidates']:
            lat = my_json['candidates'][0]['geometry']['location']['lat']
            lng = my_json['candidates'][0]['geometry']['location']['lng']
            print(f'Adding lat and lng data to {self.job_id}...')
            self.added_data += 1
            self.add_lat_lng_to_db(lat=lat, lng=lng)
        else:
            print(f'No data found for {url}')

    def add_lat_lng_to_db(self, lat: float, lng: float) -> None:
        con = sqlite3.connect(self.db)
        cur = con.cursor()

        # Update the latitude and longitude to actual values for the appropriate job_id
        cur.execute(f'''UPDATE {self.table_1} 
                        SET latitude = {lat},
                            longitude = {lng}
                        WHERE
                            job_id = '{self.job_id}';
                        ''')

        # Commit the changes
        con.commit()

        # Close the database connection
        con.close()

    def show_results(self) -> None:
        return f'\nAdded {self.added_data} rows of lat & lng data to the sqlite3 database!'
          
c = Geometry()
c.connect_and_scrape()
print(c.show_results())