#!/usr/bin/env python3
"""
Integration test script for af-foundry-workflows
Tests the integration setup and basic functionality
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def test_environment_setup():
    """Test environment variable configuration."""
    print("🔧 Testing Environment Setup...")
    
    required_vars = [
        "AZURE_OPENAI_API_KEY_GPT5",
        "AZURE_OPENAI_ENDPOINT_GPT5", 
        "AZURE_OPENAI_MODEL_DEPLOYMENT_NAME_GPT5"
    ]
    
    optional_vars = {
        "Azure AI Search": ["AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_API_KEY"],
        "Microsoft Fabric": ["FABRIC_WORKSPACE_ID", "FABRIC_ACCESS_TOKEN"],
        "GitHub": ["GITHUB_TOKEN"]
    }
    
    # Check required variables
    missing_required = []
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    if missing_required:
        print(f"❌ Missing required environment variables: {', '.join(missing_required)}")
        return False
    else:
        print("✅ Required environment variables configured")
    
    # Check optional integrations
    for service, vars_list in optional_vars.items():
        configured = all(os.getenv(var) for var in vars_list)
        status = "✅" if configured else "⚠️"
        mode = "configured" if configured else "mock mode"
        print(f"{status} {service}: {mode}")
    
    return True

def test_integrations():
    """Test integration classes initialization."""
    print("\n🔌 Testing Integration Classes...")
    
    try:
        from workflow import AISearchIntegration, FabricIntegration, GitHubIntegration
        
        # Test AI Search
        ai_search = AISearchIntegration()
        search_results = ai_search.search_documents("test query")
        print(f"✅ AI Search: {len(search_results)} results returned")
        
        # Test GitHub
        github = GitHubIntegration()
        trending = github.get_trending_topics()
        print(f"✅ GitHub: {len(trending)} trending topics")
        
        # Test Fabric
        fabric = FabricIntegration()
        insights = fabric.get_market_insights("test category")
        print(f"✅ Fabric: Market insights for '{insights['category']}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

async def test_enhanced_functions():
    """Test enhanced tool functions."""
    print("\n🛠️ Testing Enhanced Functions...")
    
    try:
        from workflow import enhanced_supplier_research, enhanced_financial_analysis, enhanced_compliance_research
        
        # Test supplier research
        supplier_result = enhanced_supplier_research("tech supplier")
        print(f"✅ Supplier research: {len(supplier_result)} characters returned")
        
        # Test financial analysis
        financial_result = await enhanced_financial_analysis("TestCorp")
        print(f"✅ Financial analysis: {len(financial_result)} characters returned")
        
        # Test compliance research
        compliance_result = enhanced_compliance_research("GreenTech")
        print(f"✅ Compliance research: {len(compliance_result)} characters returned")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced functions test failed: {e}")
        return False

def test_workflow_structure():
    """Test workflow structure and agents."""
    print("\n🔄 Testing Workflow Structure...")
    
    try:
        from workflow import workflow, compliance, commercial, procurement
        
        print(f"✅ Workflow: '{workflow.name}' with {len(workflow._executors)} executors")
        print(f"✅ Compliance agent: {compliance.id}")
        print(f"✅ Commercial agent: {commercial.id}")
        print(f"✅ Procurement agent: {procurement.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow structure test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 af-foundry-workflows Integration Test\n")
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Integration Classes", test_integrations),
        ("Enhanced Functions", test_enhanced_functions),
        ("Workflow Structure", test_workflow_structure)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Summary:")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your integration setup is ready.")
        print("\nNext steps:")
        print("1. Run: python workflow.py")
        print("2. Open: http://localhost:8090")
        print("3. Submit a supplier proposal to test the workflow")
    else:
        print("\n⚠️ Some tests failed. Check your configuration and try again.")
        
        # Provide specific guidance
        if not any(result for name, result in results if name == "Environment Setup"):
            print("\n💡 Tip: Copy .env.template to .env and configure your credentials")

if __name__ == "__main__":
    asyncio.run(main())