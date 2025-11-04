"""
Zava Market Research Workflow
A simplified demo showcasing AI Search, Fabric, and GitHub integrations
"""

import os
import logging
from dataclasses import dataclass
from typing import Any, Never
from pydantic import BaseModel
import requests
import json

from agent_framework import (
    AgentExecutor, AgentExecutorRequest, AgentExecutorResponse,
    ChatMessage, Executor, Role, WorkflowBuilder, WorkflowContext,
    Case, Default, handler
)
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework.devui import serve

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize AI client
chat_client = AzureOpenAIChatClient(
    api_key=os.environ.get("AZURE_OPENAI_API_KEY_GPT5"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT_GPT5"),
    deployment_name=os.environ.get("AZURE_OPENAI_MODEL_DEPLOYMENT_NAME_GPT5"),
    api_version="2024-02-15-preview"
)

# === AI INTEGRATIONS ===

class AISearchClient:
    """Azure AI Search integration with real API calls"""
    
    def __init__(self):
        self.endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
        self.api_key = os.environ.get("AZURE_SEARCH_API_KEY")
        self.index = os.environ.get("AZURE_SEARCH_INDEX_NAME", "supplier-docs")
        self.api_version = "2023-11-01"
    
    def search(self, query: str, top: int = 5):
        """Search documents with AI Search"""
        if not self.endpoint or not self.api_key:
            return {"error": "AI Search credentials not configured"}
        
        search_url = f"{self.endpoint}/indexes/{self.index}/docs/search?api-version={self.api_version}"
        
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        
        payload = {
            "search": query,
            "top": top,
            "includeTotalCount": True,
            "queryType": "simple"
        }
        
        try:
            response = requests.post(search_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return {
                "results": data.get("value", []),
                "total": data.get("@odata.count", 0),
                "query_time": f"{response.elapsed.total_seconds():.2f}s"
            }
        except requests.exceptions.RequestException as e:
            return {"error": f"AI Search API error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

class FabricClient:
    """Microsoft Fabric integration with real API calls"""
    
    def __init__(self):
        self.workspace_id = os.environ.get("FABRIC_WORKSPACE_ID")
        self.access_token = os.environ.get("FABRIC_ACCESS_TOKEN")
        self.base_url = "https://api.fabric.microsoft.com/v1"
    
    def query_dataset(self, dataset: str, query: str):
        """Query Fabric dataset"""
        if not self.workspace_id or not self.access_token:
            return {"error": "Fabric credentials not configured"}
        
        fabric_url = f"{self.base_url}/workspaces/{self.workspace_id}/items/{dataset}/executeQueries"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "queries": [{"query": query}],
            "serializerSettings": {"includeNulls": False}
        }
        
        try:
            response = requests.post(fabric_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return {
                "dataset": dataset,
                "results": data.get("results", []),
                "execution_time": f"{response.elapsed.total_seconds():.2f}s"
            }
        except requests.exceptions.RequestException as e:
            return {"error": f"Fabric API error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    def get_market_insights(self, category: str):
        """Get market insights from Fabric"""
        # This would typically query a specific dataset for market data
        return self.query_dataset("market-insights", f"SELECT * FROM market_data WHERE category = '{category}'")

class GitHubClient:
    """GitHub integration with real API calls"""
    
    def __init__(self):
        self.token = os.environ.get("GITHUB_TOKEN")
        self.api_url = "https://api.github.com"
    
    def search_repos(self, query: str):
        """Search GitHub repositories"""
        search_url = f"{self.api_url}/search/repositories"
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Workflow-Demo"
        }
        
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": 5
        }
        
        try:
            response = requests.get(search_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return {
                "total_count": data.get("total_count", 0),
                "items": data.get("items", []),
                "query_time": f"{response.elapsed.total_seconds():.2f}s"
            }
        except requests.exceptions.RequestException as e:
            return {"error": f"GitHub API error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    def analyze_tech_stack(self, org: str):
        """Analyze organization's technology stack"""
        if not org:
            return {"error": "Organization name required"}
        
        # Get organization repos
        org_url = f"{self.api_url}/orgs/{org}/repos"
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Workflow-Demo"
        }
        
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        
        params = {
            "per_page": 50,
            "sort": "updated"
        }
        
        try:
            response = requests.get(org_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            repos = response.json()
            
            # Analyze languages
            languages = {}
            total_repos = len(repos)
            
            for repo in repos:
                if repo.get("language"):
                    lang = repo["language"]
                    languages[lang] = languages.get(lang, 0) + 1
            
            return {
                "organization": org,
                "total_repos": total_repos,
                "languages": list(languages.keys()),
                "language_distribution": languages,
                "query_time": f"{response.elapsed.total_seconds():.2f}s"
            }
        except requests.exceptions.RequestException as e:
            return {"error": f"GitHub API error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

# Initialize integrations
ai_search = AISearchClient()
fabric = FabricClient()
github = GitHubClient()

# === SMART TOOLS WITH AI INTEGRATIONS ===

def smart_supplier_research(query: str) -> str:
    """AI-powered supplier research using Search, GitHub, and Fabric"""
    
    # Call AI Search integration
    search_results = ai_search.search(f"supplier {query}")
    
    # Call Fabric for market data
    market_data = fabric.get_market_insights(query)
    financial_data = fabric.query_dataset("suppliers", f"category='{query}'")
    
    # Call GitHub for tech analysis
    github_data = github.search_repos(f"{query} supplier")
    tech_stack = github.analyze_tech_stack(query.replace(" ", "-"))
    
    # Handle potential errors and format response
    result = "🔍 **AI Search Results**:\n"
    if "error" in search_results:
        result += f"• Error: {search_results['error']}\n"
    elif search_results.get('results') and len(search_results['results']) >= 2:
        result += f"• Found {search_results['total']} documents in {search_results['query_time']}\n"

    else:
        result += "• No search results available\n"
    
    result += "\n📊 **Fabric Market Analytics**:\n"
    if "error" in market_data:
        result += f"• Error: {market_data['error']}\n"
    else:
        result += f"• Market data analysis completed\n"
    
    result += "\n⚡ **GitHub Technology Analysis**:\n"
    if "error" in github_data:
        result += f"• Error: {github_data['error']}\n"
    elif github_data.get('items') and len(github_data['items']) > 0:
        result += f"• Found {github_data['total_count']} repositories\n"
        if tech_stack.get('languages'):
            result += f"• Languages: {', '.join(tech_stack['languages'][:3])}\n"
    else:
        result += "• No GitHub data available\n"
    
    return result

def smart_financial_analysis(company: str) -> str:
    """Enhanced financial analysis with AI insights"""
    
    # Call Fabric for financial datasets
    financial_metrics = fabric.query_dataset("financials", f"company='{company}'")
    market_insights = fabric.get_market_insights(f"{company} financial")
    
    # Call AI Search for financial documents
    financial_docs = ai_search.search(f"{company} financial performance")
    
    # Call GitHub for tech investment analysis
    tech_analysis = github.analyze_tech_stack(company.lower().replace(" ", "-"))
    
    result = f"💰 **Financial Analysis for {company}**:\n\n"
    
    result += "📈 **Fabric Financial Data**:\n"
    if "error" in financial_metrics:
        result += f"• Error: {financial_metrics['error']}\n"
    else:
        result += f"• Financial data query completed in {financial_metrics.get('execution_time', 'N/A')}\n"
    
    result += "\n📊 **Market Intelligence**:\n"
    if "error" in market_insights:
        result += f"• Error: {market_insights['error']}\n"
    else:
        result += "• Market analysis completed\n"
    
    result += "\n🔍 **AI Search - Financial Docs**:\n"
    if "error" in financial_docs:
        result += f"• Error: {financial_docs['error']}\n"
    elif financial_docs.get('results'):
        result += f"• Found {financial_docs['total']} financial documents\n"
    else:
        result += "• No financial documents available\n"
    
    result += "\n🔗 **GitHub Tech Investment**:\n"
    if "error" in tech_analysis:
        result += f"• Error: {tech_analysis['error']}\n"
    else:
        result += f"• Analysis completed for {tech_analysis.get('organization', 'organization')}\n"
        if tech_analysis.get('total_repos'):
            result += f"• Total repos: {tech_analysis['total_repos']}\n"
    
    return result

def smart_compliance_check(supplier: str) -> str:
    """Comprehensive compliance analysis"""
    
    # Call AI Search for compliance documents
    compliance_docs = ai_search.search(f"{supplier} compliance ESG")
    
    # Call Fabric for compliance metrics
    compliance_data = fabric.query_dataset("compliance", f"supplier='{supplier}'")
    
    # Call GitHub for security analysis
    security_repos = github.search_repos(f"{supplier} security compliance")
    
    result = f"✅ **Compliance Report for {supplier}**:\n\n"
    
    result += "📋 **AI Search - Compliance Docs**:\n"
    if "error" in compliance_docs:
        result += f"• Error: {compliance_docs['error']}\n"
    elif compliance_docs.get('results'):
        result += f"• Found {compliance_docs['total']} compliance documents\n"
    else:
        result += "• No compliance documents available\n"
    
    result += "\n📊 **Fabric Compliance Metrics**:\n"
    if "error" in compliance_data:
        result += f"• Error: {compliance_data['error']}\n"
    else:
        result += "• Compliance metrics analysis completed\n"
    
    result += "\n⚖️ **GitHub Security Analysis**:\n"
    if "error" in security_repos:
        result += f"• Error: {security_repos['error']}\n"
    elif security_repos.get('items'):
        result += f"• Found {security_repos['total_count']} security repositories\n"
    else:
        result += "• No security repositories available\n"
    
    return result

# === WORKFLOW STRUCTURE ===

class CompetitiveResult(BaseModel):
    is_competitive: bool

def is_competitive():
    def condition(message: Any) -> bool:
        return isinstance(message, CompetitiveResult) and message.is_competitive
    return condition

@dataclass
class Insights:
    compliance: str
    commercial: str
    procurement: str

    def __str__(self) -> str:
        return f"""
🏢 COMPLIANCE FINDINGS:
{self.compliance}

💼 COMMERCIAL ANALYSIS:
{self.commercial}

📦 PROCUREMENT ASSESSMENT:
{self.procurement}
"""

class InsightsResult(CompetitiveResult):
    insights: Insights

    def __str__(self) -> str:
        return str(self.insights)

class DispatchToExperts(Executor):
    """Fan-out to expert agents"""
    def __init__(self, expert_ids: list[str]):
        super().__init__("dispatch_to_experts")
        self._expert_ids = expert_ids

    @handler
    async def dispatch(self, prompt: str, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
        message = ChatMessage(Role.USER, text=prompt)
        for expert_id in self._expert_ids:
            await ctx.send_message(
                AgentExecutorRequest(messages=[message], should_respond=True),
                target_id=expert_id
            )

class AggregateInsights(Executor):
    """Fan-in from expert agents"""
    def __init__(self, expert_ids: list[str]):
        super().__init__("aggregate_insights")
        self._expert_ids = expert_ids

    @handler
    async def aggregate(self, results: list[AgentExecutorResponse], ctx: WorkflowContext[InsightsResult]) -> None:
        # Collect expert responses
        by_id = {r.executor_id: r.agent_run_response.text for r in results}
        
        insights = Insights(
            compliance=by_id.get("compliance_expert", ""),
            commercial=by_id.get("commercial_expert", ""),
            procurement=by_id.get("procurement_expert", "")
        )

        # AI decision making
        consolidated = f"""
Based on these expert insights, determine if this proposal is COMPETITIVE:

{insights}

Decision factors:
- Compliance score and risk level
- Commercial viability and market position  
- Procurement value and strategic fit
"""

        evaluator = chat_client.create_agent(
            instructions="You are an expert evaluator. Analyze the insights and determine if the proposal is competitive. Look for strong compliance, good financial metrics, and strategic value. Respond with clear reasoning."
        )
        
        response = await evaluator.run(consolidated)
        is_competitive_decision = 'competitive' in response.text.lower() and 'not competitive' not in response.text.lower()

        result = InsightsResult(is_competitive=is_competitive_decision, insights=insights)
        await ctx.send_message(result)

class NegotiatorExecutor(Executor):
    @handler
    async def handle(self, request: InsightsResult, ctx: WorkflowContext[Never, str]) -> AgentExecutorResponse:
        negotiator = chat_client.create_agent(
            instructions="You're a skilled negotiator. Create a winning negotiation strategy based on the competitive analysis. Use the AI insights to identify leverage points and optimal terms.",
            tools=[smart_supplier_research]
        )
        
        response = await negotiator.run(f"Create negotiation strategy for this competitive proposal:\n{request}")
        await ctx.yield_output(f"🤝 NEGOTIATION STRATEGY:\n{response.text}")
        return AgentExecutorResponse(executor_id=self.id, agent_run_response=response)

class ReviewExecutor(Executor):
    @handler  
    async def handle(self, request: InsightsResult, ctx: WorkflowContext[Never, str]) -> AgentExecutorResponse:
        reviewer = chat_client.create_agent(
            instructions="You review non-competitive proposals. Provide clear reasons for rejection and suggest improvements. Be constructive but decisive."
        )
        
        response = await reviewer.run(f"Review this non-competitive proposal:\n{request}")
        await ctx.yield_output(f"❌ PROPOSAL REVIEW:\n{response.text}")
        return AgentExecutorResponse(executor_id=self.id, agent_run_response=response)

# === EXPERT AGENTS ===

compliance_expert = AgentExecutor(
    chat_client.create_agent(
        instructions="You're a compliance expert for Zava stores. Analyze supplier proposals for legal, regulatory, and ESG compliance using AI-powered research tools.",
        tools=[smart_compliance_check]
    ),
    id="compliance_expert"
)

commercial_expert = AgentExecutor(
    chat_client.create_agent(
        instructions="You're a commercial analyst. Evaluate market competitiveness, pricing, and business value using AI-powered financial analysis and market intelligence.",
        tools=[smart_financial_analysis]
    ),
    id="commercial_expert"
)

procurement_expert = AgentExecutor(
    chat_client.create_agent(
        instructions="You're a procurement specialist. Assess supplier proposals for cost-effectiveness, strategic fit, and operational value using smart research tools.",
        tools=[smart_supplier_research]
    ),
    id="procurement_expert"
)

# === WORKFLOW ASSEMBLY ===

experts = [compliance_expert, commercial_expert, procurement_expert]
expert_ids = [e.id for e in experts]

dispatcher = DispatchToExperts(expert_ids)
aggregator = AggregateInsights(expert_ids)
negotiator = NegotiatorExecutor("negotiator")
reviewer = ReviewExecutor("reviewer")

workflow = (
    WorkflowBuilder(name="🚀 Zava AI Market Research")
    .set_start_executor(dispatcher)
    .add_fan_out_edges(dispatcher, experts)
    .add_fan_in_edges(experts, aggregator)
    .add_switch_case_edge_group(
        aggregator,
        [
            Case(condition=is_competitive(), target=negotiator),
            Default(target=reviewer)
        ]
    )
    .build()
)

def main():
    """Launch the AI-powered market research workflow"""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    logger.info("🚀 Starting Zava AI Market Research Workflow")
    logger.info("🌐 Available at: http://localhost:8090")
    logger.info("🔧 Integrations: AI Search + Fabric + GitHub")

    serve(entities=[workflow], port=8090, auto_open=True)

if __name__ == "__main__":
    main()