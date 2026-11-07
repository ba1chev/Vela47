import pytest

from app.server.security import SecurityContext
from app.server.security import SecurityPipeline
from app.server.security import AuthorizationError
from app.server.security import SecurityServiceType
from app.server.security import AuthenticationError
from app.server.security import AuthorizationService
from app.server.security import IdentityAccessAction
from app.server.security import AuthorizationDecision
from app.server.security import AuthenticationService
from app.server.security import IdentityAccessService
from app.server.security import AuthenticationTokenCodec
from app.server.security import IdentityAccessStoreInMemory
from app.server.security import AuthenticationPasswordHasher
from tests.fixtures.security.recording_security_service import RecordingSecurityService

AUTHENTICATION = SecurityServiceType.AUTHENTICATION
AUTHORIZATION = SecurityServiceType.AUTHORIZATION


def make_context(token = None):
    return SecurityContext(
        token = token, action = IdentityAccessAction.AGENT_RUN, resource = "vrn:agent::deep-agent"
    )


class TestSecurityPipeline:
    def test_services_run_in_the_order_given(self):
        log = []
        SecurityPipeline([
            RecordingSecurityService(AUTHENTICATION, log, "first"),
            RecordingSecurityService(AUTHORIZATION, log, "second", AuthorizationDecision.ALLOW)
        ]).run(make_context())
        assert log == ["first", "second"]

    def test_an_allowed_run_returns_the_same_context(self):
        context = make_context()
        pipeline = SecurityPipeline([
            RecordingSecurityService(AUTHORIZATION, [], "allow", AuthorizationDecision.ALLOW)
        ])
        assert pipeline.run(context) is context

    def test_a_pipeline_whose_services_never_decide_denies(self):
        pipeline = SecurityPipeline([RecordingSecurityService(AUTHENTICATION, [], "only")])
        with pytest.raises(AuthorizationError):
            pipeline.run(make_context())

    def test_an_empty_pipeline_denies_everything(self):
        with pytest.raises(AuthorizationError):
            SecurityPipeline([]).run(make_context())

    def test_a_decision_short_of_allow_denies_even_without_a_raise(self):
        pipeline = SecurityPipeline([
            RecordingSecurityService(AUTHORIZATION, [], "quiet", AuthorizationDecision.IMPLICIT_DENY)
        ])
        with pytest.raises(AuthorizationError):
            pipeline.run(make_context())

    def test_a_service_that_raises_stops_every_later_one(self):
        log = []
        pipeline = SecurityPipeline([
            RecordingSecurityService(AUTHENTICATION, log, "reject", error = AuthenticationError("no")),
            RecordingSecurityService(AUTHORIZATION, log, "never", AuthorizationDecision.ALLOW)
        ])
        with pytest.raises(AuthenticationError):
            pipeline.run(make_context())
        assert log == ["reject"]

    def test_len_counts_services(self):
        assert len(SecurityPipeline([RecordingSecurityService(AUTHENTICATION, [], "a")])) == 1

    def test_the_real_services_let_a_guest_run_the_agent(self):
        hasher = AuthenticationPasswordHasher(cost = 16, block_size = 1)
        identity_access_service = IdentityAccessService(IdentityAccessStoreInMemory(), hasher)
        authentication_service = AuthenticationService(
            identity_access_service, AuthenticationTokenCodec("s" * 32), hasher
        )
        token = authentication_service.issue_token(authentication_service.sign_in_guest())
        context = SecurityPipeline([
            authentication_service,
            AuthorizationService(identity_access_service)
        ]).run(make_context(token))
        assert context.allowed
