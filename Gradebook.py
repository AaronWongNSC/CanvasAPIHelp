import requests

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
    

# Parameters
INSTITUTION_URL = "https://institution.instructure.com"
API_URL = INSTITUTION_URL + '/api/v1'
API_KEY = "KEY"
auth = {"Authorization": "Bearer {}".format(API_KEY)}
coursenum = 1

# Set up connection
session = requests.Session()

# Get assignments
url = API_URL + '/courses/{}/assignments?per_page=100'.format(coursenum)
assignments = []
while True:
    response = session.get(url, headers = auth)
    current_link, next_link, last_link = get_navigation(response.headers['link'].split(','))
    assignments = assignments + response.json()

    if current_link == last_link:
        break
    url = next_link

assignment_list = [ assignment['id'] for assignment in assignments ]

# Get students
url = API_URL + '/courses/{}/enrollments?type[]=StudentEnrollment&per_page=100'.format(coursenum)
students = []
while True:
    response = session.get(url, headers = auth)
    current_link, next_link, last_link = get_navigation(response.headers['link'].split(','))
    students = students + response.json()

    if current_link == last_link:
        break
    url = next_link

student_list = [ student['user_id'] for student in students ]

# Create Gradebook by student and assignment
by_student_assignment = []
gradebook = {}
for student in students:
    for assignment in assignments:
        print(student['user_id'], assignment['id'])
        url = API_URL + '/audit/grade_change?course_id={}&assignment_id={}&student_id={}&per_page=100'.format(coursenum, assignment['id'], student['user_id'])
        response = session.get(url, headers = auth)
        
        if len(response.json()['events']) > 0:
            for event in response.json()['events']:
                by_student_assignment.append(event)
            gradebook.update({ (student['user_id'], assignment['id']): response.json()['events'][0]['grade_after']})
        else:
            gradebook.update({ (student['user_id'], assignment['id']): 'NA' })

# Create Gradebook by student
by_student = []
gradebook = {}
for student in students:
    for assignment in assignments:
        gradebook.update({ (student['user_id'], assignment['id']): 'NA' })

for student in students:
    print(student['user_id'])

    grade_change_events = []
    url = API_URL + '/audit/grade_change?course_id={}&student_id={}&per_page=100'.format(coursenum, student['user_id'])

    while True:
        response = session.get(url, headers = auth)
        current_link, next_link, last_link = get_navigation(response.headers['link'].split(','))
        grade_change_events = grade_change_events + response.json()['events']

        if current_link == last_link:
            break
        url = next_link

    for event in grade_change_events:
        by_student.append(event)
        if student['user_id'] in student_list and assignment['id'] in assignment_list:
            if gradebook[ ( student['user_id'], event['links']['assignment']) ] == 'NA':
                gradebook[ ( student['user_id'], event['links']['assignment']) ] = event['grade_after']

# Create Gradebook by course
gradebook = {}
for student in students:
    for assignment in assignments:
        gradebook.update({ (student['user_id'], assignment['id']): 'NA' })

grade_change_events = []
url = API_URL + '/audit/grade_change?course_id={}&per_page=100'.format(coursenum)

while True:
    response = session.get(url, headers = auth)
    current_link, next_link, last_link = get_navigation(response.headers['link'].split(','))
    grade_change_events = grade_change_events + response.json()['events']

    if current_link == last_link:
        break
    url = next_link

for count, event in enumerate(grade_change_events):
    if count % 100 == 0:
        print('{} of {}'.format( count, len(grade_change_events) ))
    if int(event['links']['student']) in student_list and event['links']['assignment'] in assignment_list:
        if gradebook[ ( int(event['links']['student']), event['links']['assignment']) ] == 'NA':
            gradebook[ ( int(event['links']['student']), event['links']['assignment']) ] = event['grade_after']

'''
# Export Gradebook
with open('gradebook.csv', 'w') as outfile:
    outfile.write(',Assignment,')
    for assignment in assignments:
        outfile.write('{} ({}),'.format(assignment['name'], assignment['id']))
    outfile.write('\n')
    
    for student in students:
        outfile.write('{} ({}),'.format(student['user']['name'], student['user_id']))
        for assignment in assignments:
            outfile.write('{},'.format(gradebook[ (student['user_id'], assignment['id']) ]))
        outfile.write('\n')
'''

print(len(by_student_assignment))
print(len(by_student))
print(len(grade_change_events))
