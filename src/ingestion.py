import os
import boto3
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_aws import BedrockEmbeddings
from langchain_community.vectorstores import Chroma

# Load the secret keys from your .env file
load_dotenv()

# 1. Setup Bedrock Client for Model Invocation
# Note: We use 'bedrock-runtime' here because we are actually using the model, 
# not just listing them like in Phase 1!
bedrock_client = boto3.client(
    service_name='bedrock-runtime', 
    region_name=os.getenv('AWS_DEFAULT_REGION')
)

# 2. Initialize the Embedding Model (Amazon Titan)
embeddings = BedrockEmbeddings(
    client=bedrock_client,
    model_id="amazon.titan-embed-text-v2:0"
)

def build_vector_db():
    print("Loading policy document...")
    # Load our dummy text file
    loader = TextLoader("data/policy.txt")
    docs = loader.load()

    print("Splitting text into chunks...")
    # 3. Chunk the text
    # 300 characters is a good size for specific policy rules
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50 
    )
    chunks = text_splitter.split_documents(docs)
    print(f"Created {len(chunks)} chunks.")

    print("Generating embeddings and saving to ChromaDB (this might take a few seconds)...")
    # 4. Generate vectors and save them locally
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    print("✅ Phase 2 Complete! ChromaDB successfully created in your project folder.")

if __name__ == "__main__":
    build_vector_db()