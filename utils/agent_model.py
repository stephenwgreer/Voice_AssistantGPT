from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
  api_key=os.getenv("OPENAI_API_KEY"),  # this is also the default, it can be omitted
)

class Assistant:
    @staticmethod
    def get_openai_completion(messages, functions, model="gpt-4", temperature=0,max_tokens=2000):

        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=messages,
            functions=functions
        )
        return response.choices[0].message