# utils.py
import psycopg2


def create_database(params: dict, db_name: str | None):
    """Создать БД и таблиц"""
    setup_params = params.copy()
    setup_params["database"] = "postgres"

    conn = psycopg2.connect(**setup_params)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(f"DROP DATABASE IF EXISTS {db_name}")
    cur.execute(f"CREATE DATABASE {db_name}")

    cur.close()
    conn.close()

    params["database"] = db_name
    conn = psycopg2.connect(**params)
    with conn.cursor() as cur:
        cur.execute(
            """
                CREATE TABLE employers (
                    employer_id INT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    url TEXT
                )
            """
        )
        cur.execute(
            """
                CREATE TABLE vacancies (
                    vacancy_id INT PRIMARY KEY,
                    employer_id INT REFERENCES employers(employer_id),
                    title VARCHAR(255) NOT NULL,
                    salary_from INT,
                    salary_to INT,
                    url TEXT
                )
            """
        )
    conn.commit()
    conn.close()


class DBManager:
    """Класс для БД"""

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
        """получает список всех вакансий с указанием названия компании, названия вакансии и зарплаты
        и ссылки на вакансию."""
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
        result = self.cur.fetchone()
        return result[0] if result and result[0] else 0

    def get_vacancies_with_higher_salary(self):
        """получает список всех вакансий, у которых зарплата выше средней."""
        avg_salary = self.get_avg_salary()
        query = """
            SELECT *
            FROM vacancies
            WHERE (COALESCE(salary_from, 0) + COALESCE(salary_to, 0)) / 2 > %s;
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
        self.cur.execute(query, (f"%{keyword}%",))
        return self.cur.fetchall()

    def close(self):
        """Закрытие соединения с БД"""
        self.cur.close()
        self.conn.close()
