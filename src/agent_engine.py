import os
import boto3
from dotenv import load_dotenv
from langchain_aws import ChatBedrock, BedrockEmbeddings
from langchain_chroma import Chroma
from langchain_core.tools import create_retriever_tool
from langchain_core.tools import tool
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# 1. Setup AWS Clients
# 1. Setup AWS Clients with Explicit Injection (The Fix!)
bedrock_client = boto3.client(
    service_name='bedrock-runtime', 
    region_name=os.getenv('AWS_DEFAULT_REGION'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    aws_session_token=os.getenv('AWS_SESSION_TOKEN')
)

embeddings = BedrockEmbeddings(client=bedrock_client, model_id="amazon.titan-embed-text-v2:0")
llm = ChatBedrock(client=bedrock_client, model_id="anthropic.claude-3-haiku-20240307-v1:0")

# 2. Connect to Database
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# --- THE TOOLS ---

# Tool 1: Turn our RAG database into a searchable tool
policy_tool = create_retriever_tool(
    retriever,
    "search_insurance_policy",
    "Searches and returns information about the HealthGuard policy. Use this to find base premiums, exclusions, and coverage limits."
)

# Tool 2: A custom Python function for the Agent to use
@tool
def calculate_premium(base_premium: str, is_smoker: bool) -> str:
    """Calculates the final insurance premium. Smokers get a 15% surcharge."""
    # Strip the dollar sign and commas, then convert to a math-friendly float
    clean_premium = float(str(base_premium).replace('$', '').replace(',', ''))
    final_price = clean_premium * 1.15 if is_smoker else clean_premium
    return f"The calculated final premium is ${final_price}"

@tool
def lookup_customer_policy(customer_name: str) -> str:
    """Use this tool to look up the active insurance policy details for a specific customer by name."""
    
    # A simulated internal backend database
    mock_database = {
        "john doe": "Active HealthGuard Premium policy. Smoker. Base premium paid. Includes maternity benefits.",
        "jane smith": "Active HealthGuard Standard policy. Non-smoker. No prior claims. Dental not included."
    }
    
    name_lower = customer_name.lower()
    if name_lower in mock_database:
        return mock_database[name_lower]
    else:
        return f"Customer '{customer_name}' not found in the internal system."

tools = [policy_tool, calculate_premium, lookup_customer_policy]

# --- THE GUARDRAILS ---

system_prompt = (
    "You are an internal assistant for Allianz brokers. "
    "You must ONLY answer questions using your provided tools. "
    "If a user asks about a topic not covered by the policy document, explicitly state: "
    "'I am strictly authorized to answer questions regarding the HealthGuard policy only.' "
    "Do not hallucinate or use outside internet knowledge."
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# 3. Build the Agent
agent = create_tool_calling_agent(llm, tools, prompt)

# Setting verbose=True lets us watch the AI "think" in the terminal!
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

if __name__ == "__main__":
    print("Agent Online. Testing guardrails and tools...\n")
    
    # Test 1: Guardrail Test
    print("--- Test 1: Out of bounds question ---")
    res1 = agent_executor.invoke({"input": "What is the best mutual fund to invest in for generational wealth?"})
    print(f"\nFinal Answer: {res1['output']}\n")
    
    # Test 2: Agentic Tool Test
    print("--- Test 2: RAG + Calculator ---")
    res2 = agent_executor.invoke({"input": "What is the final premium for a smoker looking at HealthGuard?"})
    print(f"\nFinal Answer: {res2['output']}\n")