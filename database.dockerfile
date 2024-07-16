FROM mysql/mysql-server:8.0

COPY settings.py /settings.py

ENV MYSQL_ROOT_PASSWORD=${ROOT_PASS}
ENV MYSQL_DATABASE=mydb
ENV MYSQL_USER=myuser
ENV MYSQL_PASSWORD=${dbpass}

COPY db_schema.sql /docker-entrypoint-initdb.d/

EXPOSE 3306

CMD ["mysqld"]