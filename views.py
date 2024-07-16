import csv
import mysql.connector
from settings import dbuser, dbpass, dbhost, dbdb
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

def find_vacancies_by_area(area_name):
    con = mysql.connector.connect(
    user = dbuser,
    password = dbpass,
    host = dbhost,
    database = dbdb
    )
    cursor = con.cursor()

    cursor.execute("SELECT * FROM vacancies WHERE area = %s", (area_name, ))
    rows = cursor.fetchall()

    if not rows:
        cursor.close()
        con.close()
        return "no vacancies found"

    csv_file_path = os.path.join("csv", f"{area_name}_vacancies.csv")
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, dialect='own-tab')
        writer.writerow(["title", "employer", "salary", "area", "experience", "schedule", "vacancy link"])
        for row in rows:
            writer.writerow([row[0], row[1], row[2], row[3], row[4], row[5], row[6]])

    matching_vacancies = {}
    for i, row in enumerate(rows[:10]):
        matching_vacancies[f"vacancy_{i+1}"] = {
            "title": row[0],
            "employer": row[1],
            "salary": row[2],
            "area" : row[3],
            "vacancy link" : row[6]
        }

    cursor.close()
    con.close()

    return matching_vacancies

def find_vacancies_by_salary(salary):
    con = mysql.connector.connect(
    user = dbuser,
    password = dbpass,
    host = dbhost,
    database = dbdb
    )
    cursor = con.cursor()

    cursor.execute("SELECT * FROM vacancies WHERE salary >= %s", (salary,))
    rows = cursor.fetchall()

    if not rows:
        cursor.close()
        con.close()
        return "no vacancies found"

    csv_file_path = os.path.join("csv", f"{salary}_vacancies.csv")
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, dialect='own-tab')
        writer.writerow(["title", "employer", "salary", "area", "experience", "schedule", "vacancy link"])
        for row in rows:
            writer.writerow([row[0], row[1], row[2], row[3], row[4], row[5], row[6]])

    matching_vacancies = {}
    for i, row in enumerate(rows[:10]):
        matching_vacancies[f"vacancy_{i+1}"] = {
            "title": row[0],
            "employer": row[1],
            "salary": row[2],
            "area" : row[3],
            "vacancy link" : row[6]
        }

    cursor.close()
    con.close()

    return matching_vacancies


def database_to_csv():
    con = mysql.connector.connect(
    user = dbuser,
    password = dbpass,
    host = dbhost,
    database = dbdb
    )
    cursor = con.cursor()
    query = "SELECT * from vacancies"
    cursor.execute(query)
    rows = cursor.fetchall()
    csv_file_path = os.path.join("csv", "database.csv")
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, dialect='own-tab')
        writer.writerow(["title", "employer", "salary", "area", "experience", "schedule", "vacancy link"])
        for row in rows:
            writer.writerow([row[0], row[1], row[2], row[3], row[4], row[5], row[6]])


def process_answer(dict):
    result = ''
    for object in dict.values():
        for key, value in object.items():
            if value is not None:
                if key == 'salary':
                    result += str(value) + ' ₽\n'
                else:
                    result += value + '\n'
        result += '\n'
    return result