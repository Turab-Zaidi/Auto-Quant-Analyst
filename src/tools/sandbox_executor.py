import os
import subprocess
import tempfile
from src.utils.logger import get_logger

logger = get_logger(__name__)

def execute_code_in_sandbox(code_string: str, timeout_seconds: int = 30) -> dict:
    """
    Executes Python code in an isolated Docker container.
    Returns the success status, stdout, stderr, and exit code.
    """
    # 1. Setup absolute paths for Docker volume mounting
    project_root = os.path.abspath(os.getcwd())
    charts_dir = os.path.join(project_root, "charts")
    os.makedirs(charts_dir, exist_ok=True)
    
    # 2. Write the LLM's code to a temporary file locally
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_script:
        temp_script.write(code_string)
        script_path = temp_script.name
        
    try:
        logger.info("Spinning up Docker sandbox...")
        
        # 3. Build the highly restricted Docker command
        cmd = [
            "docker", "run", "--rm",                 # --rm deletes container after exit
            "--network", "none",                     # NO internet access
            "--memory", "512m",                      # Limit RAM to prevent bombs
            "--cpus", "1.0",                         # Limit CPU
            "-v", f"{charts_dir}:/charts",           # Mount the output folder
            "-v", f"{script_path}:/code/script.py",  # Mount the script
            "auto-quant-sandbox",                    # The Docker image name
            "python", "/code/script.py"              # The command to run
        ]
        
        # 4. Execute with strict timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        
        success = result.returncode == 0
        if success:
            logger.info("Sandbox execution completed successfully.")
        else:
            logger.warning(f"Sandbox execution failed with code {result.returncode}. Error: {result.stderr}")
            
        return {
            "success": success,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
    except subprocess.TimeoutExpired:
        logger.error(f"Sandbox execution timed out after {timeout_seconds} seconds.")
        return {
            "success": False,
            "exit_code": 124,
            "stdout": "",
            "stderr": "Execution timed out. Infinite loop or heavy process detected."
        }
    except Exception as e:
        logger.error(f"Sandbox orchestration failed: {str(e)}")
        return {
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Host error orchestrating Docker: {str(e)}"
        }
    finally:
        if os.path.exists(script_path):
            os.remove(script_path)