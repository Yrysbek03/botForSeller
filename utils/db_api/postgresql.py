import os
import ssl

import asyncpg
from aiogram import types
from asyncpg.pool import Pool

from data import config


class Database:
    def __init__(self, pool):
        self.pool: Pool = pool

    @classmethod
    async def create(cls):
        ctx = ssl.create_default_context(
            cafile=os.path.join(os.path.dirname(__file__), 'rds-combined-ca-bundle.pem'))
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        pool = await asyncpg.create_pool(
            dsn=config.pgUri,
            # user=config.pgUser,
            # password=config.pgPassword,
            # database=config.pgDatabase,
            # host=config.pgHost,
            # port=config.pgPort,
            ssl=ctx
        )
        return cls(pool)

    async def create_table_goods(self):
        sql = """
        CREATE TABLE IF NOT EXISTS Goods (
            good_id SERIAL PRIMARY KEY, 
            name varchar(255),
            link varchar(255) unique,
            slug varchar(255) unique,
            minimum integer default 0,
            minus integer default 1,
            is_active boolean default true
            );
"""
        await self.pool.execute(sql)

    @staticmethod
    def format_args(sql, parameters: dict, by='AND'):
        sql += f" {by} ".join([
            f"{item} = ${num + 1}" for num, item in enumerate(parameters)
        ])
        return sql, tuple(parameters.values()), len(parameters) + 1

    async def insert_good(self, name: str, link: str, slug: str):
        # SQL_EXAMPLE = "INSERT INTO Users(id, Name, email) VALUES(1, 'John', 'John@gmail.com')"

        sql = """
        INSERT INTO Goods(name, link, slug) VALUES($1, $2, $3)
        """
        await self.pool.execute(sql, name, link, slug)

    async def select_good(self, **kwargs):
        # SQL_EXAMPLE = "SELECT * FROM Users where id=1 AND Name='John'"
        sql = f"""
        SELECT * FROM Goods WHERE 
        """
        sql, parameters, _ = self.format_args(sql, parameters=kwargs)
        return await self.pool.fetchrow(sql, *parameters)

    async def select_goods(self):
        sql = f"""
        SELECT * FROM Goods Order By good_id desc
        """
        return await self.pool.fetch(sql)

    async def select_goods_slug(self):
        sql = f"""
        SELECT slug FROM Goods
        """
        return await self.pool.fetch(sql)

    async def select_goods_active(self):
        # SQL_EXAMPLE = "SELECT * FROM Users where id=1 AND Name='John'"
        sql = f"""
        SELECT * FROM Goods WHERE is_active=$1
        """
        return await self.pool.fetch(sql, True)

    async def update_good(self, good_id, **kwargs):
        sql = "UPDATE Goods SET "
        sql, parameters, index = self.format_args(sql, parameters=kwargs, by=',')
        sql += f' WHERE good_id=${index}'
        parameters = parameters.__add__(tuple((good_id,)))
        return await self.pool.execute(sql, *parameters)

    async def delete_good(self, good_id: int):
        await self.pool.execute("DELETE FROM Goods WHERE good_id=$1", good_id)

    async def delete_goods(self):
        await self.pool.execute("DELETE FROM Goods WHERE TRUE")

    # parse table
    async def create_table_parse(self):
        sql = """
        CREATE TABLE IF NOT EXISTS Parse (
            parse_id integer PRIMARY KEY,
            is_parse Boolean default True,
            time integer default 900
            );
"""
        await self.pool.execute(sql)

    async def insert_parse(self, boolean):
        sql = """
                INSERT INTO Parse(parse_id, is_parse) VALUES($1, $2)
                """
        await self.pool.execute(sql, 1, boolean)

    async def update_parse_bool(self, boolean):
        sql = "UPDATE Parse SET is_parse=$1 Where parse_id=$2"
        return await self.pool.execute(sql, boolean, 1)

    async def update_parse_time(self, time):
        sql = "UPDATE Parse SET time=$1 Where parse_id=$2"
        return await self.pool.execute(sql, time, 1)

    async def select_parse(self):
        sql = f"""
        SELECT is_parse, time FROM Parse where parse_id=$1
        """
        return await self.pool.fetchrow(sql, 1)
