import os
import boto3
from dotenv import load_dotenv
from langchain_aws import ChatBedrock, BedrockEmbeddings
from langchain_chroma import Chroma
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Load the secret keys
load_dotenv()

# 1. Setup Bedrock Clients
bedrock_client = boto3.client(
    service_name='bedrock-runtime', 
    region_name=os.getenv('AWS_DEFAULT_REGION')
)

# We need the embedding model to convert the user's search query into a vector
embeddings = BedrockEmbeddings(
    client=bedrock_client,
    model_id="amazon.titan-embed-text-v2:0"
)

# We need the Chat model to actually write the final answer
llm = ChatBedrock(
    client=bedrock_client, 
    model_id="anthropic.claude-3-haiku-20240307-v1:0"
)

def test_rag():
    print("Loading Vector Database...")
    # 2. Connect to the local ChromaDB we built in Phase 2
    vectorstore = Chroma(
        persist_directory="./chroma_db", 
        embedding_function=embeddings
    )
    
    # Set up the retriever to fetch the top 3 most relevant chunks
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # 3. Create the Prompt Template (This is a basic Guardrail!)
    system_prompt = (
        "You are an expert insurance assistant for Allianz. "
        "Use the following pieces of retrieved context to answer the question. "
        "If you don't know the answer, or if the context doesn't contain the answer, "
        "just say 'I cannot answer this based on the policy documents.' Do not guess.\n\n"
        "Context: {context}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # 4. Chain it all together
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    # 5. Run a test query against our dummy data
    test_question = "What is the waiting period for pre-existing conditions?"
    print(f"\nUser Question: {test_question}")
    print("Agent is searching and thinking...")
    
    response = rag_chain.invoke({"input": test_question})
    print(f"\nFinal Answer: {response['answer']}")

if __name__ == "__main__":
    test_rag()