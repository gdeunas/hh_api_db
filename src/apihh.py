# apihhdb.py
import time
from typing import Any

import psycopg2
import requests


class HHParser:
    """Класс для api hh"""

    def __init__(self, params: dict[str, Any]) -> None:
        self.base_url = "https://api.hh.ru"
        self.headers: dict[str, str] = {"User-Agent": "hh_api_db/1.0"}

    def get_employers(self, employer_names: list[str]) -> list[dict[str, str]]:
        """Данные работодателей"""
        employers_data = []
        for name in employer_names:
            params: dict[str, str | int | bool] = {
                "text": name,
                "only_with_vacancies": True,
                "type": "company",
                "area": 113,
            }
            response = requests.get(
                f"{self.base_url}/employers", params=params, headers=self.headers
            )
            if response.status_code == 200:
                items = response.json().get("items")
                if items:
                    employers_data.append(items[0])

            time.sleep(0.2)
        return employers_data

    def get_vacancies(self, employer_id: str) -> list[dict[str, str]]:
        """Список вакансии по работодателю"""
        url = f"{self.base_url}/vacancies"
        params: dict[str, str | int | bool] = {
            "employer_id": employer_id,
            "only_with_vacancies": True,
            "per_page": 10,
        }
        response = requests.get(url, params=params, headers=self.headers)
        if response.status_code == 200:
            return response.json().get("items", [])
        return []


def save_to_db(data_list, db_params):
    conn = psycopg2.connect(**db_params)
    conn.autocommit = True

    with conn.cursor() as cur:
        for item in data_list:
            cur.execute(
                """
                INSERT INTO employers (employer_id, name)
                VALUES (%s, %s)
                ON CONFLICT (employer_id) DO NOTHING
                """,
                (item["employer_id"], item["employer_name"]),
            )

            for vac in item["vacancies"]:
                salary = vac.get("salary")
                salary_from = salary.get("from") if salary else None
                salary_to = salary.get("to") if salary else None

                cur.execute(
                    """
                    INSERT INTO vacancies (vacancy_id, employer_id, title, salary_from, salary_to, url)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (vacancy_id) DO NOTHING
                    """,
                    (
                        vac["id"],
                        vac["employer"]["id"],
                        vac["name"],
                        salary_from,
                        salary_to,
                        vac["alternate_url"],
                    ),
                )
    conn.close()
    print("Данные сохранены в БД")


if __name__ == "__main__":
    companies = [
        "Яндекс",
        "Альфа-Банк",
        "Т-Банк",
        "Сбербанк",
        "МТС",
        "VK",
        "Газпромбанк",
        "Ozon",
        "Авито",
        "Лаборатория Касперского",
    ]
    hh = HHParser({})
    comp = hh.get_employers(companies)

    all_data = []
    for emp in comp:
        # print(f"ID: {emp['id']}, Название: {emp['name']}")
        employer = emp["id"]
        if employer:
            vacancies = hh.get_vacancies("id")
            all_data.append(
                {
                    "employer_id": employer,
                    "vacancies": vacancies,
                }
            )

    print(hh.get_vacancies("1740"))
