from openai import OpenAI


def run(prompt_str):
    client = OpenAI(api_key="sk-f606c156208842f391806c4213bb8344", base_url="https://api.deepseek.com/beta")

    response = client.chat.completions.create(
        model="deepseek-coder",
        messages=[
            {"role": "system", "content": "You are a code assistant, you can answer any question about coding."},
            {"role": "user", "content": prompt_str},
        ],
        stream=False
    )
    return response.choices[0].message.content
    # print(response.choices[0].message.content)