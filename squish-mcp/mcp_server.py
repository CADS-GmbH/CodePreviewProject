# mcp_server.py
import os
import sys
import json
import logging
from pathlib import Path

# Import Agents
from agents.agent_object_spy import ObjectSpyAgent
from agents.agent_test_generator import TestGeneratorAgent
from agents.agent_squish_executor import SquishExecutorAgent
from agents.agent_intelligent_test_generator import IntelligentTestGeneratorAgent
from agents.troubleshoot_agent import TroubleshootingAgent
from src.squish_mcp.errors import AnalysisException, ConfigurationException, SquishMCPException

# Import Config
from config import CONFIG, setup_directories, apply_environment, validate_config

# ============================================
# LOGGING SETUP
# ============================================

logging.basicConfig(
    level=getattr(logging, CONFIG['LOG_LEVEL']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(CONFIG['LOG_DIR'], 'mcp_server.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# MCP SERVER CLASS
# ============================================

class SquishMCPServer:
    """
    Main MCP Server für Squish Test Automation
    Integriert alle 3 Agenten
    """
    
    def __init__(self):
        self.config = CONFIG
        self.agent_spy = None
        self.agent_generator = None
        self.agent_executor = None
        self.agent_intelligent_generator = None
        self.agent_troubleshooter = None
        
        logger.info("🚀 Initializing Squish MCP Server...")
        self._setup()
    
    def _setup(self):
        """Setup: Directories, Environment, Validation"""
        logger.info("📁 Setting up directories...")
        setup_directories()
        
        logger.info("🔧 Applying environment variables...")
        apply_environment()
        
        logger.info("🔍 Validating configuration...")
        if not validate_config():
            raise ConfigurationException("Configuration validation failed.")
        
        logger.info("✅ Setup completed successfully!")
    
    # ========================================
    # AGENT 1: OBJECT SPY
    # ========================================
    
    def initialize_object_spy(self, names_file_path):
        """Initialize Object Spy Agent"""
        try:
            logger.info(f"🔍 Initializing Object Spy with: {names_file_path}")
            self.agent_spy = ObjectSpyAgent(names_file_path)
            objects = self.agent_spy.parse_names_file()
            logger.info(f"✅ Found {len(objects)} UI objects")
            return {"status": "success", "objects_found": len(objects)}
        except Exception as e:
            logger.error(f"❌ Error in Object Spy: {e}")
            return {"status": "error", "message": str(e)}
    
    def find_object_by_name(self, obj_name):
        """Find a specific object by name"""
        if not self.agent_spy:
            return {"status": "error", "message": "Object Spy not initialized"}
        
        obj = self.agent_spy.get_object(obj_name)
        if obj:
            logger.info(f"✅ Found object: {obj_name}")
            return {"status": "success", "object": obj}
        else:
            logger.warning(f"⚠️ Object not found: {obj_name}")
            return {"status": "not_found", "object_name": obj_name}
    
    def find_objects_by_text(self, text):
        """Find objects by text content"""
        if not self.agent_spy:
            return {"status": "error", "message": "Object Spy not initialized"}
        
        results = self.agent_spy.find_by_text(text)
        logger.info(f"✅ Found {len(results)} objects with text: {text}")
        return {"status": "success", "count": len(results), "results": results}
    
    def find_objects_by_type(self, obj_type):
        """Find all objects of a specific type"""
        if not self.agent_spy:
            return {"status": "error", "message": "Object Spy not initialized"}
        
        results = self.agent_spy.find_by_type(obj_type)
        logger.info(f"✅ Found {len(results)} objects of type: {obj_type}")
        return {"status": "success", "count": len(results), "results": results}
    
    # ========================================
    # AGENT 2: TEST GENERATOR
    # ========================================
    
    def initialize_test_generator(self):
        """Initialize Test Generator Agent"""
        try:
            logger.info("📝 Initializing Test Generator...")
            self.agent_generator = TestGeneratorAgent()
            logger.info("✅ Test Generator initialized")
            return {"status": "success"}
        except Exception as e:
            logger.error(f"❌ Error in Test Generator: {e}")
            return {"status": "error", "message": str(e)}
    
    def generate_test(self, testcase_json):
        """Generate Python test code from JSON testcase"""
        if not self.agent_generator:
            return {"status": "error", "message": "Test Generator not initialized"}
        
        try:
            logger.info("🧪 Generating test code...")
            test_code = self.agent_generator.generate_test(testcase_json)
            logger.info("✅ Test code generated successfully")
            return {"status": "success", "test_code": test_code}
        except Exception as e:
            logger.error(f"❌ Error generating test: {e}")
            return {"status": "error", "message": str(e)}
    
    def generate_test_from_file(self, json_file_path):
        """Generate test from JSON file"""
        try:
            with open(json_file_path, 'r') as f:
                testcase = json.load(f)
            return self.generate_test(testcase)
        except Exception as e:
            logger.error(f"❌ Error reading testcase file: {e}")
            return {"status": "error", "message": str(e)}
    
    def save_test_code(self, test_code, output_file):
        """Save generated test code to file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(test_code)
            logger.info(f"✅ Test code saved to: {output_file}")
            return {"status": "success", "file": output_file}
        except Exception as e:
            logger.error(f"❌ Error saving test code: {e}")
            return {"status": "error", "message": str(e)}

    def initialize_intelligent_test_generator(self):
        """Initialize Intelligent Test Generator Agent"""
        try:
            logger.info("🧠 Initializing Intelligent Test Generator...")
            object_map = self.agent_spy.objects if self.agent_spy else {}
            if not object_map:
                logger.warning("⚠️ Object Spy is not initialized. Intelligent generation will run without object-map resolution.")
            self.agent_intelligent_generator = IntelligentTestGeneratorAgent(object_map=object_map)
            logger.info("✅ Intelligent Test Generator initialized")
            return {"status": "success"}
        except Exception as e:
            logger.error(f"❌ Error in Intelligent Test Generator: {e}")
            return {"status": "error", "message": str(e)}

    def generate_intelligent_test(self, description, options=None):
        """Generate test code directly from natural-language description"""
        if not self.agent_intelligent_generator:
            return {"status": "error", "message": "Intelligent Test Generator not initialized"}

        try:
            logger.info("🧠 Generating intelligent test code from description...")
            return self.agent_intelligent_generator.generate_test_from_description(description, options=options or {})
        except SquishMCPException as e:
            logger.error(f"❌ Squish MCP error generating intelligent test: {e}")
            return {"status": "error", "message": str(e), "error_type": type(e).__name__}
        except Exception as e:
            wrapped = AnalysisException(f"Error generating intelligent test: {e}")
            logger.error(f"❌ Error generating intelligent test: {wrapped}")
            return {"status": "error", "message": str(wrapped), "error_type": type(wrapped).__name__}

    def initialize_troubleshooting_agent(self):
        """Initialize troubleshooting helper agent."""
        try:
            self.agent_troubleshooter = TroubleshootingAgent()
            return {"status": "success"}
        except SquishMCPException as e:
            logger.error(f"❌ Squish MCP error in Troubleshooting Agent: {e}")
            return {"status": "error", "message": str(e), "error_type": type(e).__name__}
        except Exception as e:
            wrapped = ConfigurationException(f"Error in Troubleshooting Agent initialization: {e}")
            logger.error(f"❌ Error in Troubleshooting Agent: {wrapped}")
            return {"status": "error", "message": str(wrapped), "error_type": type(wrapped).__name__}

    def troubleshoot_test_error(self, user_input, error_message=None, test_code=None, environment_context=None):
        """Troubleshoot test failures from pasted error + code context."""
        if not self.agent_troubleshooter:
            init_result = self.initialize_troubleshooting_agent()
            if init_result.get("status") != "success":
                return init_result

        try:
            return self.agent_troubleshooter.troubleshoot(
                user_input=user_input,
                error_message=error_message,
                test_code=test_code,
                environment_context=environment_context,
            )
        except SquishMCPException as e:
            logger.error(f"❌ Squish MCP error troubleshooting test failure: {e}")
            return {"status": "error", "message": str(e), "error_type": type(e).__name__}
        except Exception as e:
            wrapped = AnalysisException(f"Error troubleshooting test failure: {e}")
            logger.error(f"❌ Error troubleshooting test failure: {wrapped}")
            return {"status": "error", "message": str(wrapped), "error_type": type(wrapped).__name__}
    
    # ========================================
    # AGENT 3: SQUISH EXECUTOR
    # ========================================
    
    def initialize_executor(self):
        """Initialize Squish Executor Agent"""
        try:
            logger.info("⚙️ Initializing Squish Executor...")
            self.agent_executor = SquishExecutorAgent(self.config)
            logger.info("✅ Squish Executor initialized")
            return {"status": "success"}
        except Exception as e:
            logger.error(f"❌ Error in Executor: {e}")
            return {"status": "error", "message": str(e)}
    
    def start_squish_server(self):
        """Start Squish Server"""
        if not self.agent_executor:
            return {"status": "error", "message": "Executor not initialized"}
        
        try:
            logger.info("🚀 Starting Squish Server...")
            success = self.agent_executor.start_squish_server()
            if success:
                return {"status": "success", "message": "Squish Server started"}
            else:
                return {"status": "error", "message": "Failed to start Squish Server"}
        except Exception as e:
            logger.error(f"❌ Error starting server: {e}")
            return {"status": "error", "message": str(e)}
    
    def stop_squish_server(self):
        """Stop Squish Server"""
        if not self.agent_executor:
            return {"status": "error", "message": "Executor not initialized"}
        
        try:
            logger.info("⛔ Stopping Squish Server...")
            self.agent_executor.stop_squish_server()
            return {"status": "success", "message": "Squish Server stopped"}
        except Exception as e:
            logger.error(f"❌ Error stopping server: {e}")
            return {"status": "error", "message": str(e)}
    
    def execute_test(self):
        """Execute test with SquishRunner"""
        if not self.agent_executor:
            return {"status": "error", "message": "Executor not initialized"}
        
        try:
            logger.info("🧪 Executing test...")
            result = self.agent_executor.execute_test()
            if result and result.returncode == 0:
                logger.info("✅ Test executed successfully")
                return {"status": "success", "exit_code": result.returncode}
            else:
                logger.error(f"❌ Test execution failed with code: {result.returncode}")
                return {"status": "error", "exit_code": result.returncode}
        except Exception as e:
            logger.error(f"❌ Error executing test: {e}")
            return {"status": "error", "message": str(e)}
    
    def run_full_test_workflow(self):
        """Complete workflow: Start Server -> Execute Test -> Parse Results -> Stop Server"""
        try:
            logger.info("=" * 60)
            logger.info("🚀 STARTING FULL TEST WORKFLOW")
            logger.info("=" * 60)
            
            # Step 1: Start Server
            start_result = self.start_squish_server()
            if start_result['status'] != 'success':
                return start_result
            
            # Step 2: Execute Test
            exec_result = self.execute_test()
            
            # Step 3: Parse Results
            logger.info("📊 Parsing test results...")
            results = self.agent_executor.parse_results()
            
            # Step 4: Stop Server
            self.stop_squish_server()
            
            logger.info("=" * 60)
            logger.info("✅ FULL TEST WORKFLOW COMPLETED")
            logger.info("=" * 60)
            
            return {
                "status": "success",
                "test_execution": exec_result,
                "results_file": os.path.join(self.config['RESULTS_DIR'], 'results.xml')
            }
        
        except Exception as e:
            logger.error(f"❌ Error in full workflow: {e}")
            self.stop_squish_server()
            return {"status": "error", "message": str(e)}
    
    # ========================================
    # INFO & STATUS
    # ========================================
    
    def get_status(self):
        """Get server status"""
        return {
            "status": "running",
            "server_host": self.config['MCP_HOST'],
            "server_port": self.config['MCP_PORT'],
            "squish_version": "8.0.0",
            "squish_port": self.config['SQUISH_PORT'],
            "agents_initialized": {
                "object_spy": self.agent_spy is not None,
                "test_generator": self.agent_generator is not None,
                "intelligent_test_generator": self.agent_intelligent_generator is not None,
                "executor": self.agent_executor is not None
            }
        }
    
    def get_config(self):
        """Get current configuration"""
        return self.config

# ============================================
# MAIN ENTRY POINT
# ============================================

def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("🚀 SQUISH MCP SERVER STARTING")
    logger.info("=" * 60)
    
    # Initialize Server
    server = SquishMCPServer()
    
    # Initialize all Agents
    logger.info("\n📊 Initializing all agents...")
    
    # Agent 1: Object Spy
    names_file = os.path.join(CONFIG['TEST_SUITE'], 'names.py')
    if os.path.exists(names_file):
        server.initialize_object_spy(names_file)
    else:
        logger.warning(f"⚠️ names.py not found at {names_file}")
    
    # Agent 2: Test Generator
    server.initialize_test_generator()

    # Agent 3: Executor
    server.initialize_executor()

    # Agent 4: Intelligent Test Generator (Orchestrator)
    server.initialize_intelligent_test_generator()
    
    # Print Status
    logger.info("\n📊 Server Status:")
    status = server.get_status()
    logger.info(json.dumps(status, indent=2))
    
    logger.info("\n✅ Server ready!")
    logger.info("=" * 60)
    
    return server

if __name__ == "__main__":
    server = main()
    
    # Example: Start the full workflow
    # Uncomment to test:
    # result = server.run_full_test_workflow()
    # print(json.dumps(result, indent=2))
