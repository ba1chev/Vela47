from typing import Any
from pydantic import ValidationError
from fastapi import APIRouter, HTTPException, Request

from app.server.routes import authorize
from app.server.requests import CreateEntityRequest
from app.server.security import IdentityAccessAction
from app.server.security import format_entity_type_vrn

iam_router = APIRouter(prefix = "/api/iam")


@iam_router.post("/entities", status_code = 201)
def create_entity(body: CreateEntityRequest, request: Request) -> dict[str, Any]:
    authorize(request, IdentityAccessAction.IAM_CREATE_ENTITY, format_entity_type_vrn(body.type))

    try:
        entity = request.app.state.identity_access_service.create_entity(
            body.type, body.name, body.password
        )
    except ValidationError as error:
        raise HTTPException(
            status_code = 400,
            detail = "; ".join(current_error["msg"] for current_error in error.errors())
        ) from None
    except ValueError as error:
        raise HTTPException(status_code = 400, detail = str(error)) from None

    return {"id": entity.id, "type": entity.type.value, "name": entity.name}
