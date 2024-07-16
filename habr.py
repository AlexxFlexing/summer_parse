import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from converter import process_salary_habr
import time
import hashlib
import msgpack
import mysql.connector
from settings import dbuser, dbpass, dbhost, dbdb
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

cursor = con.cursor()
query = 'INSERT INTO vacancies (vacancy_name, company_name, area, salary, vacancy_link, vacancy_hash) VALUES (%s, %s, %s, %s, %s, %s)'

def area_calc(area_input):
    match area_input:
        case 1: #moscow
            return 'c_678'
        case 2: #spb
            return 'c_679'
        case 3: #novosib
            return 'c_717'
        case 4: #ekb
            return 'c_693'
        case 5: #kazan
            return 'c_698'
        case 0: #no area
            return 0
salary_input = 0
string_input = ''

def habr_parse(string_input, area_input, salary_input):
    soup = BeautifulSoup(requests.get(f'https://career.habr.com/vacancies?page=1&salary={salary_input}&locations[]={area_calc(area_input)}&q={string_input}&type=all', headers={'user-agent':UserAgent().random}).content, 'lxml')
    vacancies = soup.find_all('div', class_='vacancy-card__info')
    data = []
    for vacancy in vacancies:
        company = vacancy.find('a', class_="link-comp link-comp--appearance-dark").text
        title = vacancy.find('a', class_="vacancy-card__title-link").text
        salary = vacancy.find('div', class_="basic-salary").text
        area = vacancy.find('div', class_="vacancy-card__meta").find('a', class_="link-comp link-comp--appearance-dark")
        if area != None:
            area = area.text
        if salary != None:
            salary = process_salary_habr(salary)
        link = "https://career.habr.com"+vacancy.find('a', class_="vacancy-card__title-link")["href"]
        vacancy_data = {'title': title, 'company': company, 'area':area, 'salary':salary, 'link':link}
        msgpack_data = msgpack.packb(vacancy_data)
        hash_value = hashlib.sha256(msgpack_data).hexdigest()
        cursor.execute("SELECT * FROM vacancies WHERE vacancy_hash = %s", (hash_value,))
        if cursor.fetchone():
            print("Duplicate hash value found. Skipping insert.")
        else:
            cursor.execute(query, (title, company, area, salary, link, hash_value))
            con.commit()
        data.append(vacancy_data)
        endless_page = soup.find('div', class_='pagination')
        if endless_page != None:
            #print('yes')
            current = endless_page.find('a', class_='page current')
            while endless_page.find('a', class_='next_page')!=None:
                time.sleep(5)
                response = requests.get(f'https://career.habr.com/vacancies?page={int(current.text)+1}&locations[]={area_calc(area_input)}&q={string_input}&salary={salary_input}&type=all', headers={'user-agent':UserAgent().random})
                print(response.status_code)
                soup = BeautifulSoup(response.text, "lxml")
                endless_page = soup.find('div', class_='pagination')
                current = endless_page.find('a', class_='page current')
                vacancies = soup.find_all('div', class_='vacancy-card__info')
                for vacancy in vacancies:
                    company = vacancy.find('a', class_="link-comp link-comp--appearance-dark").text
                    title = vacancy.find('a', class_="vacancy-card__title-link").text
                    salary = vacancy.find('div', class_="basic-salary").text
                    area = vacancy.find('div', class_="vacancy-card__meta").find('a', class_="link-comp link-comp--appearance-dark")
                    if area != None:
                        area = area.text
                    if salary != None:
                        salary = process_salary_habr(salary)
                    link = "https://career.habr.com"+vacancy.find('a', class_="vacancy-card__title-link")["href"]
                    vacancy_data = {'title': title, 'company': company, 'area':area, 'salary':salary, 'link':link}
                    msgpack_data = msgpack.packb(vacancy_data)
                    hash_value = hashlib.sha256(msgpack_data).hexdigest()
                    cursor.execute("SELECT * FROM vacancies WHERE vacancy_hash = %s", (hash_value,))
                    if cursor.fetchone():
                        print("Duplicate hash value found. Skipping insert.")
                    else:
                        cursor.execute(query, (title, company, area, salary, link, hash_value))
                        con.commit()
                    data.append(vacancy_data)

    csv_file_path = os.path.join("csv", "temp_habr_vacancies.csv")
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, dialect='own-tab')
        writer.writerow(["title", "employer", "salary", "area", "vacancy link"])
        for row in data:
            writer.writerow([row['title'], row['company'], row['salary'], row['area'], row['link']])

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
