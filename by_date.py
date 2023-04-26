import requests
import datetime as dt
from datetime import datetime

# Helper function
def get_navigation(link_list):
    current_link = ''
    next_link = ''
    last_link = ''
    for link_info in link_list:
        if 'rel="current"' in link_info:
            current_link = link_info.split(';')[0].strip('<>')
        if 'rel="next"' in link_info:
            next_link = link_info.split(';')[0].strip('<>')
        if 'rel="last"' in link_info:
            last_link = link_info.split(';')[0].strip('<>')
    return current_link, next_link, last_link
    
def z_to_dt(z):
    return datetime.strptime(z, '%Y-%m-%dT%H:%M:%SZ')

def dt_to_z(dto):
    return dto.strftime('%Y-%m-%dT%H:%M:%SZ')

def dt_to_html(dto):
    return dt_to_z(dto).replace(':', '%3A')
    

# Parameters
INSTITUTION_URL = "https://institution.instructure.com"
API_URL = INSTITUTION_URL + '/api/v1'
API_KEY = "KEY"
auth = {"Authorization": "Bearer {}".format(API_KEY)}
coursenum = 1

# Set up connection
session = requests.Session()

# Get all grade change events for the course
by_course = []
url = API_URL + '/audit/grade_change?course_id={}&per_page=100'.format(coursenum)

while True:
    response = session.get(url, headers = auth)
    current_link, next_link, last_link = get_navigation(response.headers['link'].split(','))
    by_course = by_course + response.json()['events']

    if current_link == last_link:
        break
    url = next_link

# Get all grade change events for the course by date
by_date = []
first_date = dt.datetime(2100, 1, 1)
last_date = dt.datetime(2000, 1, 1)
one_day = dt.timedelta(days = 1)
one_sec = dt.timedelta(seconds = 1)
delta = one_day - one_sec

for event in by_course:
    if z_to_dt(event['created_at']) < first_date:
        first_date = z_to_dt(event['created_at'])
    if z_to_dt(event['created_at']) > last_date:
        last_date = z_to_dt(event['created_at'])

current_date = first_date
while current_date < last_date:
    url = API_URL + '/audit/grade_change?course_id={}&start_time={}&end_time={}&per_page=100'.format(coursenum, dt_to_html(current_date), dt_to_html(current_date + delta))
    print(first_date, current_date, current_date + delta, last_date)
    while True:
        response = session.get(url, headers = auth)
        current_link, next_link, last_link = get_navigation(response.headers['link'].split(','))
        
        by_date = by_date + response.json()['events']
        if current_link == last_link:
            break
        url = next_link

    current_date = current_date + one_day
    
# Compare the results
print(len(by_course), len(by_date))

yes_date_no_course = []
for event in by_date:
    if event not in by_course:
        yes_date_no_course.append(event)

yes_course_no_date = []
for event in by_course:
    if event not in by_date:
        yes_course_no_date.append(event)

  
