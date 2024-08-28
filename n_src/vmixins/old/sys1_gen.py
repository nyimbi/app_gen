import re
from time import sleep
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate


with open('v_prompt.txt', 'r') as f:
    prompt = f.read()


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


def generate_mixin_plan(mixin_description):

    chat = ChatAnthropic(model="claude-3-5-sonnet-20240620",
                         temperature=0,
                         api_key="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",
                         max_tokens=8192)
    planning_prompt = f"""You are an expert Python developer specializing in Flask-AppBuilder and SQLAlchemy.
    Please carefully consider the requirements for the following mixin and outline a detailed plan for its implementation.
    The plan should include a detailed and exhaustive description of features, methods, and capabilities and considerations required to implement the mixin successfully.

    Mixin description: {mixin_description}

    Please provide a detailed plan with considerations before proceeding to the implementation."""

    messages = [HumanMessage(content=planning_prompt)]

    response = chat.invoke(messages)
    plan = response.content

    return plan


def generate_mixin_code(mixin_description, plan):

    chat = ChatAnthropic(model="claude-3-5-sonnet-20240620",
                         temperature=0,
                         api_key="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",
                         max_tokens=8192)
    implementation_prompt = f"""Based on the following detailed plan, implement the mixin.
    Use best practices and ensure the code is efficient and clean.

    Plan:
    {plan}

    Mixin description: {mixin_description}

    Implement the mixin now. If you need more space to complete the code, use [CODE_CONTINUES]."""

    messages = [HumanMessage(content=implementation_prompt)]
    full_code = ""

    while True:
        response = chat.invoke(messages)
        code_chunk = response.content

        if "[CODE_CONTINUES]" in code_chunk:
            full_code += code_chunk.replace("[CODE_CONTINUES]", "").strip()
            print("\t continue")

            continue_prompt = f"""Please continue the mixin implementation where you left off. Here are the last few lines for context:

            {full_code[-700:]}

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
    # sleep(5)
    mix_name = extract_mixin_name(description)
    print(f"Processing mixin: {mix_name.strip()}")

    # Step 1: Generate a detailed plan
    plan = generate_mixin_plan(description)
    print(f"Plan for {mix_name.strip()}:\n{plan}")
    sleep(5)

    # Step 2: Generate the mixin code based on the plan
    code = generate_mixin_code(description, plan)

    # Save the generated code to a file
    with open(f"{camel_to_snake(mix_name)}.py", "w") as f:
        f.write(code)

