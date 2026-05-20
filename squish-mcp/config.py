# config.py
import os
from pathlib import Path

# ============================================
# SQUISH 8.0.0 CONFIGURATION (Windows EC2)
# ============================================

CONFIG = {
    # Squish Installation
    'SQUISH_BIN': r'C:\Users\Administrator\Squish for Qt 8.0.0\bin',
    
    # Test Suite Paths
    'TEST_SUITE': r'C:\Projekte\Suite_TestEnvironment\suite_Suite_Testautomation\suite_Suite_Testautomation',
    'TEST_FILES_DIR': r'C:\Projekte\Suite_TestEnvironment\Testfiles',
    
    # Results & Logging
    'RESULTS_DIR': r'C:\Projekte\Suite_TestEnvironment\TestResults',
    'LOG_DIR': r'C:\Projekte\Suite_TestEnvironment\Logs',
    
    # Squish Server Settings
    'SQUISH_HOST': '127.0.0.1',
    'SQUISH_PORT': 4322,
    'AUT_NAME': 'suite-app',
    
    # Qt OpenGL Settings (für deine App)
    'QT_OPENGL': 'angle',
    'QT_ANGLE_PLATFORM': 'd3d11',
    
    # MCP Server Settings
    'MCP_HOST': 'localhost',
    'MCP_PORT': 8000,
    
    # Azure DevOps (optional, für später)
    'AZURE_DEVOPS_ORG': 'your-org',
    'AZURE_DEVOPS_PROJECT': 'your-project',
    'AZURE_DEVOPS_TOKEN': 'your-token',
    
    # Logging
    'LOG_LEVEL': 'INFO',
    'DEBUG_MODE': True
}

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_config():
    """Returns the configuration dictionary"""
    return CONFIG

def setup_directories():
    """Creates necessary directories if they don't exist"""
    dirs = [
        CONFIG['RESULTS_DIR'],
        CONFIG['LOG_DIR'],
        CONFIG['TEST_FILES_DIR']
    ]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Directory ready: {dir_path}")

def validate_config():
    """Validates that all paths exist"""
    required_paths = {
        'SQUISH_BIN': 'Squish Binary Directory',
        'TEST_SUITE': 'Test Suite Directory',
        'TEST_FILES_DIR': 'Test Files Directory'
    }
    
    print("\n🔍 Validating Configuration...")
    for key, description in required_paths.items():
        path = CONFIG[key]
        if os.path.exists(path):
            print(f"✅ {description}: {path}")
        else:
            print(f"❌ {description} NOT FOUND: {path}")
            return False
    
    return True

# ============================================
# ENVIRONMENT VARIABLES FOR SQUISH
# ============================================

def apply_environment():
    """Sets environment variables needed for Squish"""
    os.environ['QT_OPENGL'] = CONFIG['QT_OPENGL']
    os.environ['QT_ANGLE_PLATFORM'] = CONFIG['QT_ANGLE_PLATFORM']
    print(f"🔧 Environment Variables Set:")
    print(f"   QT_OPENGL={CONFIG['QT_OPENGL']}")
    print(f"   QT_ANGLE_PLATFORM={CONFIG['QT_ANGLE_PLATFORM']}")

# ============================================
# INITIALIZATION
# ============================================

if __name__ == "__main__":
    print("🚀 Squish MCP Server Configuration")
    print("=" * 50)
    setup_directories()
    apply_environment()
    if validate_config():
        print("\n✅ Configuration is VALID!")
    else:
        print("\n❌ Configuration has ERRORS!")
