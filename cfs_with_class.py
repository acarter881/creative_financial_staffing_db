import requests
import time
import re
import sqlite3
import json
from tqdm import tqdm
from bs4 import BeautifulSoup

class CreativeFinancialStaffing:
    def __init__(self) -> None:
        self.db = r'C:\Users\Alex\Desktop\hello\Python\cfs\cfs_1.db'
        self.table_1 = 'cfs_jobs'
        self.base_url = 'https://www.cfstaffing.com'
        self.job_url = 'https://www.cfstaffing.com/index.php/jobs/search/'
        self.headers = {
            'accept-language': 'en-US,en;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'origin': 'https://www.cfstaffing.com',
            'referer': 'https://www.cfstaffing.com/index.php/jobs/search/',
            'dnt': '1',
        }
        self.features = 'html.parser'
        self.cfs_jobs = list()
        self.job_ids_to_delete = list()
        # RegEx to retrieve the job ID in URLs such as "https://www.cfstaffing.com/index.php/jobs/detail/OH/North Canton/Bookkeeper/07292022-OHA-KM6/wpbh_Id/"
        self.job_id_regex = r'.+\/(.+)\/wpbh_[iI]d'
        self.page_not_found_regex = r'.*Page not found.*'
        
    def __repr__(self) -> str:
        return 'This script is intended to analyze job data from a staffing company.'

    def check_db_jobs(self) -> list:
        con = sqlite3.connect(self.db)
        cur = con.cursor()

        cur.execute('''SELECT
                        job_id
                    FROM
                        cfs_jobs;
                    ''')

        self.data = cur.fetchall()

        # Close the database connection
        con.close()

        return self.data

    def job_urls(self, stop: int, sleep_time: float) -> str:
        """

        Sending POST requests to the main job webpage and retrieving the job URL, unique ID, and job title
        
        """
        self.markup = ''

        for i in tqdm(range(1, stop, 1)):
            payload = {
            'wpbh_search': '1',
            'wpbh_term': '',
            'wpbh_category':'',
            'wpbh_location':'',
            'wpbh_job_number': '',
            'wpbh_jobdate': '',
            'wpbh_sort': '',
            'wpbh_page': {i},
        }
            r = requests.post(url=self.job_url, data=payload, headers=self.headers)

            time.sleep(sleep_time)

            if re.match(pattern=r'.+(There are currently no jobs that meet your search requirement\.).*', string=r.text[:300]):
                break
            else:
                self.markup += r.text

        return self.markup

    def parse_job_urls(self) -> list:
        soup = BeautifulSoup(markup=self.markup, features=self.features)

        for a in soup.find_all(name='a', attrs={'href': re.compile(pattern='/index\.php/jobs/detail/.+')}):
            job_url = self.base_url + a['href']
            id = re.search(pattern=self.job_id_regex, string=job_url).group(1)
            title = a.text.split('-')[0].title()
            
            # The "0" is for "is_scraped", showing that the job URL hasn't been scraped yet
            self.cfs_jobs.append((id, title, job_url, 0))

        return self.cfs_jobs

    def add_db_jobs(self) -> None:
        con = sqlite3.connect(self.db)
        cur = con.cursor()

        # Get the count of tables with a specific name
        cur.execute(f'''SELECT
                            COUNT(name)
                        FROM
                            sqlite_master 
                        WHERE 
                            type = 'table' 
                            AND name = '{self.table_1}'; 
                    ''')

        # Check if the table exists
        if cur.fetchone()[0] == 1:
            print('\nThe table already exists.\n')
        else:
            cur.execute(f'CREATE TABLE {self.table_1} (job_id TEXT NOT NULL PRIMARY KEY, job_title TEXT, job_url TEXT, is_scraped INTEGER);')

        # Add the jobs to the "cfs_jobs" table
        for job in self.cfs_jobs:
            # Check if the job is in the field "job_id"
            cur.execute(f'SELECT * FROM {self.table_1} WHERE job_id=:example;', {'example': job[0]})
            data = cur.fetchone()

            if data:
                pass
                # print(f'{job[0]} is ALREADY in the database')
            else:
                # Insert the job_id, job_title, and job_url into the "cfs_jobs" table
                insert_sql = f'''INSERT INTO 
                                    {self.table_1} (job_id, job_title, job_url, is_scraped) 
                                 VALUES (?, ?, ?, ?);
                              '''
                cur.execute(insert_sql, job)
                print(f'{job[0]} is being added to the database')
        
        # Commit the changes
        con.commit()

        # Close the database connection
        con.close()

    def get_job_details(self, url) -> None:
        r = requests.get(url=url, headers=self.headers)

        soup = BeautifulSoup(markup=r.text, features='html.parser')

        # Check for HTTP 404
        if re.search(pattern=self.page_not_found_regex, string=r.text):
            self.industry, self.city, self.state, self.postal_code, self.salary_low, self.salary_high, self.hourly_low, self.hourly_high, self.posted_date, self.job_desc = 'HTTP 404', '', '', '', '', '', '', '', '', ''
        else:
            # Find job_industry, job_city, job_state, and job_postal_code
            script = soup.find(name='script', attrs={'type': re.compile(r'application.+'), 'class': None})

            my_json = ''

            for line in script:
                my_json += line.strip()

            dummy_num = my_json.find('\"employmentType\"')

            my_json = "{" + my_json[dummy_num:]

            job_data = json.loads(s=my_json)

            # Industry
            self.industry = job_data['industry']

            # City
            self.city = job_data['jobLocation']['address']['addressLocality']

            # State
            self.state = job_data['jobLocation']['address']['addressRegion']

            # Postal Code
            self.postal_code = job_data['jobLocation']['address']['PostalCode']

            # Find the "job_salary_range_low", "job_salary_range_high", "job_hourly_range_low", and "job_hourly_range_high"
            divs = soup.find_all(name='div', attrs={'style': re.compile(pattern=r'^display.+')})

            self.has_wage = False

            for div in divs:
                if div.text.startswith('$'):
                    if 'hour' in div.text.lower():
                        # Hourly
                        try:
                            self.hourly_low, self.hourly_high = [int(item.strip().replace('$', '').replace('/hour', '').replace(',', '')) for item in div.text.lower().split('-')]
                        except ValueError as v:
                            print(v)
                            self.hourly_low = [int(item.strip().replace('$', '').replace('/hour', '')) for item in div.text.lower().split('-')]
                            self.hourly_high = self.hourly_low
                        finally:
                            self.salary_low, self.salary_high = '', ''
                            self.has_wage = True
                        break
                    else:
                        # Salary
                        try:
                            self.salary_low, self.salary_high = [int(item.strip().replace('$', '').replace(',', '')) for item in div.text.split('-')]
                        except ValueError as v:
                            print(v)
                            self.salary_low = [int(item.strip().replace('$', '').replace(',', '')) for item in div.text.split('-')][0]
                            self.salary_high = self.salary_low
                        finally:
                            self.hourly_low, self.hourly_high = '', ''
                            self.has_wage = True
                        break

            # Check if there are any wage-related data on the job post
            if self.has_wage == False:
                self.hourly_low, self.hourly_high, self.salary_low, self.salary_high = '', '', '', ''

            # Find the job's posted date
            self.posted_date = re.search(pattern=r'"date[pP]osted":\s?"(.+)"', string=r.text).group(1)

            # Find the job description
            self.job_desc = ''

            for item in soup.find(name='div', attrs={'class': re.compile(pattern=r'wp_bullhorn_detail_FullDescription')}):
                try:
                    if not item.text.startswith('Id:'):
                        self.job_desc += item.text
                except AttributeError:
                    pass

            self.job_desc = self.job_desc.split('\n')

            self.job_desc = '\n'.join([line for line in self.job_desc if line != ''])

            # Account for "UnicodeEncodeError: 'utf-8' codec can't encode character '\ud83d' in position 677: surrogates not allowed" and its varieties
            self.job_desc = self.job_desc.encode('utf-8', 'replace').decode()

            self.tuple = (1, 
                        self.industry, 
                        self.city, 
                        self.state, 
                        self.postal_code, 
                        self.salary_low,
                        self.salary_high,
                        self.hourly_low,
                        self.hourly_high,
                        self.posted_date,
                        self.job_desc 
                        )

    def connect_and_scrape(self, sleep_time: float) -> None:
        con = sqlite3.connect(self.db)
        cur = con.cursor()

        # TODO: If you'd like, you can find all the jobs that currently have salary data and double check that the salary is correct.
        # The code to determine salary is correct, but it used to be incorrect. This means that some jobs in the database may have incorrect salary data.
        cur.execute('''SELECT 
                            * 
                       FROM 
                            cfs_jobs 
                       WHERE 
                            is_scraped = 0;
                    ''')
       
        data = cur.fetchall()

        for job in tqdm(data):
            time.sleep(sleep_time)
            self.job_id = job[0]
            self.job_title = job[1]
            self.job_url = job[2]
            print(self.job_url)
            self.get_job_details(url=self.job_url)

            # Set is_scraped to "1" and input dummy values (i.e., -999) for latitude and longitude
            sql = (f'''UPDATE 
                            {self.table_1} 
                       SET 
                            is_scraped = 1,
                            job_industry = ?,
                            job_city = ?,
                            job_state = ?,
                            job_postal_code = ?,
                            job_salary_range_low = ?,
                            job_salary_range_high = ?,
                            job_hourly_range_low = ?,
                            job_hourly_range_high = ?,
                            job_posted_date = ?,
                            job_description = ?,
                            latitude = -999,
                            longitude = -999
                       WHERE
                            job_id = ?;
                    ''')

            cur.execute(sql, [self.industry, 
                              self.city, 
                              self.state, 
                              self.postal_code, 
                              self.salary_low, 
                              self.salary_high, 
                              self.hourly_low, 
                              self.hourly_high, 
                              self.posted_date, 
                              self.job_desc, 
                              self.job_id]
                        )
        
        # Commit the changes
        con.commit()

        # Close the database connection
        con.close()

    def check_jobs_against_db(self) -> None:
        # For each job_id in the database
        for db_job in self.data:
            # If the job_id in the database is NOT in a list of all of the job_ids from the current website
            if db_job[0] not in [web_job[0] for web_job in self.cfs_jobs]:
                self.job_ids_to_delete.append(db_job[0])

        return self.job_ids_to_delete

    def delete_db_jobs(self) -> None:
        deleted_jobs = 0

        con = sqlite3.connect(self.db)
        cur = con.cursor()

        for job_id in self.job_ids_to_delete:
            deleted_jobs += 1
            print(f'Removing `{job_id}` from the database...')
            cur.execute(f'''DELETE FROM cfs_jobs
                            WHERE job_id = '{job_id}';              
                         ''')

        print(f'\nThere were {deleted_jobs} jobs removed from the database.')
        
        # Commit the changes
        con.commit()

        # Close the database connection
        con.close()

# Instantiate the class and run the necessary functions
if __name__ == '__main__':
    # Create an instance of the main class
    c = CreativeFinancialStaffing()

    # Get a list of all jobs currently in the sqlite3 database
    c.check_db_jobs()

    # Scrape the first 100 pages of job data from https://www.cfstaffing.com/index.php/jobs/search/
    # I would keep "stop" at 100. Setting it lower may delete active jobs from the sqlite3 database
    c.job_urls(stop=100, sleep_time=0.1)

    # Parse the HTML from "job_urls" to get all job IDs, job titles, and job URLs from the current website
    c.parse_job_urls()

    # Compare the jobs in the database to the jobs from the current website
    # Any jobs that are in the database but not on the current website are added to a list of database jobs to be deleted
    c.check_jobs_against_db()

    # Delete the database jobs found in "check_jobs_against_db"
    c.delete_db_jobs()

    # Add jobs to the sqlite3 database. These are jobs found on the current website that are not in the sqlite3 database
    c.add_db_jobs()

    # Get all details (except for latitude and longitude) for all the new jobs that were added to the sqlite3 database
    c.connect_and_scrape(sleep_time=0.1)