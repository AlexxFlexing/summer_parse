import requests
import json
from fake_useragent import UserAgent
from converter import process_salary_hh
import msgpack
import hashlib
import mysql.connector
from settings import dbuser, dbpass, dbhost, dbdb
import time
import csv
import os


class idkhowtoproperlydelimit(csv.Dialect): #rework probably
    delimiter = ';'
    quotechar = '"'
    escapechar = '\\'
    doublequote = True
    skipinitialspace = False
    lineterminator = '\n'
    quoting = csv.QUOTE_ALL

csv.register_dialect('own-tab', idkhowtoproperlydelimit)


con = mysql.connector.connect(
    user = dbuser,
    password = dbpass,
    host = dbhost,
    database = dbdb
)


def area_calc(area_input):
    match area_input:
        case 1: #moscow
            return '&area=1'
        case 2: #spb
            return '&area=2'
        case 3: #novosib
            return '&area=4'
        case 4: #ekb
            return '&area=3'
        case 5: #kazan
            return '&area=88'
        case 0: #no area
            return ''
        
def salary_calc(salary_input):
    if salary_input != 0:
        return f'&only_with_salary=true&salary={salary_input}'
    else:
        return ''
    
def exp_calc(exp_input):
    match exp_input:
        case 0:
            return ''
        case 1:
            return '&experience=noExperience'
        case 2:
            return '&experience=between1And3'
        case 3:
            return '&experience=between3And6'
        case 4:
            return '&experience=moreThan6'
        
def employment_calc(employment_input):
    match employment_input:
        case 0:
            return ''
        case 1:
            return '&employment=full'
        case 2:
            return '&employment=part'
        case 3:
            return '&employment=project'
        case 4:
            return '&employment=volunteer'
        case 5:
            return '&employment=probation'

def schedule_calc(schedule_input):
    match schedule_input:
        case 0:
            return ''
        case 1:
            return '&schedule=fullDay'
        case 2:
            return '&schedule=shift'
        case 3:
            return '&schedule=flexible'
        case 4:
            return '&schedule=remote'
        case 5:
            return '&schedule=flyInFlyOut'

salary_input = 0
string_input = ''

cursor = con.cursor()
query = 'INSERT INTO vacancies (vacancy_name, company_name, area, salary, vacancy_link, vacancy_hash, experience, schedule) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'

def hh_parse(string_input, area_input, salary_input, exp_input, employment_input, schedule_input):
    response = requests.get(url=f"https://api.hh.ru/vacancies?page=1&per_page=100&text={string_input}{area_calc(area_input=area_input)}{salary_calc(salary_input)}{exp_calc(exp_input)}{employment_calc(employment_input)}{schedule_calc(schedule_input)}", 
                            headers={'user-agent':UserAgent().random})
    response = response.content.decode() #string somehow
    response = json.loads(response)
    max_pages = response['pages']
    print(response['pages']) #pagination depth is capped at 2000 therefore page*per_page=2000
    data = []
    for i in range(1,max_pages):
        response = requests.get(url=f"https://api.hh.ru/vacancies?page={i}&per_page=100&text={string_input}{area_calc(area_input=area_input)}{salary_calc(salary_input)}{exp_calc(exp_input)}{employment_calc(employment_input)}{schedule_calc(schedule_input)}",
                            headers={'user-agent':UserAgent().random})
        response = response.content.decode()
        response = json.loads(response)
        for item in response['items']:
                salary = None
                if item["salary"] != None:
                    if item["salary"]["from"] == None:
                        salary = item["salary"]["to"]
                    else:
                        salary = item["salary"]["from"]
                    if item['salary']['currency'] != 'RUR':              
                        salary = process_salary_hh(salary, item["salary"]["currency"])       
                vacancy_data = {'title': item["name"], 'company': item["employer"]["name"], 'area': item["area"]["name"], 'link':item['alternate_url'], 'salary': salary, 'exp': item["experience"]['name'], 'schedule': item["schedule"]["name"]}
                msgpack_data = msgpack.packb(vacancy_data)
                hash_value = hashlib.sha256(msgpack_data).hexdigest()
                cursor.execute("SELECT * FROM vacancies WHERE vacancy_hash = %s", (hash_value,))
                if cursor.fetchone():
                    print("Duplicate hash value found. Skipping insert.")
                else:
                    cursor.execute(query, (item["name"], item["employer"]["name"], item["area"]["name"], salary, item['alternate_url'], hash_value, item["experience"]['name'], item["schedule"]["name"]))
                    con.commit()
                data.append(vacancy_data)
        time.sleep(5)
    csv_file_path = os.path.join("csv", "temp_hh_vacancies.csv")
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, dialect='own-tab')
        writer.writerow(["title", "employer", "salary", "area", "experience", "schedule", "vacancy link"])
        for row in data:
            writer.writerow([row['title'], row['company'], row['salary'], row['area'], row['exp'], row['schedule'], row['link']])

    matching_vacancies = {}
    for i, row in enumerate(data[:10]):
        matching_vacancies[f"vacancy_{i+1}"] = {
            "title": row['title'],
            "employer": row['company'],
            "salary": row['salary'],
            "area" : row['area'],
            "vacancy link" : row['link']
        }

    cursor.close()
    return matching_vacancies
