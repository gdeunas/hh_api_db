# main.py
import os
from dotenv import load_dotenv

from src.apihh import HHParser, save_to_db
from src.utils import DBManager

load_dotenv()

db_config = {
    "host": os.getenv('HOST'),
    "database": os.getenv("DATABASE"),
    "user": os.getenv("USER"),
    "password": os.getenv("PASSWORD"),
    "port": os.getenv("PORT"),

}

# 1.подключение и запрос данных с hh.ru
hh = HHParser({})
companies_list = [
    'Яндекс',
    'Альфа-Банк',
    'Т-Банк',
    'Сбербанк',
    'МТС',
    'VK',
    'Газпромбанк',
    'Ozon',
    'Авито',
    'Лаборатория Касперского'
]

comp = hh.get_employers(companies_list)

all_data = []
for emp in comp:
    emp_id = emp['id']

    vacancies = hh.get_vacancies(emp_id)

    all_data.append({
        'employer_id': emp_id,
        'employer_name': emp['name'],
        'vacancies': vacancies,
    })

# 2. Сохранить данные по работодателю и его вакансиям в БД
save_to_db(all_data, db_config)

# 3. Получить количество вакансии из БД
db_manager = DBManager(db_config)
data = db_manager.get_companies_and_vacancies_count()
for name, count in data:
    print(f"Компания: {name} | Вакансии: {count}")

# 4. Вывести все вакансии
vacancies = db_manager.get_all_vacancies()
print("\nСписок всех вакансий:")
for comp, title, s_from, s_to, url in vacancies:
    salary = f"{s_from if s_from else 0}-{s_to if s_to else ''}"
    print(f"Компания: {comp} | Вакансия: {title} | Зарплата: {salary} | Ссылка: {url}")

# 5. Средняя зарплата
avg_salary = db_manager.get_avg_salary()
value = avg_salary[0] if isinstance(avg_salary, tuple) else avg_salary
print(f"\nСредняя зарплата по всем вакансиям: {int(value if value else 0)} руб.")

# 6. Вакансии с зарплатой выше средней
high_salary_vacs = db_manager.get_vacancies_with_higher_salary()
print("\nВакансии с зарплатой выше средней:")
for vac in high_salary_vacs:
    # Предполагаем, что vac[2] - название, vac[3] - зарплата 'от'
    print(f"Вакансия: {vac[2]} | Зарплата от: {vac[3]} | Ссылка: {vac[5]}")

# 7. Поиск ключевого слова
word = input("Введите слово для поиска (например, python): ")
keyword_vacs = db_manager.get_vacancies_with_keyword(word)
print(f"\nВакансии со словом '{word}':")
for vac in keyword_vacs:
    print(f"Компания ID: {vac[1]} | Название: {vac[2]} | Ссылка: {vac[5]}")

db_manager.close()
