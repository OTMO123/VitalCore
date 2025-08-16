#!/usr/bin/env python3
import asyncio, asyncpg

async def check():
    conn = await asyncpg.connect('postgresql://postgres:password@localhost:5432/iris_db')
    constraints = await conn.fetch("SELECT constraint_name, check_clause FROM information_schema.check_constraints WHERE constraint_name LIKE '%audit%';")
    print('Audit constraints:')
    for c in constraints:
        print(f'{c["constraint_name"]}: {c["check_clause"]}')
    await conn.close()

asyncio.run(check())