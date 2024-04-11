import os
import openai
import param
from dotenv import load_dotenv

# Depricated
# from langchain.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain.schema.runnable import RunnablePassthrough

from langchain.prompts import MessagesPlaceholder
from langchain.prompts import ChatPromptTemplate

from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents import AgentExecutor

from langchain.memory import ConversationBufferMemory
#Depricated
#from langchain.tools.render import format_tool_to_openai_function
from langchain_core.utils.function_calling import convert_to_openai_function


load_dotenv()

openai.api_key = os.environ['OPENAI_API_KEY']

#### AGENT CLASS

class v_agent(param.Parameterized):
    
    def __init__(self, tools, context, **params):
        super(v_agent, self).__init__( **params)
        self.functions = [convert_to_openai_function(f) for f in tools]
        self.model = ChatOpenAI(temperature=0, model="gpt-4").bind(functions=self.functions)
        self.memory = ConversationBufferMemory(return_messages=True,memory_key="chat_history")
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", context),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        self.chain = RunnablePassthrough.assign(
            agent_scratchpad = lambda x: format_to_openai_functions(x["intermediate_steps"])
        ) | self.prompt | self.model | OpenAIFunctionsAgentOutputParser()
        self.qa = AgentExecutor(agent=self.chain, tools=tools, verbose=True, memory=self.memory)
    
    def convchain(self, query):
        if not query:
            return
        result = self.qa.invoke({"input": query})
        self.answer = result['output'] 
        return self.answer

    def clr_history(self,count=0):
        self.chat_history = []
        return