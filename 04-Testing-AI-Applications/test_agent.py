import asyncio
from pathlib import Path

import pytest
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from sql_tools import SQLTools
from utils import collect_tools, ToolCall

import dotenv
from openai import OpenAI

dotenv.load_dotenv()
openai = OpenAI()


DB_PATH = Path(__file__).resolve().parent / "taxi.db"


class AgentOutput(BaseModel):
    sql_query: str = Field(description="The SQL query executed to answer the question")
    result_text: str = Field(description="The result returned by the SQL query")


INSTRUCTIONS = """
You answer questions about the DuckDB trips table.
Use get_schema to check available columns and run_sql to execute your query.
For the user's question, return the exact SQL query used in sql_query and include
the actual run_sql result in result_text. Do not estimate or invent query results.
""".strip()

def create_test_agent(sql):
        return Agent(
        name="sql agent test",
        model="openai:gpt-4o-mini",
        instructions=INSTRUCTIONS,
        tools=[sql.get_schema, sql.run_sql],
        output_type=AgentOutput,
        )
    
   
@pytest.mark.asyncio
async def test_agent_counts_trips_with_more_than_five_passengers():
    sql = SQLTools(str(DB_PATH))
    try:
        expected_count = sql.con.execute(
            "SELECT COUNT(*) FROM trips WHERE passenger_count > 5"
        ).fetchone()[0]
        

        agent = create_test_agent(sql)
        result = await agent.run("How many trips had more than 5 passengers?")
        output = result.output
        print(output)

        assert isinstance(output.sql_query, str) and output.sql_query.strip()
        assert str(expected_count) in output.result_text
        return output
    finally:
        sql.con.close()
        
@pytest.mark.asyncio
async def test_most_common_payment_type():
    sql = SQLTools(str(DB_PATH))
    try:
        
        agent = create_test_agent(sql)
        user_prompt = 'What is the most common payment type?'
        result = await agent.run(user_prompt)
        output = result.output
        print(output)
        messages = result.new_messages()
        tool_calls = collect_tools(messages)
        tool_call1 = tool_calls[0]
        tool_call2 = tool_calls[1]
        assert tool_call1.name == 'get_schema'
        assert tool_call2.name == 'run_sql'
    finally:
        sql.con.close()

async def main():
    await test_agent_counts_trips_with_more_than_five_passengers()
    print("Passenger count test passed.")

    await test_most_common_payment_type()
    print("Payment type test passed.")


if __name__ == "__main__":
    asyncio.run(main())


