from fastapi import APIRouter, Depends
from src.common.utils.response import Response, Status
from src.module.agent.agent_dependency import get_agent_service
from src.module.agent.agent_schema import (
    AgentListItem,
    AgentResponse,
    CreateAgentRequest,
    UpdateAgentRequest,
)
from src.module.agent.agent_service import AgentService

router = APIRouter(prefix="/agent", tags=["agents"])


@router.post("/create", response_model=AgentResponse)
async def create_agent(
    request: CreateAgentRequest,
    agent_service: AgentService = Depends(get_agent_service),
):
    try:
        result = await agent_service.create_agent(
            username=request.username,
            name=request.name,
            bio=request.bio,
            type=request.type,
        )
        return Response.success(
            message="Agent created successfully",
            data=result,
            status_code=Status.CREATED,
        )
    except ValueError as e:
        error_message = str(e)
        status_code = (
            Status.CONFLICT
            if "username" in error_message.lower()
            and "already exists" in error_message.lower()
            else Status.BAD_REQUEST
        )
        return Response.error(
            message=error_message,
            status_code=status_code,
        )
    except Exception as e:
        return Response.error(
            message=f"Failed to create agent: {str(e)}",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.get("", response_model=list[AgentListItem])
async def get_all_agents(
    agent_service: AgentService = Depends(get_agent_service),
):
    try:
        result = await agent_service.get_all_agents()
        return Response.success(
            message="Agents retrieved successfully",
            data=result,
        )
    except Exception as e:
        return Response.error(
            message=f"Failed to retrieve agents: {str(e)}",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    agent_service: AgentService = Depends(get_agent_service),
):
    try:
        result = await agent_service.get_agent_by_id(agent_id=agent_id)
        return Response.success(
            message="Agent retrieved successfully",
            data=result,
        )
    except ValueError as e:
        return Response.error(
            message=str(e),
            status_code=Status.NOT_FOUND,
        )
    except Exception as e:
        return Response.error(
            message=f"Failed to retrieve agent: {str(e)}",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    request: UpdateAgentRequest,
    agent_service: AgentService = Depends(get_agent_service),
):
    try:
        result = await agent_service.update_agent(
            agent_id=agent_id,
            username=request.username,
            name=request.name,
            bio=request.bio,
            type=request.type,
        )
        return Response.success(
            message="Agent updated successfully",
            data=result,
        )
    except ValueError as e:
        error_message = str(e)
        status_code = (
            Status.CONFLICT
            if "username" in error_message.lower()
            and "already exists" in error_message.lower()
            else Status.BAD_REQUEST
        )
        return Response.error(
            message=error_message,
            status_code=status_code,
        )
    except Exception as e:
        return Response.error(
            message=f"Failed to update agent: {str(e)}",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    agent_service: AgentService = Depends(get_agent_service),
):
    try:
        await agent_service.delete_agent(agent_id=agent_id)
        return Response.success(
            message="Agent deleted successfully",
            status_code=Status.NO_CONTENT,
        )
    except ValueError as e:
        return Response.error(
            message=str(e),
            status_code=Status.NOT_FOUND,
        )
    except Exception as e:
        return Response.error(
            message=f"Failed to delete agent: {str(e)}",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.delete("")
async def delete_all_agents(
    agent_service: AgentService = Depends(get_agent_service),
):
    try:
        count = await agent_service.delete_all_agents()
        return Response.success(
            message=f"Deleted {count} agents successfully",
            data={"deleted_count": count},
            status_code=Status.OK,
        )
    except Exception as e:
        return Response.error(
            message=f"Failed to delete agents: {str(e)}",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )
