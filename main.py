import requests
import re
from bs4 import BeautifulSoup
import datetime
import json

# Function to connect to the website using the provided formation code
def connect_to_website(code_formation):
    data = {
        'loginstudent': code_formation,
        'cookieetudiant': '1',
        'logintype': 'student',
    }

    session = requests.Session()

    # Send a POST request to the website with the formation code
    response = session.post('https://edt.univ-evry.fr/index.php', data=data)
    if response.status_code != 200:
        print("Error connecting to the website.")
        exit()

    print("Connection successful.")
    return session

# Function to get the current student ID from the website session
def get_current_student(session):
    soup = BeautifulSoup(session.get('https://edt.univ-evry.fr/index.php').text, 'html.parser')
    href_value = soup.find('area', alt='seance').get('href')
    current_student = re.search(r'student=(\d+)', href_value).group(1)
    return current_student

# Function to extract the available modules for the current student
def extract_modules(session, current_student):
    response = session.get(f'https://edt.univ-evry.fr/module_etudiant.php?current_student={current_student}')
    soup = BeautifulSoup(response.text, 'html.parser')
    select_menu = soup.find('select', {'name': 'selec_module'})

    if select_menu:
        options = select_menu.find_all('option')
        modules = [option['value'] for option in options]
        return modules
    else:
        print("Dropdown menu not found in the HTML.")
        return []

# Function to extract the classes
def extract_classes(session, current_student, module, current_week):
    response_module = session.get(f'https://edt.univ-evry.fr/module_etudiant.php?current_student={current_student}&selec_module={module}')
    soup = BeautifulSoup(response_module.text, 'html.parser')
    classes = [
        {
            'date': datetime.datetime.strptime(columns[0].text.strip().split(' ')[1], '%d-%m-%Y').strftime('%d-%m-%Y'),
            'week': columns[1].text.strip(),
            'formation': columns[2].text.strip(),
            'type': columns[3].text.strip(),
            'module': columns[4].text.strip(),
            'professor': columns[5].text.strip(),
            'classroom': columns[6].text.strip(),
            'start_time': columns[8].text.strip(),
            'duration': columns[9].text.strip(),
        }
        for tr_tag in soup.find_all('tr')[1:]
        if (columns := tr_tag.find_all('td')) and columns[1].text.strip() == str(current_week)
    ]
    return classes

# Function to save the extracted classes to a JSON file
def save_classes_to_json(classes):
    classes = sorted(classes, key=lambda x: (datetime.datetime.strptime(x['date'], '%d-%m-%Y'), datetime.datetime.strptime(x['start_time'], '%Hh%M')))
    with open(f'cours_week{datetime.datetime.now().isocalendar()[1]}.json', 'w', encoding='utf-8') as json_file:
        json.dump(classes, json_file, ensure_ascii=False, indent=2)
    print("Course information has been saved in cours.json")

# Main function
def main():
    code_formation = input("Enter the code of the formation (e.g., m1miai): ")
    session = connect_to_website(code_formation)
    current_student = get_current_student(session)
    modules = extract_modules(session, current_student)
    current_week = datetime.datetime.now().isocalendar()[1]

    all_classes = []

    # Extract classes for each module and add them to the list
    for module in modules:
        classes = extract_classes(session, current_student, module, current_week)
        all_classes.extend(classes)

    # Save the classes to a JSON file
    save_classes_to_json(all_classes)

if __name__ == "__main__":
    main()
