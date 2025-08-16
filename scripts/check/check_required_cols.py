#!/usr/bin/env python3
import asyncio, asyncpg

async def check():
    conn = await asyncpg.connect('postgresql://postgres:password@localhost:5432/iris_db')
    cols = await conn.fetch("SELECT column_name, is_nullable FROM information_schema.columns WHERE table_name = 'clinical_workflow_steps' AND is_nullable = 'NO' ORDER BY ordinal_position;")
    print('Required columns in clinical_workflow_steps:')
    for c in cols:
        print(f'  {c["column_name"]}')
    await conn.close()

asyncio.run(check())