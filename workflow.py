from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient
from agent_framework.devui import serve
import asyncio
import logging
import json
from datetime import datetime

from dataclasses import dataclass

from pydantic import BaseModel
from agent_framework import (
    AgentExecutor,
    AgentExecutorRequest,
    AgentExecutorResponse,
    ChatMessage,
    Executor,
    Role,
    WorkflowBuilder,
    WorkflowContext,
    Case,
    Default,
    handler,
)
from typing import Any, Never, List, Dict, Optional
import os
from agent_framework.azure import AzureOpenAIChatClient
from dotenv import load_dotenv
load_dotenv()

# AI Search integration
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

# GitHub integration
from github import Github

# Fabric integration
import requests
import aiohttp

# from zava_shop_agents import MCPStreamableHTTPToolOTEL

chat_client = AzureOpenAIChatClient(api_key=os.environ.get("AZURE_OPENAI_API_KEY_GPT5"),
                                    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT_GPT5"),
                                    deployment_name=os.environ.get("AZURE_OPENAI_MODEL_DEPLOYMENT_NAME_GPT5"),
                                    api_version=os.environ.get("AZURE_OPENAI_ENDPOINT_VERSION_GPT5", "2024-02-15-preview"))


class AISearchIntegration:
    """Integration with Azure AI Search for document search and retrieval."""
    
    def __init__(self):
        self.endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT", "")
        self.api_key = os.environ.get("AZURE_SEARCH_API_KEY", "")
        self.index_name = os.environ.get("AZURE_SEARCH_INDEX_NAME", "documents")
        
        if self.api_key:
            credential = AzureKeyCredential(self.api_key)
        else:
            credential = DefaultAzureCredential()
            
        if self.endpoint:
            self.search_client = SearchClient(
                endpoint=self.endpoint,
                index_name=self.index_name,
                credential=credential
            )
        else:
            self.search_client = None
    
    def search_documents(self, query: str, top: int = 5) -> List[Dict]:
        """Search for documents related to the query."""
        if not self.search_client:
            return [{"content": f"Mock search result for: {query}", "score": 0.8}]
        
        try:
            results = self.search_client.search(
                search_text=query,
                top=top,
                include_total_count=True
            )
            
            return [
                {
                    "content": result.get("content", ""),
                    "title": result.get("title", ""),
                    "score": result.get("@search.score", 0),
                    "metadata": {k: v for k, v in result.items() if not k.startswith("@")}
                }
                for result in results
            ]
        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]
    
    def semantic_search(self, query: str, top: int = 5) -> List[Dict]:
        """Perform semantic search using vector similarity."""
        if not self.search_client:
            return [{"content": f"Mock semantic search result for: {query}", "score": 0.9}]
        
        try:
            # For semantic search, you'd typically use a vectorized query
            # This is a simplified version
            results = self.search_client.search(
                search_text=query,
                query_type="semantic",
                top=top
            )
            
            return [
                {
                    "content": result.get("content", ""),
                    "title": result.get("title", ""),
                    "score": result.get("@search.score", 0),
                    "captions": result.get("@search.captions", [])
                }
                for result in results
            ]
        except Exception as e:
            return [{"error": f"Semantic search failed: {str(e)}"}]


class FabricIntegration:
    """Integration with Microsoft Fabric for data analytics and insights."""
    
    def __init__(self):
        self.workspace_id = os.environ.get("FABRIC_WORKSPACE_ID", "")
        self.tenant_id = os.environ.get("FABRIC_TENANT_ID", "")
        self.access_token = os.environ.get("FABRIC_ACCESS_TOKEN", "")
        self.base_url = "https://api.fabric.microsoft.com/v1"
    
    async def get_datasets(self) -> List[Dict]:
        """Retrieve available datasets from Fabric workspace."""
        if not self.access_token:
            return [{"name": "mock_dataset", "id": "mock_id", "type": "sample"}]
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/workspaces/{self.workspace_id}/items"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("value", [])
                    else:
                        return [{"error": f"Failed to fetch datasets: {response.status}"}]
        except Exception as e:
            return [{"error": f"Fabric API error: {str(e)}"}]
    
    async def query_data(self, dataset_id: str, query: str) -> Dict:
        """Execute a query against a Fabric dataset."""
        if not self.access_token:
            return {
                "results": [{"metric": "revenue", "value": 1000000, "period": "Q4"}],
                "query": query,
                "dataset": dataset_id
            }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "serializerSettings": {
                "includeNulls": False
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/workspaces/{self.workspace_id}/items/{dataset_id}/executeQueries"
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"Query failed: {response.status}"}
        except Exception as e:
            return {"error": f"Query execution error: {str(e)}"}
    
    def get_market_insights(self, category: str) -> Dict:
        """Get market insights for a specific category."""
        # Mock implementation - in real scenario, this would query Fabric datasets
        return {
            "category": category,
            "market_trend": "growing",
            "projected_growth": "15%",
            "key_factors": ["sustainability", "cost-effectiveness", "innovation"],
            "timestamp": datetime.now().isoformat()
        }


class GitHubIntegration:
    """Integration with GitHub for repository analysis and collaboration."""
    
    def __init__(self):
        self.token = os.environ.get("GITHUB_TOKEN", "")
        if self.token:
            self.github = Github(self.token)
        else:
            self.github = None
    
    def get_repository_info(self, repo_name: str) -> Dict:
        """Get information about a GitHub repository."""
        if not self.github:
            return {
                "name": repo_name,
                "description": f"Mock repository: {repo_name}",
                "stars": 100,
                "forks": 25,
                "language": "Python"
            }
        
        try:
            repo = self.github.get_repo(repo_name)
            return {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "language": repo.language,
                "topics": repo.get_topics(),
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat(),
                "open_issues": repo.open_issues_count
            }
        except Exception as e:
            return {"error": f"Failed to fetch repository info: {str(e)}"}
    
    def search_repositories(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for repositories on GitHub."""
        if not self.github:
            return [
                {"name": f"mock-repo-{i}", "description": f"Mock result {i} for query: {query}"}
                for i in range(min(limit, 3))
            ]
        
        try:
            repos = self.github.search_repositories(query=query)
            results = []
            
            for i, repo in enumerate(repos):
                if i >= limit:
                    break
                results.append({
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "stars": repo.stargazers_count,
                    "language": repo.language,
                    "url": repo.html_url
                })
            
            return results
        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]
    
    def get_trending_topics(self) -> List[str]:
        """Get trending topics from GitHub."""
        # This is a simplified implementation
        # In practice, you might analyze trending repositories
        return [
            "artificial-intelligence",
            "machine-learning",
            "sustainability",
            "cloud-computing",
            "blockchain",
            "iot",
            "cybersecurity"
        ]
    
    def analyze_competitor_repos(self, company_name: str) -> Dict:
        """Analyze competitor repositories."""
        if not self.github:
            return {
                "company": company_name,
                "repositories": 5,
                "total_stars": 1500,
                "primary_languages": ["Python", "JavaScript", "Go"],
                "recent_activity": "High"
            }
        
        try:
            repos = self.github.search_repositories(query=f"user:{company_name}")
            
            total_stars = 0
            languages = {}
            repo_count = 0
            
            for repo in repos:
                if repo_count >= 20:  # Limit analysis to first 20 repos
                    break
                total_stars += repo.stargazers_count
                if repo.language:
                    languages[repo.language] = languages.get(repo.language, 0) + 1
                repo_count += 1
            
            return {
                "company": company_name,
                "repositories": repo_count,
                "total_stars": total_stars,
                "primary_languages": sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5],
                "language_distribution": languages
            }
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}


# Initialize integrations
ai_search = AISearchIntegration()
fabric_integration = FabricIntegration()
github_integration = GitHubIntegration()

# Enhanced tool functions with AI Search, Fabric, and GitHub integrations

def enhanced_supplier_research(query: str) -> str:
    """Enhanced supplier research using AI Search, Fabric, and GitHub."""
    results = []
    
    # AI Search for supplier documents
    search_results = ai_search.search_documents(f"supplier {query}")
    if search_results:
        results.append("=== AI Search Results ===")
        for result in search_results[:3]:
            if "error" not in result:
                results.append(f"- {result.get('title', 'Document')}: {result.get('content', '')[:200]}...")
    
    # GitHub analysis for supplier technology stack
    github_results = github_integration.search_repositories(f"{query} supplier")
    if github_results:
        results.append("\n=== GitHub Technology Analysis ===")
        for repo in github_results[:2]:
            if "error" not in repo:
                results.append(f"- {repo['name']}: {repo.get('description', 'No description')} (⭐{repo.get('stars', 0)})")
    
    # Fabric market insights
    market_insights = fabric_integration.get_market_insights(query)
    if market_insights and "error" not in market_insights:
        results.append(f"\n=== Market Insights ===")
        results.append(f"- Trend: {market_insights.get('market_trend', 'Unknown')}")
        results.append(f"- Growth: {market_insights.get('projected_growth', 'N/A')}")
        results.append(f"- Key Factors: {', '.join(market_insights.get('key_factors', []))}")
    
    return "\n".join(results) if results else f"Research data for {query}: Standard supplier with good reputation"

async def enhanced_financial_analysis(company: str) -> str:
    """Enhanced financial analysis using Fabric data insights."""
    results = []
    
    # Fabric datasets analysis
    datasets = await fabric_integration.get_datasets()
    if datasets and not any("error" in d for d in datasets):
        results.append("=== Fabric Data Analysis ===")
        results.append(f"Available datasets: {len(datasets)}")
    
    # Market insights from Fabric
    financial_insights = fabric_integration.get_market_insights(f"{company} financial")
    if financial_insights and "error" not in financial_insights:
        results.append(f"- Financial trend: {financial_insights.get('market_trend', 'stable')}")
        results.append(f"- Growth projection: {financial_insights.get('projected_growth', '5%')}")
    
    # GitHub competitor analysis
    competitor_analysis = github_integration.analyze_competitor_repos(company.lower().replace(" ", "-"))
    if competitor_analysis and "error" not in competitor_analysis:
        results.append(f"\n=== GitHub Competitor Analysis ===")
        results.append(f"- Repositories: {competitor_analysis.get('repositories', 0)}")
        results.append(f"- Total stars: {competitor_analysis.get('total_stars', 0)}")
        results.append(f"- Languages: {', '.join(str(lang[0]) for lang in competitor_analysis.get('primary_languages', [])[:3])}")
    
    # AI Search for financial documents
    financial_docs = ai_search.search_documents(f"{company} financial performance revenue")
    if financial_docs:
        results.append(f"\n=== Financial Document Analysis ===")
        for doc in financial_docs[:2]:
            if "error" not in doc:
                results.append(f"- Score {doc.get('score', 0):.2f}: {doc.get('content', '')[:150]}...")
    
    return "\n".join(results) if results else f"Financial analysis for {company}: Stable performance with average market position"

def enhanced_compliance_research(supplier: str) -> str:
    """Enhanced compliance research using AI Search and GitHub."""
    results = []
    
    # AI Search for compliance documents
    compliance_docs = ai_search.semantic_search(f"{supplier} compliance ESG sustainability")
    if compliance_docs:
        results.append("=== Compliance Document Analysis ===")
        for doc in compliance_docs[:3]:
            if "error" not in doc:
                results.append(f"- {doc.get('title', 'Document')}: {doc.get('content', '')[:200]}...")
                if doc.get('captions'):
                    results.append(f"  Key points: {', '.join(doc['captions'][:2])}")
    
    # GitHub analysis for open source compliance
    github_repos = github_integration.search_repositories(f"{supplier} compliance OR ESG OR sustainability")
    if github_repos:
        results.append(f"\n=== Open Source Compliance ===")
        for repo in github_repos[:2]:
            if "error" not in repo:
                results.append(f"- {repo['name']}: {repo.get('description', 'No description')}")
    
    # Trending compliance topics from GitHub
    trending_topics = github_integration.get_trending_topics()
    compliance_topics = [topic for topic in trending_topics if any(word in topic for word in ['sustainability', 'security', 'compliance'])]
    if compliance_topics:
        results.append(f"\n=== Industry Compliance Trends ===")
        results.append(f"- Trending: {', '.join(compliance_topics)}")
    
    return "\n".join(results) if results else f"Compliance research for {supplier}: Standard compliance profile"

# Update the existing tool functions to use enhanced versions
def supplier_mcp_tools(location: str) -> str:
    """Enhanced supplier research tool."""
    return enhanced_supplier_research(location)

async def finance_mcp_async(location: str) -> str:
    """Enhanced financial analysis tool."""
    return await enhanced_financial_analysis(location)

def finance_mcp_enhanced(location: str) -> str:
    """Enhanced financial analysis tool (sync wrapper)."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(finance_mcp_async(location))
    except RuntimeError:
        # If no event loop is running, create a new one
        return asyncio.run(finance_mcp_async(location))

def finance_mcp(location: str) -> str:
    """Enhanced financial analysis tool."""
    return finance_mcp_enhanced(location)

class CompetitiveResult(BaseModel):
    is_competitive: bool

def is_competitive():
    def condition(message: Any) -> bool:
        # Only match when the upstream payload is a DetectionResult with the expected decision.
        return isinstance(message, CompetitiveResult) and message.is_competitive

    return condition

class DispatchToExperts(Executor):
    """Dispatches the incoming prompt to all expert agent executors (fan-out)."""

    def __init__(self, expert_ids: list[str], id: str | None = None):
        super().__init__(id=id or "dispatch_to_experts")
        self._expert_ids = expert_ids

    @handler
    async def dispatch(self, prompt: str, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
        # Wrap the incoming prompt as a user message for each expert and request a response.
        initial_message = ChatMessage(Role.USER, text=prompt)
        for expert_id in self._expert_ids:
            await ctx.send_message(
                AgentExecutorRequest(messages=[initial_message], should_respond=True),
                target_id=expert_id,
            )


@dataclass
class AggregatedInsights:
    """Structured output from the aggregator."""

    compliance: str
    commercial: str
    procurement: str

    def __str__(self) -> str:
        return (
            f"Compliance Findings:\n{self.compliance}\n\n"
            f"Commercial Angle:\n{self.commercial}\n\n"
            f"Procurement Notes:\n{self.procurement}\n"
        )


class AggregateInsightsResult(CompetitiveResult):
    aggregated_insights: AggregatedInsights

    def __str__(self) -> str:
        return self.aggregated_insights.__str__()


LEGAL_COMPLIANCE_EXPERT_ID = "Legal/Compliance Researcher"
COMMERCIAL_EXPERT_ID = "Commercial Researcher"
PROCUREMENT_EXPERT_ID = "Procurement Researcher"


class AggregateInsights(Executor):
    """Aggregates expert agent responses into a single consolidated result (fan-in)."""

    def __init__(self, expert_ids: list[str], id: str | None = None):
        super().__init__(id=id or "aggregate_insights")
        self._expert_ids = expert_ids

    @handler
    async def aggregate(self, results: list[AgentExecutorResponse], ctx: WorkflowContext[AggregateInsightsResult]) -> None:
        # Map responses to text by executor id for a simple, predictable demo.
        by_id: dict[str, str] = {}
        for r in results:
            # AgentExecutorResponse.agent_run_response.text contains concatenated assistant text
            by_id[r.executor_id] = r.agent_run_response.text

        compliance_text = by_id.get(LEGAL_COMPLIANCE_EXPERT_ID, "")
        commercial_text = by_id.get(COMMERCIAL_EXPERT_ID, "")
        procurement_text = by_id.get(PROCUREMENT_EXPERT_ID, "")

        aggregated = AggregatedInsights(
            compliance=compliance_text,
            commercial=commercial_text,
            procurement=procurement_text,
        )

        # Provide a readable, consolidated string as the final workflow result.
        consolidated = (
            "Considering the consolidated Insights, decide whether this proposal is competitive or not competitive\n"
            "====================\n\n"
            f"Compliance Findings:\n{aggregated.compliance}\n\n====================\n\n"
            f"Commercial Angle:\n{aggregated.commercial}\n\n====================\n\n"
            f"Procurement Notes:\n{aggregated.procurement}\n"
        )

        chat_client_agent = chat_client.create_agent(
            instructions=(
                "You are an expert evaluator. Given the consolidated insights, determine if the proposal is competitive or not competitive. " \
                "Consider market trends, technology stack analysis from GitHub, compliance patterns from AI Search, " \
                "and financial benchmarks from Fabric analytics. Make your decision based on comprehensive data analysis."
            ),
            tools=[supplier_mcp_tools],
        )
        response = await chat_client_agent.run(consolidated)

        # Extract the competitive decision from the response text
        is_competitive_value = False
        try:
            response_text = response.text.lower() if hasattr(response, 'text') else str(response).lower()
            is_competitive_value = 'competitive' in response_text and 'not competitive' not in response_text
        except Exception:
            # Default to False if parsing fails
            is_competitive_value = False

        result = AggregateInsightsResult(is_competitive=is_competitive_value, aggregated_insights=aggregated)

        await ctx.send_message(result)

compliance = AgentExecutor(
    chat_client.create_agent(
        instructions=(
            "You're an expert legal and compliance researcher. You review a proposal and provide feedback on behalf of Zava stores. " \
            "Use the provided tools to find information about suppliers' ESG and compliance status using AI Search for document analysis, " \
            "GitHub for open source compliance patterns, and Fabric for market trend data. " \
            "Focus on sustainability metrics, regulatory compliance, and industry best practices."
        ),
        tools=[supplier_mcp_tools],
    ),
    id=LEGAL_COMPLIANCE_EXPERT_ID,
)
commercial = AgentExecutor(
    chat_client.create_agent(
        instructions=(
            "You are an expert commercial analyst. Evaluate supplier proposals for market competitiveness and value. " \
            "Use the supplied tools to understand existing stock levels, prices, demand, and market insights from Fabric analytics. " \
            "Leverage GitHub data for technology stack analysis and AI Search for competitive intelligence documents. " \
            "Provide comprehensive market positioning and competitive advantage analysis."
        ),
        tools=[finance_mcp],
    ),
    id=COMMERCIAL_EXPERT_ID,
)
procurement = AgentExecutor(
    chat_client.create_agent(
        instructions=(
            "You are an expert procurement analyst. Analyze supplier proposals for cost-effectiveness and strategic fit. " \
            "Use the supplied tools to check existing supplier contracts, performance data, and market benchmarks from Fabric. " \
            "Utilize GitHub for supplier technology assessment and AI Search for procurement best practices. " \
            "Focus on total cost of ownership, supplier reliability, and strategic alignment."
        ),
        tools=[supplier_mcp_tools],
    ),
    id=PROCUREMENT_EXPERT_ID,
)

expert_ids = [compliance.id, commercial.id, procurement.id]

dispatcher = DispatchToExperts(expert_ids=expert_ids, id="Proposal Dispatcher")
aggregator = AggregateInsights(expert_ids=expert_ids, id="Competitive Analysis Aggregator")


class NegotiatorSummarizerExecutor(Executor):
    @handler
    async def handle(self, request: AggregateInsightsResult, ctx: WorkflowContext[Never, str]) -> AgentExecutorResponse:
        chat_client_agent = chat_client.create_agent(
            instructions=(
                "You are a skilled negotiator. Given that the proposal is competitive, draft a negotiation strategy and summarize key points. " \
                "Consult with existing suppliers from the tools provided to optimize terms. " \
                "Use AI Search to find similar contract terms, GitHub to assess supplier technical capabilities, " \
                "and Fabric analytics for market benchmarking data to strengthen your negotiation position."
            ),
            tools=[supplier_mcp_tools],
        )
        response = await chat_client_agent.run(str(request))

        await ctx.yield_output(response.text)
        return AgentExecutorResponse(executor_id=self.id, agent_run_response=response)

class ReviewAndDismissExecutor(Executor):
    @handler
    async def handle(self, request: AggregateInsightsResult, ctx: WorkflowContext[Never, str]) -> AgentExecutorResponse:
        chat_client_agent = chat_client.create_agent(
            instructions=(
                "You have been asked to review a supplier proposal that is not competitive. " \
                "Provide a summary of the reasons and suggest dismissal points. " \
                "Use AI Search for market comparisons, GitHub for technology stack analysis, " \
                "and Fabric data for market benchmarking to support your dismissal recommendations with concrete data."
            ),
            tools=[supplier_mcp_tools],
        )
        response = await chat_client_agent.run(str(request))

        await ctx.yield_output(response.text)
        return AgentExecutorResponse(executor_id=self.id, agent_run_response=response)


negotiator = NegotiatorSummarizerExecutor(
    id="Negotiator & Summarizer",
)

review_and_dismiss = ReviewAndDismissExecutor(
    id="Review & Dismiss",
)

workflow = (
    WorkflowBuilder(name="Zava Market Research Workflow")
    .set_start_executor(dispatcher)
    .add_fan_out_edges(dispatcher, [compliance, commercial, procurement])
    .add_fan_in_edges([compliance, commercial, procurement], aggregator)
    .add_switch_case_edge_group(
            aggregator,
            [
                Case(condition=is_competitive(), target=negotiator),
                Default(target=review_and_dismiss),
            ],
        )
    .build()
)

def main():
    """Launch the spam detection workflow in DevUI."""
    from agent_framework.devui import serve

    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    logger.info("Starting Spam Detection Workflow")
    logger.info("Available at: http://localhost:8090")
    logger.info("Entity ID: workflow_spam_detection")

    # Launch server with the workflow
    serve(entities=[workflow], port=8090, auto_open=True)


if __name__ == "__main__":
    main()