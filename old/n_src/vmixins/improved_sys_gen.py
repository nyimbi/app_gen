import re
import asyncio
import aiofiles
from time import sleep
from typing import List, Optional
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate
from rich import print
from rich.progress import Progress
import yaml
from ratelimit import limits, sleep_and_retry

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

API_KEY = config['anthropic_api_key']
RATE_LIMIT = config['rate_limit']
RATE_PERIOD = config['rate_period']

async def read_file(filename: str) -> str:
    async with aiofiles.open(filename, 'r') as f:
        return await f.read()

def camel_to_snake(name: str) -> str:
    if not isinstance(name, str):
        raise ValueError("Input must be a string.")
    name = name.strip()
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

def extract_mixin_name(description: str) -> Optional[str]:
    match = re.search(r'\.(.*):', description)
    return match.group(1) if match else None

@sleep_and_retry
@limits(calls=RATE_LIMIT, period=RATE_PERIOD)
async def generate(chat: ChatAnthropic, prompt: str, mixin_description: str) -> str:
    pprompt = prompt.format(mixin_description=mixin_description)
    messages = [
        ("system", "You are an expert Python developer specializing in Flask-AppBuilder and SQLAlchemy."),
        ("human", pprompt),
    ]

    full_code = ""
    while True:
        response = await chat.ainvoke(messages)
        code_chunk = response.content

        if "[CODE_CONTINUES]" in code_chunk:
            full_code += code_chunk.replace("[CODE_CONTINUES]", "").strip()
            print("\t continue")

            continue_prompt = f"""Please continue the implementation where you left off. Here are the last few lines for context:

            {full_code[-700:]}

            Continue the implementation, and remember to end with [CODE_CONTINUES] if you're not finished."""

            messages.append(AIMessage(content=code_chunk))
            messages.append(HumanMessage(content=continue_prompt))
        else:
            full_code += code_chunk
            break

    return full_code

async def process_mixin(description: str, mix_prompt: str, plan_prompt: str, progress: Progress, task: int):
    chat = ChatAnthropic(
        model="claude-3-5-sonnet-20240620",
        temperature=0,
        api_key=API_KEY,
        max_tokens=8192
    )

    mix_name = extract_mixin_name(description)
    if not mix_name:
        print(f"[bold red]Could not extract mixin name from: {description}[/bold red]")
        return

    mix_name = mix_name.strip()
    print(f"[bold yellow]{mix_name}[/bold yellow]")

    print(f"[bold cyan]Planning ...[/bold cyan]")
    plan = await generate(chat, plan_prompt, description)
    async with aiofiles.open(f"vplan/plan_{camel_to_snake(mix_name)}.md", "w") as f:
        await f.write(plan)

    await asyncio.sleep(10)

    print("[bold cyan]Coding .....[/bold cyan]")
    code = await generate(chat, mix_prompt, f"{description}\n\nHere is technical plan:\n{plan}\n\n")

    async with aiofiles.open(f"vmix/{camel_to_snake(mix_name)}.py", "w") as f:
        await f.write(code)

    progress.update(task, advance=1)

async def main():
    mix_prompt = await read_file('v_prompt.txt')
    plan_prompt = await read_file('p_prompt.txt')
    mix_list = (await read_file('mix_list.txt')).splitlines()

    with Progress() as progress:
        task = progress.add_task("[green]Processing mixins...", total=len(mix_list))
        await asyncio.gather(*[process_mixin(description, mix_prompt, plan_prompt, progress, task) for description in mix_list if description.strip()])

if __name__ == "__main__":
    asyncio.run(main())
