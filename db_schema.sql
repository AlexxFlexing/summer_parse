CREATE DATABASE job_vacancies;

USE job_vacancies;

CREATE TABLE vacancies (
  vacancy_name TEXT NOT NULL,
  company_name TEXT NOT NULL,
  salary INT,
  area TEXT,
  experience TEXT,
  employment TEXT,
  schedule TEXT,
  vacancy_link TEXT NOT NULL,
  vacancy_hash VARCHAR(255) NOT NULL PRIMARY KEY
);
