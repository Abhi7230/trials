"""Stdio JSON-RPC client for MCP servers."""

import json
import subprocess
import time
from typing import Any, Optional
from .models import JsonRpcRequest, JsonRpcResponse


class McpClient:
    """Minimal stdio JSON-RPC 2.0 client for MCP servers."""
    
    def __init__(self, cmd: str, timeout: float = 5.0):
        self.cmd = cmd
        self.timeout = timeout
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0
        self.stderr_lines: list[str] = []
        self.stdout_noise: list[str] = []
        
    def start(self) -> None:
        """Launch the server subprocess."""
        self.process = subprocess.Popen(
            self.cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
    def send_request(self, method: str, params: Optional[dict[str, Any]] = None) -> JsonRpcResponse:
        """Send a JSON-RPC request and wait for response."""
        if not self.process:
            raise RuntimeError("Server not started")
            
        self.request_id += 1
        request = JsonRpcRequest(
            id=self.request_id,
            method=method,
            params=params or {}
        )
        
        request_line = request.model_dump_json() + "\n"
        
        try:
            self.process.stdin.write(request_line)
            self.process.stdin.flush()
        except BrokenPipeError:
            raise RuntimeError("Server process terminated unexpectedly")
        
        start_time = time.time()
        response_line = None
        
        while time.time() - start_time < self.timeout:
            if self.process.poll() is not None:
                raise RuntimeError("Server process exited")
                
            try:
                line = self.process.stdout.readline()
                if not line:
                    time.sleep(0.01)
                    continue
                    
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    data = json.loads(line)
                    if "jsonrpc" in data:
                        response_line = line
                        break
                    else:
                        self.stdout_noise.append(line)
                except json.JSONDecodeError:
                    self.stdout_noise.append(line)
                    
            except Exception:
                time.sleep(0.01)
                continue
        
        if response_line is None:
            raise TimeoutError(f"Request timed out after {self.timeout}s")
            
        response_data = json.loads(response_line)
        return JsonRpcResponse(**response_data)
    
    def send_notification(self, method: str, params: Optional[dict[str, Any]] = None) -> None:
        """Send a JSON-RPC notification (no response expected)."""
        if not self.process:
            raise RuntimeError("Server not started")
            
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        
        notification_line = json.dumps(notification) + "\n"
        
        try:
            self.process.stdin.write(notification_line)
            self.process.stdin.flush()
        except BrokenPipeError:
            raise RuntimeError("Server process terminated unexpectedly")
    
    def is_alive(self) -> bool:
        """Check if server process is still running."""
        if not self.process:
            return False
        return self.process.poll() is None
    
    def stop(self) -> None:
        """Stop the server subprocess."""
        if not self.process:
            return
            
        try:
            try:
                self.process.stdin.close()
            except (BrokenPipeError, OSError):
                pass
            
            self.process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        
        if self.process.stderr:
            try:
                stderr_text = self.process.stderr.read()
                if stderr_text:
                    self.stderr_lines = stderr_text.strip().split("\n")
            except Exception:
                pass
        
        self.process = None
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False
