"""Test endpoint for Claude Code integration."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.deps import get_orchestrator
from app.services.dagger_module_service import DaggerModuleService

settings = get_settings()
router = APIRouter()


class TestClaudeCodeRequest(BaseModel):
    """Request for testing Claude Code."""
    repo_url: str = "https://github.com/fastapi/fastapi"
    prompt: str = "Add docstrings to the main.py file"


class TestClaudeCodeResponse(BaseModel):
    """Response from Claude Code test."""
    status: str
    output: str


@router.post(
    "/test-claude-code",
    response_model=TestClaudeCodeResponse,
    summary="Test Claude Code integration",
)
async def test_claude_code(
    request: TestClaudeCodeRequest,
    dagger_service: DaggerModuleService = Depends(lambda: DaggerModuleService()),
) -> TestClaudeCodeResponse:
    """Test Claude Code integration with Dagger."""
    
    if not dagger_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Dagger CLI is not available"
        )
    
    try:
        # Run Claude Code and collect output
        output_lines = []
        async for line in dagger_service.stream_agent_output(
            repo_url=request.repo_url,
            prompt=request.prompt,
            variation_id=0,
            use_claude_code=True,
        ):
            output_lines.append(line)
        
        return TestClaudeCodeResponse(
            status="success",
            output="\n".join(output_lines)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Claude Code execution failed: {str(e)}"
        )