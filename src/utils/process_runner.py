# app/utils/process_runner.py
import subprocess
import logging
import time
import os
from typing import List, Dict, Optional, Callable, Any

logger = logging.getLogger("tamu_newsletter")

class ProcessRunner:
    """
    Utility class for running external processes with real-time output capture
    """
    
    @staticmethod
    def run_process(
        cmd: List[str], 
        output_callback: Optional[Callable[[str], Any]] = None,
        env: Optional[Dict[str, str]] = None
    ) -> tuple:
        """
        Run a subprocess with real-time output handling
        
        Args:
            cmd: Command to run as a list of strings
            output_callback: Optional callback function that will be called with each line of output
            env: Optional environment variables dictionary
            
        Returns:
            Tuple of (return_code, stdout_output, stderr_output)
        """
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Use current environment if not provided
        if env is None:
            env = dict(os.environ)
        
        # Collected output
        stdout_output = ""
        stderr_output = ""
        
        try:
            # Create process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=env
            )
            
            # Process output in real-time
            while True:
                # Read stdout line by line
                stdout_line = process.stdout.readline()
                if stdout_line:
                    stdout_output += stdout_line
                    logger.info(f"Process stdout: {stdout_line.strip()}")
                    if output_callback:
                        output_callback(stdout_line)
                
                # Read stderr line by line
                stderr_line = process.stderr.readline()
                if stderr_line:
                    stderr_output += stderr_line
                    logger.error(f"Process stderr: {stderr_line.strip()}")
                    if output_callback:
                        output_callback(f"ERROR: {stderr_line}")
                
                # Check if process has finished
                if process.poll() is not None:
                    # Get any remaining output
                    remaining_stdout, remaining_stderr = process.communicate()
                    if remaining_stdout:
                        stdout_output += remaining_stdout
                        logger.info(f"Process remaining stdout: {remaining_stdout.strip()}")
                        if output_callback:
                            output_callback(remaining_stdout)
                    if remaining_stderr:
                        stderr_output += remaining_stderr
                        logger.error(f"Process remaining stderr: {remaining_stderr.strip()}")
                        if output_callback:
                            output_callback(f"ERROR: {remaining_stderr}")
                    break
                
                time.sleep(0.1)  # Prevent CPU overuse
            
            return_code = process.returncode
            logger.info(f"Process completed with return code: {return_code}")
            
            return (return_code, stdout_output, stderr_output)
            
        except Exception as e:
            logger.error(f"Error running process: {str(e)}")
            return (1, stdout_output, f"Error running process: {str(e)}")