# creative_financial_staffing_db
Database of Creative Financial Staffing's jobs

## What is this repository?
This repository displays the Python code for downloading all current jobs from [Creative Financial Staffing](https://www.cfstaffing.com/index.php/jobs/search/#getJobs), a leading, employee-owned staffing firm founded by CPA firms (according to [this page](https://www.cfstaffing.com/index.php/about/join-our-team/)) and doing the following:
### `cfs_with_class.py`
* Storing the job data in an [sqlite3](https://docs.python.org/3/library/sqlite3.html) database. The job data include the following:
    * Job ID
    * Job Title
    * Job URL
    * Job Industry
    * City
    * State
    * Postal Code
    * Salary Range (Low)
    * Salary Range (High)
    * Hourly Range (Low)
    * Hourly Range (High)
    * Date Posted
    * Job Description
* Updating (i.e., adding new jobs and deleting jobs that are no longer on the website) the sqlite3 database.
### `lat_lng.py`
* Using Google's [Places API](https://developers.google.com/maps/documentation/places/web-service/search-find-place#maps_http_places_findplacefromtext_mca-py) (making Find Place requests) to retrieve the latitude and longitude based on each job's city, state, and zip code.
### `basic_map.py`
* Plotting the latitude and longitude on a map and displaying the map.
## Screenshots
* sqlite3 database (using [SQLiteStudio](https://sqlitestudio.pl/))
![Imgur](https://imgur.com/fZ8Ncep.jpg)
* Output from `basic_map.py`
![Imgur](https://imgur.com/zeRkwT7.jpg)
* Find HTTP 404s (i.e., links to jobs that are no longer valid)
![Imgur](https://imgur.com/FWgnWjd.jpg)
* Find errors within the job description or job's metadata
    * Salary irregularities
![Imgur](https://imgur.com/Yb1KAT4.jpg)
![Imgur](https://imgur.com/v6ECg68.jpg)
    * Invalid postal codes
![Imgur](https://imgur.com/mB9IYpj.jpg)
## What else could we do?
* Find misspellings in job descriptions.
* Generate thematic, interactive maps and host them online (e.g., a dashboard).
* Analyze the text in job descriptions, extracting metrics such as the most frequently used words.
