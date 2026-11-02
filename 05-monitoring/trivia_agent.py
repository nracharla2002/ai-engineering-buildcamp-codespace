import asyncio
from pydantic_ai import Agent
from trivia_tools import TriviaTools
from openai import OpenAI
import dotenv
import logfire


dotenv.load_dotenv()
openai = OpenAI()

logfire.configure()
logfire.instrument_pydantic_ai()


instructions = """You are a trivia quizmaster. When asked to play trivia:
1. Use the available tools to fetch trivia questions
2. Ask the player one question at a time with multiple choice options
3. Wait for their answer before moving to the next question
4. When the player answers, explain why the correct answer is correct - add interesting context and facts
5. After all questions, give the final score
"""

trivia_tools = TriviaTools()

agent = Agent(
    'openai:gpt-4o-mini',
    name='agent',
    tools=[trivia_tools.get_categories, trivia_tools.get_questions],
    instructions=instructions,
)



async def main():
    with logfire.span('trivia_session'):
        result = await agent.run("Let's play 5 easy questions from Science & Nature")
        message_history = result.all_messages()  
        print (result.output)
        while True:
            player_answer = input("Your answer(or type 'quit' to stop)")
            if  player_answer.strip().lower() == 'quit':
                break      
            result = await agent.run(player_answer,message_history=message_history)
            print (result.output)
            message_history = result.all_messages()

     
        

if __name__ == "__main__":
    asyncio.run(main())
    