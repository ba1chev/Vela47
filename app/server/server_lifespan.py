import asyncio
import logging
import secrets
from fastapi import FastAPI
from typing import AsyncIterator
from contextlib import asynccontextmanager

from app.server.config import Config
from app.intelligence.web import WebFetcher
from app.server.builders import build_database
from app.server.builders import install_security
from app.server.builders import build_web_search
from app.server.builders import build_rag_indexer
from app.server.builders import build_model_client
from app.server.builders import build_sandbox_pool
from app.server.knowledge import KnowledgeStoreSql
from app.server.security import IdentityEntityType
from app.server.security import IdentityAccessService
from app.server.security import IdentityAccessStoreSql
from app.server.chat_sessions import ChatSessionStoreSql
from app.server.security import AuthenticationPasswordHasher

SANDBOX_POOL_SIZE = 10

logger = logging.getLogger("vela47")


def _token_secret(config: Config) -> str:
    if config.token_secret is not None:
        return config.token_secret.get_secret_value()

    logger.warning(
        "VELA47_TOKEN_SECRET is not set — generating a signing key for this run, so every "
        "session ends when the server restarts."
    )
    return secrets.token_urlsafe(48)


def _bootstrap_admin(identity_access_service: IdentityAccessService, config: Config) -> None:
    if config.admin_username is None or config.admin_password is None:
        logger.warning(
            "No admin credentials are configured, so no admin is bootstrapped on this start."
        )
        return

    if identity_access_service.find_entity(config.admin_username) is not None:
        return

    try:
        identity_access_service.create_entity(
            IdentityEntityType.ADMIN,
            config.admin_username,
            config.admin_password.get_secret_value()
        )
    except ValueError:
        if identity_access_service.find_entity(config.admin_username) is None:
            raise
        logger.warning(
            "Admin '%s' was created by another server starting at the same time.",
            config.admin_username.strip().lower()
        )
        return
    logger.info("Admin '%s' created from the configuration.", config.admin_username.strip().lower())


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    config = await asyncio.to_thread(Config.from_environment)
    app.state.config = config

    database = build_database(config)
    await asyncio.to_thread(database.start)
    app.state.database = database
    app.state.chat_session_store = ChatSessionStoreSql(database)
    app.state.knowledge_store = KnowledgeStoreSql(database)
    app.state.model_client = build_model_client(config)
    app.state.rag_indexer = build_rag_indexer(config.platform, app.state.model_client)
    app.state.web_fetcher = WebFetcher()
    app.state.web_search = build_web_search(config, app.state.web_fetcher)
    logger.info(
        "Database ready: %s in %s, release %s",
        database.database_type.value, config.environment.value, config.version or "unversioned"
    )
    logger.info("Web search: %s", type(app.state.web_search).__name__)

    install_security(
        app.state, IdentityAccessStoreSql(database), AuthenticationPasswordHasher(), _token_secret(config)
    )
    _bootstrap_admin(app.state.identity_access_service, config)

    pool = build_sandbox_pool(config, SANDBOX_POOL_SIZE)
    await asyncio.to_thread(pool.start)
    app.state.sandbox_pool = pool
    logger.info("Sandbox ready: %s slots in %s", pool.available, type(pool).__name__)

    try:
        yield
    finally:
        await asyncio.to_thread(pool.shutdown)
        logger.info("Sandbox torn down.")
        await asyncio.to_thread(database.shutdown)
        logger.info("Database closed.")
