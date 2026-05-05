@echo off
title AlphaChart MCP Server
color 0B

echo.
echo  =============================================
echo   AlphaChart v3.4 -- MCP Server for OpenCode
echo  =============================================
echo.
echo  This window must stay open while using OpenCode.
echo  The server communicates via stdio (managed by OpenCode).
echo.
echo  To test manually, run:
echo    python alphachart_mcp_server.py
echo.
echo  For OpenCode, copy opencode_mcp_config.json content
echo  into your OpenCode config file (~/.config/opencode/config.json)
echo.

cd /d "%~dp0"

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found in PATH.
    pause
    exit /b 1
)

python -c "import sys; print(f'  Python {sys.version.split()[0]} ready')"
echo  Docs directory: %~dp0
echo.
echo  MCP server ready. OpenCode will launch it automatically.
echo  Press any key to run a quick self-test...
pause >nul

echo.
echo  Running self-test...
echo {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test"}}} | python alphachart_mcp_server.py 2>nul | python -c "import sys,json; d=json.loads(sys.stdin.readline()); print('  [OK] Server responds:', d['result']['serverInfo'])"
echo {"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_docs","arguments":{}}} | python alphachart_mcp_server.py 2>nul | python -c "import sys,json; d=json.loads(sys.stdin.readline()); txt=d['result']['content'][0]['text']; found=txt.count('[?]'); print(f'  [OK] Docs loaded. Missing: {found}')"
echo.
echo  Self-test complete.
pause
