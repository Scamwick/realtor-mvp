#!/usr/bin/env python3
"""
CLI Wrapper Proxy for ClawWork
Routes OpenAI API calls to subscription CLIs (Claude, Gemini, Kimi, Codex)
"""

import subprocess
import json
import os
import sys
from typing import Optional, Dict, Any
from datetime import datetime

class CLIWrapperProxy:
    """Proxy OpenAI API calls to subscription CLI tools."""

    def __init__(self):
        self.cli_wrapper_path = os.path.expanduser("~/.openclaw/bot/src/tools/cli-wrapper.js")
        self.node_path = self._find_node()
        self.call_count = 0

    def _find_node(self) -> str:
        """Find node executable."""
        result = subprocess.run(['which', 'node'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return '/usr/local/bin/node'

    def _run_cli_wrapper(self, prompt: str, model: str = "claude") -> Dict[str, Any]:
        """
        Call the Node CLI wrapper with automatic fallback.
        Tries: claude → gemini → kimi → codex
        """
        try:
            # Build Node code to load and call the wrapper
            node_code = f"""
const wrapper = require('./cli-wrapper.js');
const prompt = {json.dumps(prompt)};

wrapper.callWithFallback(['claude', 'gemini', 'kimi', 'codex'], prompt)
  .then(result => {{
    const response = {{
      ok: result.ok,
      text: result.text || null,
      error: result.ok ? null : (result.errors || 'Unknown error'),
      usage: {{
        prompt_tokens: Math.ceil(prompt.length / 4),
        completion_tokens: result.text ? Math.ceil(result.text.length / 4) : 0,
        total_tokens: Math.ceil((prompt.length + (result.text || '').length) / 4)
      }}
    }};
    console.log(JSON.stringify(response));
  }})
  .catch(err => {{
    console.log(JSON.stringify({{
      ok: false,
      text: null,
      error: err.message,
      usage: {{
        prompt_tokens: Math.ceil(prompt.length / 4),
        completion_tokens: 0,
        total_tokens: Math.ceil(prompt.length / 4)
      }}
    }}));
  }});
"""

            # Execute via Node in the ClawWork directory
            cwd = os.path.dirname(os.path.abspath(__file__))
            result = subprocess.run(
                [self.node_path, '-e', node_code],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=cwd,
                env=self._clean_env()
            )

            if result.returncode == 0:
                try:
                    response = json.loads(result.stdout.strip())
                    return response
                except json.JSONDecodeError:
                    return {
                        'ok': False,
                        'text': None,
                        'error': f'Failed to parse response: {result.stdout}',
                        'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
                    }
            else:
                return {
                    'ok': False,
                    'text': None,
                    'error': result.stderr or 'CLI wrapper execution failed',
                    'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
                }

        except subprocess.TimeoutExpired:
            return {
                'ok': False,
                'text': None,
                'error': 'CLI wrapper timeout (300s)',
                'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
            }
        except Exception as e:
            return {
                'ok': False,
                'text': None,
                'error': str(e),
                'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
            }

    @staticmethod
    def _clean_env() -> Dict[str, str]:
        """Remove CLAUDECODE vars to prevent nested session errors."""
        env = os.environ.copy()
        for key in list(env.keys()):
            if 'CLAUDECODE' in key or 'CLAUDE_CODE' in key:
                del env[key]
        return env

    def create_completion(self,
                         messages: list,
                         model: str = "claude",
                         temperature: float = 0.7,
                         max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Convert OpenAI completion request to CLI wrapper call.
        Returns response in OpenAI API format.
        """
        self.call_count += 1

        # Format messages as prompt
        prompt = self._format_messages(messages)

        # Call CLI wrapper
        cli_response = self._run_cli_wrapper(prompt, model)

        # Convert to OpenAI format
        return {
            'id': f'clawwork-{self.call_count}',
            'object': 'text_completion',
            'created': int(datetime.now().timestamp()),
            'model': model,
            'choices': [
                {
                    'text': cli_response['text'] if cli_response['ok'] else f"Error: {cli_response['error']}",
                    'index': 0,
                    'logprobs': None,
                    'finish_reason': 'stop' if cli_response['ok'] else 'error'
                }
            ],
            'usage': cli_response.get('usage', {
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0
            })
        }

    def create_chat_completion(self,
                               messages: list,
                               model: str = "claude",
                               temperature: float = 0.7,
                               max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Convert OpenAI chat completion request to CLI wrapper call.
        Returns response in OpenAI chat format.
        """
        self.call_count += 1

        # Format messages as prompt
        prompt = self._format_messages(messages)

        # Call CLI wrapper
        cli_response = self._run_cli_wrapper(prompt, model)

        # Convert to OpenAI chat format
        return {
            'id': f'chatcmpl-{self.call_count}',
            'object': 'chat.completion',
            'created': int(datetime.now().timestamp()),
            'model': model,
            'choices': [
                {
                    'index': 0,
                    'message': {
                        'role': 'assistant',
                        'content': cli_response['text'] if cli_response['ok'] else f"Error: {cli_response['error']}"
                    },
                    'finish_reason': 'stop' if cli_response['ok'] else 'error'
                }
            ],
            'usage': cli_response.get('usage', {
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0
            })
        }

    @staticmethod
    def _format_messages(messages: list) -> str:
        """Convert message list to prompt string."""
        lines = []
        for msg in messages:
            role = msg.get('role', 'user').upper()
            content = msg.get('content', '')
            lines.append(f"{role}:\n{content}\n")
        return "\n".join(lines)


# FastAPI server for OpenAI API compatibility
if __name__ == '__main__':
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    import uvicorn

    app = FastAPI(title="ClawWork CLI Wrapper Proxy")
    proxy = CLIWrapperProxy()

    @app.post("/v1/completions")
    async def completions(request: dict):
        """OpenAI completions endpoint"""
        try:
            print(f"[PROXY] POST /v1/completions: {request}")
            response = proxy.create_completion(
                messages=request.get('prompt', []),
                model=request.get('model', 'claude'),
                temperature=request.get('temperature', 0.7),
                max_tokens=request.get('max_tokens')
            )
            print(f"[PROXY] Response: {response}")
            return response
        except Exception as e:
            print(f"[PROXY] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/v1/chat/completions")
    async def chat_completions(request: dict):
        """OpenAI chat completions endpoint"""
        try:
            print(f"[PROXY] POST /v1/chat/completions: {request}")
            response = proxy.create_chat_completion(
                messages=request.get('messages', []),
                model=request.get('model', 'claude'),
                temperature=request.get('temperature', 0.7),
                max_tokens=request.get('max_tokens')
            )
            print(f"[PROXY] Response OK: {response['id']}")
            return response
        except Exception as e:
            print(f"[PROXY] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/health")
    async def health():
        """Health check endpoint"""
        return {"status": "healthy", "calls": proxy.call_count}

    print(f"🦞 ClawWork CLI Wrapper Proxy starting...")
    print(f"   API endpoint: http://localhost:8001")
    print(f"   Chat completions: POST /v1/chat/completions")
    print(f"   Health check: GET /health")
    print(f"")

    uvicorn.run(app, host="0.0.0.0", port=8001)
