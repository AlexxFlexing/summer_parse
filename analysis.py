import mysql.connector
import matplotlib.pyplot as plt
import numpy as np
from settings import dbuser, dbpass, dbhost, dbdb
import os


def city_salary_distribution(area_name):
    con = mysql.connector.connect(
        user = dbuser,
        password = dbpass,
        host = dbhost,
        database = dbdb
    )

    cursor = con.cursor()

    query = "SELECT salary FROM vacancies WHERE area = %s AND salary IS NOT NULL AND salary > 0"
    cursor.execute(query, (area_name,))

    salaries = [row[0] for row in cursor.fetchall()]

    min_salary = min(salaries)
    max_salary = max(salaries)
    avg_salary = sum(salaries) / len(salaries)

    hist, bins = np.histogram(salaries, bins=20)
    plt.figure()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.plot(bins[:-1], hist)
    plt.xlabel('Зарплата')
    plt.ylabel('Количество вакансий')
    plt.title(f'{area_name}: распределение зарплат')
    plt.text(0.5, 0.9, f'мин: {min_salary:.2f}, макс: {max_salary:.2f}, средн: {avg_salary:.2f}', ha='center', transform=plt.gca().transAxes)
    plt.savefig(os.path.join("png", "city_salary_graph.png"))
    cursor.close()
    con.close()


def area_amount_rank():
    con = mysql.connector.connect(
        user = dbuser,
        password = dbpass,
        host = dbhost,
        database = dbdb
    )

    cursor = con.cursor()
    query = "SELECT area, COUNT(*) as count FROM vacancies WHERE area IS NOT NULL GROUP BY area ORDER BY count DESC LIMIT 10"
    cursor.execute(query)
    results = cursor.fetchall()
    areas = [row[0] for row in results]
    counts = [row[1] for row in results]
    plt.figure(figsize=(30, 10))
    plt.bar(areas, counts)
    plt.title('10 городов с наибольшим количеством вакансий')
    plt.xlabel('Город')
    plt.ylabel('Количество вакансий')
    plt.savefig(os.path.join("png", "top10_area_amount.png"))
    cursor.close()
    con.close()

def company_amount_rank():
    con = mysql.connector.connect(
        user = dbuser,
        password = dbpass,
        host = dbhost,
        database = dbdb
    )

    cursor = con.cursor()
    query = "SELECT company_name, COUNT(*) as count FROM vacancies WHERE company_name IS NOT NULL GROUP BY company_name ORDER BY count DESC LIMIT 10"
    cursor.execute(query)
    results = cursor.fetchall()
    companies = [row[0] for row in results]
    counts = [row[1] for row in results]
    plt.figure(figsize=(30, 10))
    plt.bar(companies, counts)
    plt.title('10 компаний с наибольшим количеством вакансий')
    plt.xlabel('Компания')
    plt.ylabel('Количество вакансий')
    plt.savefig(os.path.join("png", "top10_companies_amount.png"))
    cursor.close()
    con.close()

def company_salary_rank():
    con = mysql.connector.connect(
        user = dbuser,
        password = dbpass,
        host = dbhost,
        database = dbdb
    )

    cursor = con.cursor()
    query = "SELECT company_name, salary FROM vacancies WHERE company_name IS NOT NULL AND salary IS NOT NULL AND salary != 0"
    #would like to use limit 10 here as well but dont know how to process avg salary properly
    cursor.execute(query)
    results = cursor.fetchall()
    company_salaries = {}
    for row in results:
        company, salary = row
        if company not in company_salaries:
            company_salaries[company] = []
        company_salaries[company].append(salary)
    company_avg_salaries = {}
    for company, salaries in company_salaries.items():
        avg_salary = sum(salaries) / len(salaries)
        company_avg_salaries[company] = avg_salary
    top_10_companies = sorted(company_avg_salaries.items(), key=lambda x: x[1], reverse=True)[:10]
    #looks scuffed but limits the company names length as well
    companies = [company[:25] + "..." if len(company) > 25 else company for company, avg_salary in top_10_companies]
    avg_salaries = [avg_salary for company, avg_salary in top_10_companies]
    print(avg_salaries)
    plt.figure(figsize=(30, 20))
    plt.bar(companies, avg_salaries)
    plt.title('10 компаний с наивысшей средней зарплатой')
    plt.xlabel('Компания')
    plt.ylabel('Средняя зарплата')
    #gca removes e stuff 
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    plt.savefig(os.path.join("png", "top10_companies_salary.png"))
    cursor.close()
    con.close()
