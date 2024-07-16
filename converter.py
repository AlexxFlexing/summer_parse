import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

soup = BeautifulSoup(requests.get('https://www.cbr.ru/currency_base/daily/', headers={'user-agent':UserAgent().random}).content, 'lxml')
tbody = soup.find('tbody')

def get_currency_rate(code):
    for row in tbody.find_all('tr'):
        cols = row.find_all('td')
        #print(cols)
        if len(cols) != 0 and cols[1].text == code:
            to_rur = float(cols[4].text.replace(',','.')) / int(cols[2].text)
    return to_rur

#print(get_currency_rate('KZT'))

def process_salary_habr(salary):
    if "от" in salary and "до" in salary:
        seq = []
        add = True
        for word in salary.split():
            if word == 'до':
                add = False
            elif add and word.isdigit():
                seq.append(word)
        if salary.endswith("€"):
            return round(int("".join(map(str, seq))) * get_currency_rate('EUR'))
        if salary.endswith("$"):
            return round(int("".join(map(str, seq))) * get_currency_rate('USD'))
        return int("".join(map(str, seq)))
    
    if 'от' in salary:
        seq = []
        for word in salary.split():
            if word.isdigit():
                seq.append(word)
        if salary.endswith("€"):
            return round(int("".join(map(str, seq))) * get_currency_rate('EUR'))
        if salary.endswith("$"):
            return round(int("".join(map(str, seq))) * get_currency_rate('USD'))
        return int("".join(map(str, seq)))

    if 'до' in salary:
        seq = []
        for word in salary.split():
            if word.isdigit():
                seq.append(word)
        if salary.endswith("€"):
            return round(int("".join(map(str, seq))) * get_currency_rate('EUR'))
        if salary.endswith("$"):
            return round(int("".join(map(str, seq))) * get_currency_rate('USD'))
        return int("".join(map(str, seq)))
    else:
        if salary == '':
            return None
        seq = []
        for word in salary.split():
            if word.isdigit():
                seq.append(word)
        if salary.endswith("€"):
            return round(int("".join(map(str, seq))) * get_currency_rate('EUR'))
        if salary.endswith("$"):
            return round(int("".join(map(str, seq))) * get_currency_rate('USD'))
        return int("".join(map(str, seq)))
    
def process_salary_hh(salary, curr):
    if curr == 'BYR':
        curr = 'BYN'
    return round(salary * get_currency_rate(curr))