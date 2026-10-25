import asyncio

import pydantic_ai
from pydantic_ai import Agent
from pydantic import BaseModel, Field
import dotenv
from openai import OpenAI
from sql_tools import SQLTools, setup_database

dotenv.load_dotenv()
openai = OpenAI()

instructions = """
You are a SQL agent that queries a DuckDB database.

Rules:
1. The table name is trips.
2. Use only column names returned by the schema tool.
3. Never invent or assume column names.
4. The passenger column is passenger_count, not passengers.
5. The distance column is trip_distance, not distance.
6. Generate valid DuckDB SQL.
7. Execute the SQL using the run_sql tool.
8. Explain the results returned by the tool.
""".strip()
query = "What's the average trip distance for rides with 2 passengers?"

def create_agent(db_path="taxi.db"):
    sql = SQLTools(db_path)
    return Agent(
        name="sql agent",
        model="openai:gpt-4o-mini",
        instructions=instructions,
        tools=[sql.get_schema, sql.run_sql],
    )


sql_agent = None

async def main():
    setup_database("taxi.db")
    agent = create_agent("taxi.db")
    result = await agent.run(query)
    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
else:
    setup_database()
    sql_agent = create_agent()
