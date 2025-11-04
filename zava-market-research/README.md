# af-foundry-workflows

AI-powered workflow system for market research and supplier analysis with integrated Azure AI Search, Microsoft Fabric, and GitHub capabilities.

## Features

### Core Workflow
- **Multi-agent market research**: Compliance, commercial, and procurement analysis
- **Intelligent routing**: Competitive proposals go to negotiation, non-competitive to review
- **Comprehensive insights aggregation**: Fan-out to experts, fan-in for decision making

### Integrations

#### 🔍 Azure AI Search
- **Document search**: Semantic and keyword-based search across supplier documents
- **Compliance research**: ESG and sustainability document analysis
- **Market intelligence**: Competitive analysis and best practices discovery

#### 📊 Microsoft Fabric
- **Data analytics**: Market insights and trend analysis
- **Financial benchmarking**: Revenue and performance metrics
- **Dataset integration**: Real-time data querying from Fabric workspaces

#### 🐙 GitHub
- **Technology stack analysis**: Supplier and competitor repository analysis
- **Open source compliance**: License and security pattern detection
- **Industry trends**: Trending topics and technology adoption patterns

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.template` to `.env` and fill in your credentials:

```bash
cp .env.template .env
```

### 3. Required Environment Variables

#### Azure OpenAI (Required)
- `AZURE_OPENAI_API_KEY_GPT5`: Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT_GPT5`: Your Azure OpenAI endpoint
- `AZURE_OPENAI_MODEL_DEPLOYMENT_NAME_GPT5`: Model deployment name (e.g., gpt-4)

#### Azure AI Search (Optional)
- `AZURE_SEARCH_ENDPOINT`: Your search service endpoint
- `AZURE_SEARCH_API_KEY`: Search service API key
- `AZURE_SEARCH_INDEX_NAME`: Index name (default: documents)

#### Microsoft Fabric (Optional)
- `FABRIC_WORKSPACE_ID`: Your Fabric workspace ID
- `FABRIC_TENANT_ID`: Your Azure tenant ID
- `FABRIC_ACCESS_TOKEN`: Fabric access token

#### GitHub (Optional)
- `GITHUB_TOKEN`: Personal access token for GitHub API

### 4. Run the Workflow
```bash
python workflow.py
```

Access the workflow at: http://localhost:8090

## Architecture

### Expert Agents
1. **Legal/Compliance Researcher**: ESG analysis, regulatory compliance
2. **Commercial Researcher**: Market competitiveness, pricing analysis
3. **Procurement Researcher**: Cost-effectiveness, strategic fit

### Decision Flow
```
Input → Dispatcher → [Compliance, Commercial, Procurement] → Aggregator → Decision
                                                                           ↓
                                                               Competitive? 
                                                              ↙          ↘
                                                      Negotiator    Review & Dismiss
```

### Enhanced Capabilities

#### AI Search Integration
- Semantic search across compliance documents
- Competitive intelligence gathering
- Best practices discovery

#### Fabric Analytics
- Real-time market trend analysis
- Financial performance benchmarking
- Data-driven insights generation

#### GitHub Intelligence
- Supplier technology stack assessment
- Open source compliance analysis
- Industry trend monitoring

## Usage Examples

### Basic Supplier Analysis
Submit a supplier proposal through the DevUI interface. The system will:
1. Analyze compliance and ESG factors
2. Evaluate commercial competitiveness
3. Assess procurement fit
4. Make competitive/non-competitive decision
5. Route to appropriate next steps

### Enhanced Research
With integrations enabled, the system provides:
- Document-backed compliance analysis from AI Search
- Market trend validation from Fabric data
- Technology stack assessment from GitHub
- Comprehensive competitive intelligence

## Mock Mode
If integration credentials are not provided, the system runs in mock mode with sample data, allowing you to test the workflow structure without external dependencies.

## Development

### Adding New Integrations
1. Create integration class in `workflow.py`
2. Add environment variables to `.env.template`
3. Update agent instructions to leverage new capabilities
4. Test in mock mode first

### Extending Workflows
The framework supports:
- Additional expert agents
- Complex routing logic
- Custom decision criteria
- Multi-step workflows

## License
This project is licensed under the MIT License.