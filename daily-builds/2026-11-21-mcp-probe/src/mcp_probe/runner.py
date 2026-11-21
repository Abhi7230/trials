"""Main test runner for MCP probe."""

import time
import statistics
from typing import Any, Optional
from .client import McpClient
from .models import Finding, Report, ToolInfo, InitializeResult
from .rules import check_handshake, check_tool_schemas, check_results, check_robustness
from .fuzz import FuzzGenerator


class ProbeRunner:
    """Execute probe tests against an MCP server."""
    
    def __init__(
        self,
        cmd: str,
        timeout: float = 5.0,
        seed: int = 1,
        fuzz_per_tool: int = 8,
    ):
        self.cmd = cmd
        self.timeout = timeout
        self.seed = seed
        self.fuzz_per_tool = fuzz_per_tool
        self.findings: list[Finding] = []
        self.latencies: list[float] = []
        self.timeout_count = 0
        self.crash_count = 0
        
    def run(self) -> Report:
        """Run the full probe suite."""
        with McpClient(self.cmd, self.timeout) as client:
            server_info = self._check_handshake(client)
            
            tools = self._get_tools(client)
            
            if tools:
                self._check_tool_list(tools)
                self._fuzz_tools(client, tools)
            
            self._check_robustness(client)
            
            from .scoring import calculate_score
            score, grade = calculate_score(self.findings)
            
            return Report(
                findings=self.findings,
                score=score,
                grade=grade,
                stats={
                    "tool_count": len(tools),
                    "test_count": len(self.latencies),
                    "timeout_count": self.timeout_count,
                    "crash_count": self.crash_count,
                    "latency_p50": statistics.median(self.latencies) if self.latencies else 0.0,
                    "latency_p95": statistics.quantiles(self.latencies, n=20)[18] if len(self.latencies) > 1 else 0.0,
                },
                server_info=server_info,
            )
    
    def _check_handshake(self, client: McpClient) -> Optional[dict[str, Any]]:
        """Perform handshake checks."""
        try:
            start = time.time()
            init_resp = client.send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcp-probe", "version": "0.1.0"}
            })
            self.latencies.append(time.time() - start)
            init_request_id = client.request_id
        except Exception as e:
            self.findings.append(Finding(
                rule_id="HS000",
                severity="error",
                message=f"initialize failed: {e}"
            ))
            return None
        
        try:
            client.send_notification("notifications/initialized")
        except Exception:
            pass
        
        try:
            start = time.time()
            unknown_resp = client.send_request("unknown_method_xyz", {})
            self.latencies.append(time.time() - start)
        except Exception as e:
            unknown_resp = None
            self.findings.append(Finding(
                rule_id="HS000",
                severity="error",
                message=f"unknown method check failed: {e}"
            ))
        
        malformed_ok = True
        try:
            client.process.stdin.write("{{{{invalid json\n")
            client.process.stdin.flush()
            time.sleep(0.1)
            if not client.is_alive():
                malformed_ok = False
        except Exception:
            malformed_ok = False
        
        try:
            start = time.time()
            ping_resp = client.send_request("ping", {})
            self.latencies.append(time.time() - start)
            ping_request_id = client.request_id
        except Exception as e:
            ping_resp = None
            ping_request_id = 0
            self.findings.append(Finding(
                rule_id="HS000",
                severity="warning",
                message=f"ping failed: {e}"
            ))
        
        if unknown_resp and ping_resp:
            handshake_findings = check_handshake(
                init_resp,
                init_request_id,
                unknown_resp,
                malformed_ok,
                ping_resp,
                ping_request_id,
            )
            self.findings.extend(handshake_findings)
        
        if init_resp.result:
            return init_resp.result
        return None
    
    def _get_tools(self, client: McpClient) -> list[ToolInfo]:
        """Retrieve tools list with pagination support."""
        tools = []
        cursor = None
        
        while True:
            try:
                params = {}
                if cursor:
                    params["cursor"] = cursor
                
                start = time.time()
                resp = client.send_request("tools/list", params)
                self.latencies.append(time.time() - start)
                
                if resp.error:
                    break
                
                if resp.result and "tools" in resp.result:
                    for tool_data in resp.result["tools"]:
                        tools.append(ToolInfo(**tool_data))
                    
                    cursor = resp.result.get("nextCursor")
                    if not cursor:
                        break
                else:
                    break
                    
            except Exception:
                break
        
        return tools
    
    def _check_tool_list(self, tools: list[ToolInfo]) -> None:
        """Check tool schemas."""
        schema_findings = check_tool_schemas(tools)
        self.findings.extend(schema_findings)
    
    def _fuzz_tools(self, client: McpClient, tools: list[ToolInfo]) -> None:
        """Fuzz test each tool."""
        fuzzer = FuzzGenerator(self.seed)
        
        for tool in tools[:5]:
            valid_inputs = fuzzer.generate_valid(tool.inputSchema, self.fuzz_per_tool // 2)
            invalid_inputs = fuzzer.generate_invalid(tool.inputSchema, self.fuzz_per_tool // 2)
            
            for inputs in valid_inputs:
                self._call_tool(client, tool.name, inputs, expect_error=False)
            
            for inputs in invalid_inputs:
                self._call_tool(client, tool.name, inputs, expect_error=True)
    
    def _call_tool(
        self,
        client: McpClient,
        tool_name: str,
        arguments: dict[str, Any],
        expect_error: bool,
    ) -> None:
        """Call a tool and check the result."""
        try:
            start = time.time()
            resp = client.send_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })
            self.latencies.append(time.time() - start)
            
            if resp.error:
                if not expect_error:
                    pass
            elif resp.result:
                result_findings = check_results(tool_name, resp.result)
                self.findings.extend(result_findings)
                
                if expect_error and not resp.result.get("isError"):
                    self.findings.append(Finding(
                        rule_id="FZ001",
                        severity="warning",
                        message=f"tool '{tool_name}' accepted invalid input",
                        location=tool_name
                    ))
                    
        except TimeoutError:
            self.timeout_count += 1
            self.findings.append(Finding(
                rule_id="FZ002",
                severity="error",
                message=f"tool '{tool_name}' timed out",
                location=tool_name
            ))
        except Exception as e:
            self.crash_count += 1
            self.findings.append(Finding(
                rule_id="FZ003",
                severity="error",
                message=f"tool '{tool_name}' caused error: {e}",
                location=tool_name
            ))
    
    def _check_robustness(self, client: McpClient) -> None:
        """Check server robustness after testing."""
        latency_p50 = statistics.median(self.latencies) if self.latencies else 0.0
        latency_p95 = statistics.quantiles(self.latencies, n=20)[18] if len(self.latencies) > 20 else (max(self.latencies) if self.latencies else 0.0)
        
        robustness_findings = check_robustness(
            client.is_alive(),
            client.stdout_noise,
            latency_p50,
            latency_p95,
            self.timeout_count,
            self.crash_count,
        )
        self.findings.extend(robustness_findings)
