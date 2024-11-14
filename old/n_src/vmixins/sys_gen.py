import re
from time import sleep
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate
from rich import print


with open('v_prompt.txt', 'r') as f:
    mix_prompt = f.read()

with open('p_prompt.txt', 'r') as f:
    plan_prompt = f.read()

with open('mix_list.txt', 'r') as f:
    mix_list = f.readlines()


def camel_to_snake(name: str) -> str:
    """
    Converts a camelCase or PascalCase string to snake_case.

    :param name: The camelCase or PascalCase string to be converted.
    :return: The converted snake_case string.

    Example:
    >>> camel_to_snake('ExampleString')
    'example_string'
    """
    if not isinstance(name, str):
        raise ValueError("Input must be a string.")
    if not name:
        return ''
    name = name.strip()
    snake_case_name = ''
    for i, char in enumerate(name):
        if char.isupper() and i != 0:
            snake_case_name += '_'
        snake_case_name += char.lower()
    return snake_case_name


def extract_mixin_name(description):
    # Use regular expression to find text between '.' and ':'
    match = re.search(r'\.(.*):', description)
    if match:
        return match.group(1)
    else:
        return None


def generate(prompt, mixin_description):

    chat = ChatAnthropic(model="claude-3-5-sonnet-20240620",
                         temperature=0,
                         api_key="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",
                         max_tokens=8192)

    pprompt = prompt.format(mixin_description=mixin_description)

    messages = [(
                "system",
                "You are an expert Python developer specializing in Flask-AppBuilder and SQLAlchemy."
                ),
                (
                "human",
                f"{pprompt}"
                ),
                ]

    full_code = ""

    while True:
        sleep(5)
        response = chat.invoke(messages)
        code_chunk = response.content

        if "[CODE_CONTINUES]" in code_chunk:
            full_code += code_chunk.replace("[CODE_CONTINUES]", "").strip()
            print("\t continue, waiting first ...")
            sleep(5)

            continue_prompt = f"""Please continue the implementation where you left off. Here are the last few lines for context:

            {full_code[-200:]}

            Continue the implementation, and remember to end with [CODE_CONTINUES] if you're not finished."""

            messages.append(AIMessage(content=code_chunk))
            messages.append(HumanMessage(content=continue_prompt))
        else:
            full_code += code_chunk
            break

    return full_code

def generate_mixin_code(mixin_description):

    chat = ChatAnthropic(model="claude-3-5-sonnet-20240620",
                         temperature=0,
                         api_key="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",
                         max_tokens=8192)
    pprompt = prompt.format(mixin_description=mixin_description)
    messages = [(
                "system",
                "You are an expert Python developer specializing in Flask-AppBuilder and SQLAlchemy."
                ),
                (
                "human",
                f"{pprompt}"
                ),
                ]

    full_code = ""

    while True:
        sleep(5)
        response = chat.invoke(messages)
        code_chunk = response.content

        if "[CODE_CONTINUES]" in code_chunk:
            full_code += code_chunk.replace("[CODE_CONTINUES]", "").strip()
            print("\t continue, sleeping ...")
            sleep(5)

            continue_prompt = f"""Please continue the mixin implementation where you left off. Here are the last few lines for context:

            {full_code[-400:]}

            Continue the implementation, and remember to end with [CODE_CONTINUES] if you're not finished."""

            messages.append(AIMessage(content=code_chunk))
            messages.append(HumanMessage(content=continue_prompt))
        else:
            full_code += code_chunk
            break

    return full_code


for i, description in enumerate(mix_list):
    if description.strip() == '':
        continue
    mix_name = extract_mixin_name(description)
    mix_name = mix_name.strip()
    print(f"[bold yellow] {mix_name.strip()}")
    print(f"[bold cyan]Planning ...[/bold cyan]")
    plan = generate(plan_prompt,description)
    with open(f"vplan/plan_{camel_to_snake(mix_name)}.md", "w") as f:
        f.write(plan)
    sleep(10)
    print("[bold cyan]Coding .....[/bold cyan]")
    code = generate(mix_prompt, description +f"\n\nHere is technical plan:\n {plan}\n\n" )

    with open(f"vmix/{camel_to_snake(mix_name)}.py", "w") as f:
        f.write(code)

