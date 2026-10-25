import pytest

from judge import assert_criteria
from sql_tools import SQLTools
from test_agent import create_test_agent


TEST_CASES = [
    pytest.param(
        "Which hour of the day has the highest average fare amount?",
        [
        "the SQL query correctly calculates average fare by hour of day",
        "the result identifies a specific hour as having the highest average fare",
        "the result includes the actual average fare amount",
        ],
        id="hour-of-the-day-with-highest-average",
    ),
    pytest.param(
        "How many trips had zero passengers recorded?",
        [
        "The SQL query filters on the passenger_count column.",
        "The filter checks for passenger_count equal to 0.",
        "The query counts the matching trips.",
        "The result reports the count returned by the query.",
        ],
        id="trips-with-zero-passanger",
    ),  
]


@pytest.mark.parametrize(("user_query", "criteria"), TEST_CASES)
@pytest.mark.asyncio
async def test_agent_with_judge(user_query, criteria):
    sql = SQLTools("taxi.db")
    try:
        agent = create_test_agent(sql)
        result = await agent.run(user_query)
        await assert_criteria(result, criteria)
    finally:
        sql.con.close()