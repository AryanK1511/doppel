from fastapi import APIRouter, Depends
from src.common.utils.response import Response, Status
from src.module.world.world_dependency import get_world_service
from src.module.world.world_schema import (
    RemoveAgentRequest,
    SpawnAgentRequest,
    WorldState,
)
from src.module.world.world_service import WorldService

router = APIRouter(prefix="/world", tags=["world"])


@router.post("/start")
async def start_world(
    world_service: WorldService = Depends(get_world_service),
):
    try:
        world_service.start()
        return Response.success(
            message="World simulation started",
            data={"status": "running"},
        )
    except Exception as e:
        return Response.error(
            message=f"Failed to start world: {str(e)}",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.post("/stop")
async def stop_world(
    world_service: WorldService = Depends(get_world_service),
):
    try:
        world_service.stop()
        return Response.success(
            message="World simulation stopped",
            data={"status": "stopped"},
        )
    except Exception as e:
        return Response.error(
            message=f"Failed to stop world: {str(e)}",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.post("/spawn")
async def spawn_agent(
    request: SpawnAgentRequest,
    world_service: WorldService = Depends(get_world_service),
):
    try:
        agent_state = await world_service.spawn_agent(
            agent_id=request.agent_id,
            x=request.x,
            y=request.y,
        )
        return Response.success(
            message="Agent spawned successfully",
            data={
                "agent_id": agent_state.agent_id,
                "name": agent_state.name,
                "agent_type": agent_state.agent_type,
                "x": agent_state.x,
                "y": agent_state.y,
                "state": agent_state.state,
            },
            status_code=Status.CREATED,
        )
    except ValueError as e:
        return Response.error(
            message=str(e),
            status_code=Status.BAD_REQUEST,
        )
    except Exception as e:
        return Response.error(
            message=f"Failed to spawn agent: {str(e)}",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.post("/remove")
async def remove_agent(
    request: RemoveAgentRequest,
    world_service: WorldService = Depends(get_world_service),
):
    try:
        removed = world_service.remove_agent(request.agent_id)
        if removed:
            return Response.success(
                message="Agent removed successfully",
            )
        else:
            return Response.error(
                message=f"Agent {request.agent_id} not found in world",
                status_code=Status.NOT_FOUND,
            )
    except Exception as e:
        return Response.error(
            message=f"Failed to remove agent: {str(e)}",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.get("/state", response_model=WorldState)
async def get_world_state(
    world_service: WorldService = Depends(get_world_service),
):
    try:
        state = world_service.get_world_state()
        return Response.success(
            message="World state retrieved",
            data=state,
        )
    except Exception as e:
        return Response.error(
            message=f"Failed to get world state: {str(e)}",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )
