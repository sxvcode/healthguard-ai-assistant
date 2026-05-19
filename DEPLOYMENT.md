# HealthGuard AI Assistant: Deployment & Setup Guide

This document outlines the complete end-to-end setup required to recreate the HealthGuard AI Assistant infrastructure. It covers provisioning the AWS backend (S3 & Bedrock), configuring the local container, and deploying to AWS ECS Fargate.

## 🛠️ Phase 1: Prerequisites & Assumptions

**This guide assumes the following architecture baseline:**

* **AWS Region:** `us-east-1`
* **ECS Launch Type:** Fargate
* **Application Port:** `8501` (Streamlit)
* **Network:** Public internet access enabled
* **Architecture:** Single-container deployment

**Before beginning, ensure you have the following installed and configured:**

* **Docker Desktop:** Running locally.
* **Git & Python 3.10+:** Installed on your local machine.
* **AWS Environment:** Access to an AWS Account (or corporate Sandbox) with permissions to provision S3, Bedrock, ECR, VPC, and ECS resources.
* **AWS Credentials:** Active `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN`.

---

## ☁️ Phase 2: AWS Backend Provisioning (S3 & Bedrock)

The application relies on Amazon Bedrock for orchestration and S3 Vectors for retrieval.

### Step 1: Create the Knowledge Base (Vector Store)

1. Navigate to **Amazon S3** in the AWS Console.
2. Create a new private bucket (e.g., `healthguard-knowledge-base-data`).
3. Upload the `data/policy.txt` file from this repository into the bucket.
4. Navigate to **Amazon Bedrock -> Knowledge Bases** and click Create Knowledge Base.
5. In the data source section, select the S3 URI of the bucket you created in Step 2.
6. In the embeddings model section, select **Titan Text Embeddings V2**.
7. Choose **Amazon S3 Vectors** as the vector database (this avoids OpenSearch provisioning limits).
8. Complete the creation process and click **Sync** to embed the policy document.

### Step 2: Create the Bedrock Agent

1. Navigate to **Amazon Bedrock -> Agents** and create a new Agent.
2. Select **Amazon Nova Pro** as the foundation model.
3. Write the following instructions for the agent and click save: *"You are the Allianz HealthGuard AI Assistant. Your job is to answer questions strictly based on the provided policy document. If a user asks about topics outside of this policy, politely refuse to answer."*
4. Under the Agent Builder, link the Knowledge Base you created in Step 1. Use the following instructions for the Knowledge Base: *"Contains the official Allianz HealthGuard policy document. Search this database whenever the user asks about coverage, limits, or rules."*
5. **Save and Prepare** the agent.
6. Create an **Alias** for the agent (e.g., `LIVE_VERSION`).
7. **CRITICAL:** Copy the **Agent ID** and the **Agent Alias ID**. You will need these for the frontend configuration.

---

## 💻 Phase 3: Application Configuration & Local Setup

### Step 1: Clone and Configure

1. Clone this repository to your local machine.
2. Open `app.py` and update the `invoke_agent` function parameters with your specific AWS IDs:

```python
agentId='YOUR_AGENT_ID',        # Paste Agent ID here
agentAliasId='YOUR_ALIAS_ID',   # Paste Alias ID here

```

3. Create a `.env` file in the root directory and add your temporary AWS credentials:

```text
AWS_ACCESS_KEY_ID="your_access_key"
AWS_SECRET_ACCESS_KEY="your_secret_key"
AWS_SESSION_TOKEN="your_session_token"
AWS_DEFAULT_REGION="us-east-1"

```

### Step 2: Local Docker Deployment

To test the integration locally before pushing to the cloud:

1. Build the Docker image:

```bash
docker build -t healthguard-local .

```

2. Run the container, passing in the environment variables:

```bash
docker run -p 8501:8501 --env-file .env healthguard-local

```

3. Access the UI at `http://localhost:8501`.

---

## 🚀 Phase 4: Production Cloud Deployment (ECS Fargate)

### Step 1: Push to Amazon ECR (Elastic Container Registry)

1. In the AWS Console, create a private ECR Repository named `healthguard-frontend`.
2. Select the newly created repository and click the **View push commands** button.
3. Open your local terminal and run the generated ECR push commands sequentially to:
* Authenticate Docker with AWS.
* Tag the local image for ECR.
* Push the container image to the cloud repository.



### Step 2: Provision Network (VPC)

1. Navigate to the **VPC Dashboard** and click **Create VPC**.
2. Select **VPC and more**.
3. Configure with **2 Public Subnets** and **0 Private Subnets** (to avoid NAT Gateway costs in sandbox environments).
4. Click **Create VPC**.

### Step 3: Create the ECS Task Definition (Blueprint)

1. Navigate to **Amazon ECS -> Task Definitions** and create a new revision.
2. Select **AWS Fargate** as the infrastructure.
3. Point the container image to your ECR URI and set the Container Port to `8501`.
4. *⚠️ IAM Sandbox Workaround:* If your environment restricts the creation of ECS Task Roles, expand the **Environment Variables** section for the container and manually inject your `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN`.

### Step 4: Launch the ECS Service

1. Create a new **ECS Cluster** using AWS Fargate.
2. Create a new **Service** within that cluster.
3. Select your newly created Task Definition.
4. Under Networking, select your custom VPC and both Public Subnets. Ensure **Auto-assign Public IP** is enabled.
5. Create a new Security Group allowing **Custom TCP on port 8501** from anywhere (`0.0.0.0/0`).
6. Launch the service. Once the task reaches a `RUNNING` state, copy the Public IP and access the live application at `http://[PUBLIC_IP]:8501`.

### Note on Credential Rotation

If utilizing the environment variable injection workaround due to IAM restrictions, the AWS session tokens will expire. To restore access without rebuilding the container:

1. Generate new AWS keys.
2. Create a new Task Definition revision with the updated keys in the environment variables.
3. Update the ECS Service and check **Force new deployment**.