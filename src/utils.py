# utils.py
import psycopg2


class DBManager:
    """Класс для БД"""

    # table vacancy
    # table company
    def __init__(self, params: dict):
        self.conn = psycopg2.connect(**params)
        self.cur = self.conn.cursor()

    def get_companies_and_vacancies_count(self):
        """получает список всех компаний и количество вакансий у каждой компании."""
        query = """
            SELECT name, COUNT(vacancies.vacancy_id)
            FROM employers
            LEFT JOIN vacancies USING(employer_id)
            GROUP BY name;
            """
        self.cur.execute(query)
        return self.cur.fetchall()

    def get_all_vacancies(self):
        """получает список всех вакансий с указанием названия компании, названия вакансии и зарплаты и ссылки на вакансию."""
        query = """
            SELECT employers.name, title, salary_from, salary_to, vacancies.url
            FROM vacancies
            JOIN employers USING(employer_id);
            """
        self.cur.execute(query)
        return self.cur.fetchall()

    def get_avg_salary(self):
        """получает среднюю зарплату по вакансиям."""
        query = """
            SELECT AVG((COALESCE(salary_from, salary_to) + COALESCE(salary_to, salary_from)) / 2)
            FROM vacancies
            WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL;
            """
        self.cur.execute(query)
        return self.cur.fetchone()[0]

    def get_vacancies_with_higher_salary(self):
        """получает список всех вакансий, у которых зарплата выше средней по всем вакансиям."""
        avg_salary_tuple = self.get_avg_salary()
        avg_salary = self.get_avg_salary()[0] if avg_salary_tuple else 0
        query = """
            SELECT * 
            FROM vacancies 
            WHERE (COALESCE(salary_from, 0) + COALESCE(salary_to, 0)) / 2 > %s;"
            """
        self.cur.execute(query, (avg_salary,))
        return self.cur.fetchall()

    def get_vacancies_with_keyword(self, keyword):
        """получает список всех вакансий, в названии которых содержатся переданные в метод слова, например python."""
        query = """
            SELECT * 
            FROM vacancies
            WHERE title ILIKE %s;
            """
        self.cur.execute(query, (f'%{keyword}%',))
        return self.cur.fetchall()

    def close(self):
        """Закрытие соединения с БД"""
        self.cur.close()
        self.conn.close()
