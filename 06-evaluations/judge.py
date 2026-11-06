import json

from pydantic import BaseModel
from typing import Literal
from pydantic_ai import Agent

from openai import OpenAI
import dotenv
dotenv.load_dotenv()
openai = OpenAI()


class JudgeEvaluation(BaseModel):
    reasoning: str
    label: Literal["good", "bad"]


judge_instructions = """You are an expert evaluator assessing a recipe assistant that answers
cooking questions using a fixed recipe collection. The recipe collection is included
with each evaluation prompt. Use it as evidence when checking the assistant's answer.

A response is "good" if:
1. It answers accurately using information supported by the provided recipe collection.
2. It correctly identifies when a recipe or requested detail is not in the collection.
   It may suggest a relevant recipe that is in the collection.
3. It asks a relevant follow-up question when the user's request is vague.
4. It declines questions outside the recipe assistant's scope. A brief, neutral
   redirection is acceptable.

A response is "bad" if ANY of these apply:
1. It invents a recipe or gives a material ingredient, instruction, time, temperature,
   or nutrition detail that the collection does not support.
2. It contradicts information in the collection, including explicit recipe instructions.
3. It answers a request for a missing recipe with invented recipe instructions.
4. It gives substantive advice on an out-of-scope topic instead of declining.
5. It gives incorrect information about a recipe in the collection.
6. It says it cannot help when the collection contains information that answers the question.

Use the provided recipe collection as evidence. Do not call a response unverifiable
when you can check it against that collection. Judge the answer to the user's question
and any material extra claims; do not penalize harmless wording or a relevant follow-up
question. Unsupported cooking claims still count as bad, even when they sound plausible.
"""

judge_agent = Agent(
    'openai:gpt-4o-mini',
    output_type=JudgeEvaluation,
    instructions=judge_instructions,
)

with open('recipes.json', encoding='utf-8') as f:
    recipes = json.load(f)

with open('results.json', encoding='utf-8') as f:
    results = json.load(f)

for i, row in enumerate(results):
    prompt = f"""Recipe collection:
{json.dumps(recipes, indent=2)}

Question: {row['question']}
Agent response: {row['output']}"""

    evaluation = judge_agent.run_sync(prompt)
    row['judge_label'] = evaluation.output.label
    row['judge_reasoning'] = evaluation.output.reasoning
    print(f"[{i+1}/{len(results)}] {row['judge_label']}: {row['question']}")

with open('results_judged.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

print(f"\nSaved judged results to results_judged.json")
