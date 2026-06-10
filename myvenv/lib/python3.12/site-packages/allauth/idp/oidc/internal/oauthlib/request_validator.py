from __future__ import annotations

import base64
import uuid
from datetime import timedelta
from typing import Any

from django.utils import timezone

import jwt
from oauthlib.common import Request
from oauthlib.openid import RequestValidator

from allauth.core import context
from allauth.core.internal import jwkkit
from allauth.idp.oidc import app_settings
from allauth.idp.oidc.adapter import get_adapter
from allauth.idp.oidc.internal.clientkit import (
    is_origin_allowed,
    is_redirect_uri_allowed,
)
from allauth.idp.oidc.internal.oauthlib import authorization_codes
from allauth.idp.oidc.internal.oauthlib.utils import (
    ValidatorContext,
    get_validator_context,
)
from allauth.idp.oidc.internal.resources import InvalidTargetError, is_resources_subset
from allauth.idp.oidc.internal.tokens import decode_jwt_token
from allauth.idp.oidc.models import Client, Token


class OAuthLibRequestValidator(RequestValidator):
    def validate_client_id(self, client_id: Any, request: Request) -> bool:
        if not isinstance(client_id, str):
            return False
        client = self._lookup_client(request, client_id)
        if not client:
            return False
        self._use_client(request, client)
        return True

    def validate_redirect_uri(
        self, client_id, redirect_uri, request, *args, **kwargs
    ) -> bool:
        return is_redirect_uri_allowed(
            redirect_uri,
            request.client.get_redirect_uris(),
            request.client.allow_uri_wildcards,
        )

    def validate_response_type(
        self, client_id, response_type, client, request: Request, *args, **kwargs
    ) -> bool:
        return response_type in request.client.get_response_types()

    def validate_scopes(
        self, client_id, scopes, client, request: Request, *args, **kwargs
    ) -> bool:
        return set(scopes).issubset(request.client.get_scopes())

    def get_default_scopes(
        self, client_id, request: Request, *args, **kwargs
    ) -> list[str]:
        return request.client.get_default_scopes()

    def save_authorization_code(
        self, client_id, code, request: Request, *args, **kwargs
    ) -> None:
        # WORKAROUND: docstring says:
        # > To support OIDC, you MUST associate the code with:
        # > - nonce, if present (``code["nonce"]``)
        # Yet, nonce is not there, it is in request.nonce.
        nonce = getattr(request, "nonce", None)
        if nonce:
            code = dict(**code, nonce=nonce)
        # (end WORKAROUND)
        authorization_codes.create(request.client, code, request)

    def authenticate_client_id(
        self, client_id, request: Request, *args, **kwargs
    ) -> bool:
        """Ensure client_id belong to a non-confidential client."""
        client = self._lookup_client(request, client_id)
        if not client or client.type != Client.Type.PUBLIC:
            return False
        self._use_client(request, client)
        return True

    def _extract_basic_auth(self, request: Request) -> tuple[str | None, str | None]:
        auth = request.headers.get("Authorization", "")
        scheme, _, credentials = auth.partition(" ")
        if scheme.lower() != "basic" or not credentials:
            return None, None
        try:
            decoded = base64.b64decode(credentials).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return None, None
        client_id, _, client_secret = decoded.partition(":")
        if not client_id or not client_secret:
            return None, None
        return client_id, client_secret

    def authenticate_client(self, request: Request, *args, **kwargs) -> bool:
        client_id, client_secret = self._extract_basic_auth(request)
        if not client_id and not client_secret:
            client_id = getattr(request, "client_id", None)
            client_secret = getattr(request, "client_secret", None)
        if not isinstance(client_id, str):
            return False
        if not client_secret and request.grant_type == Client.GrantType.DEVICE_CODE:
            return self.authenticate_client_id(client_id, request)
        if not client_secret or not isinstance(client_secret, str):
            return False
        client = self._lookup_client(request, client_id)
        if not client:
            return False
        if not client.check_secret(client_secret):
            return False
        self._use_client(request, client)
        return True

    def validate_grant_type(
        self, client_id, grant_type, client, request: Request, *args, **kwargs
    ) -> bool:
        return grant_type in client.get_grant_types()

    def validate_code(
        self, client_id, code, client, request: Request, *args, **kwargs
    ) -> bool:
        return authorization_codes.validate(client_id, code, request)

    def confirm_redirect_uri(
        self, client_id, code, redirect_uri, client, request: Request, *args, **kwargs
    ) -> bool:
        authorization_code = self._lookup_authorization_code(request, client_id, code)
        if not authorization_code:
            return False
        return redirect_uri == authorization_code["redirect_uri"]

    def save_bearer_token(self, token: dict, request: Request, *args, **kwargs) -> None:
        """
        https://datatracker.ietf.org/doc/html/rfc6749#section-6
        > The authorization server MAY issue a new refresh token, in which case
        > the client MUST discard the old refresh token and replace it with the
        > new refresh token.  The authorization server MAY revoke the old
        > refresh token after issuing a new refresh token to the client.  If a
        > new refresh token is issued, the refresh token scope MUST be
        > identical to that of the refresh token included by the client in the
        > request.

        https://datatracker.ietf.org/doc/html/rfc6749#section-1.5
        > Refresh tokens are issued to the client by the authorization server and
        > are used to obtain a new access token when the current access token becomes
        > invalid or expires, or to obtain additional access tokens with identical or
        > narrower scope
        """
        ctx = get_validator_context()
        refresh_token = token.get("refresh_token")
        tokens = []
        if refresh_token:
            rt = self._prep_refresh_token(ctx, refresh_token, request)
            if not rt.pk:
                tokens.append(rt)
        access_token = self._prep_access_token(ctx, token, request)
        tokens.append(access_token)
        for t in tokens:
            t.set_scopes(request.scopes)
            if ctx.email:
                t.set_scope_email(ctx.email)
        Token.objects.bulk_create(tokens)

    def _prep_access_token(
        self, ctx: ValidatorContext, token: dict, request: Request
    ) -> Token:
        adapter = get_adapter()
        access_token = Token(
            client=request.client,
            user=request.user,
            type=Token.Type.ACCESS_TOKEN,
            hash=adapter.hash_token(token["access_token"]),
            expires_at=timezone.now() + timedelta(seconds=token["expires_in"]),
        )
        if resources := ctx.requested_resources:
            if not is_resources_subset(resources, ctx.granted_resources):
                raise InvalidTargetError
        else:
            resources = ctx.granted_resources
        if resources:
            access_token.set_resources(resources)
        return access_token

    def _prep_refresh_token(
        self, ctx: ValidatorContext, refresh_token: str, request: Request
    ) -> Token:
        adapter = get_adapter()
        refresh_token_hash = adapter.hash_token(refresh_token)
        rt: Token | None = ctx.refresh_token
        if rt:
            ctx.granted_resources = rt.get_resources()
            if not ctx.email and "email" in request.scopes:
                ctx.email = rt.get_scope_email()
        if (
            rt
            and not app_settings.ROTATE_REFRESH_TOKEN
            and refresh_token_hash == rt.hash
        ):
            # We reuse our token.
            return rt

        resources: list[str] | None
        if rt:
            resources = rt.get_resources()
            # If we have an existing refresh token, drop it, because of:
            assert (
                app_settings.ROTATE_REFRESH_TOKEN or refresh_token_hash != rt.hash
            )  # nosec[assert_used]
            rt.delete()
            rt = None
        else:
            resources = ctx.granted_resources
        new_rt = Token(
            client=request.client,
            user=request.user,
            type=Token.Type.REFRESH_TOKEN,
            hash=refresh_token_hash,
        )
        if resources:
            new_rt.set_resources(resources)
        rt = new_rt
        return rt

    def invalidate_authorization_code(
        self, client_id, code, request: Request, *args, **kwargs
    ) -> None:
        authorization_codes.invalidate(client_id, code)

    def validate_user_match(
        self, id_token_hint, scopes, claims, request: Request
    ) -> bool:
        if not context.request.user:
            return False
        sub = None
        if id_token_hint:
            payload = decode_jwt_token(
                id_token_hint,
                client_id=request.client.id,
                verify_exp=True,
                verify_iss=True,
            )
            if payload is None:
                return False
            sub = payload.get("sub")
            session_sub = get_adapter().get_user_sub(
                request.client, context.request.user
            )
            if sub != session_sub:
                return False
        if claims:
            sub = claims.get("sub")
            session_sub = get_adapter().get_user_sub(
                request.client, context.request.user
            )
            if sub != session_sub:
                return False
        return True

    def get_authorization_code_scopes(
        self, client_id, code, redirect_uri, request
    ) -> list[str]:
        authorization_code = self._lookup_authorization_code(request, client_id, code)
        if not authorization_code:
            return []
        return authorization_code["scopes"]

    def get_authorization_code_nonce(
        self, client_id, code, redirect_uri, request
    ) -> str | None:
        authorization_code = self._lookup_authorization_code(request, client_id, code)
        if authorization_code is None:
            return None
        return authorization_code["code"].get("nonce")

    def get_code_challenge(self, code, request: Request) -> str | None:
        ret = None
        authorization_code = self._lookup_authorization_code(
            request, request.client_id, code
        )
        if authorization_code is None:
            return None
        if pkce := authorization_code.get("pkce"):
            ret = pkce["code_challenge"]
        return ret

    def get_code_challenge_method(self, code, request: Request) -> str | None:
        ret = None
        authorization_code = self._lookup_authorization_code(
            request, request.client_id, code
        )
        if authorization_code is None:
            return None
        if pkce := authorization_code.get("pkce"):
            ret = pkce["code_challenge_method"]
        return ret

    def is_pkce_required(self, client_id, request: Request) -> bool:
        client = self._lookup_client(request, client_id)
        return bool(client and client.type == Client.Type.PUBLIC)

    def finalize_id_token(
        self, id_token: dict, token: dict, token_handler, request
    ) -> str:
        """
        https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims
        """
        adapter = get_adapter()
        id_token["iss"] = adapter.get_issuer()
        id_token["exp"] = id_token["iat"] + app_settings.ID_TOKEN_EXPIRES_IN
        id_token["jti"] = uuid.uuid4().hex
        ctx = get_validator_context()
        email = ctx.email
        id_token.update(
            adapter.get_claims(
                "id_token", request.user, request.client, request.scopes, email=email
            )
        )
        adapter.populate_id_token(id_token, request.client, request.scopes)
        jwk_dict, private_key = jwkkit.load_jwk_from_pem(app_settings.PRIVATE_KEY)
        return jwt.encode(
            id_token, private_key, algorithm="RS256", headers={"kid": jwk_dict["kid"]}
        )

    def validate_bearer_token(self, token, scopes, request: Request) -> bool:
        if not token:
            return False
        if context.request.GET.get("access_token") == token:
            # Supporting tokens in query params is considered bad practice, yet,
            # oauthlib supports this. E.g., if access tokens are sent via URI
            # query parameters, such tokens may leak to log files and the HTTP
            # 'referer'.
            return False
        instance = Token.objects.lookup(Token.Type.ACCESS_TOKEN, token)
        if not instance:
            return False
        if instance.user and not instance.user.is_active:
            return False
        granted_scopes = instance.get_scopes()
        if not set(scopes).issubset(set(granted_scopes)):
            return False
        request.user = instance.user
        if not instance.client:
            return False
        self._use_client(request, instance.client)
        request.scopes = granted_scopes
        get_validator_context().access_token = instance
        request.access_token = token
        return True

    def revoke_token(self, token, token_type_hint, request, *args, **kwargs) -> None:
        if token_type_hint == "access_token":  # nosec
            types = [Token.Type.ACCESS_TOKEN]
        elif token_type_hint == "refresh_token":  # nosec
            types = [Token.Type.REFRESH_TOKEN]
        else:
            types = [Token.Type.ACCESS_TOKEN, Token.Type.REFRESH_TOKEN]
        Token.objects.by_value(token).filter(type__in=types).delete()

    def get_userinfo_claims(self, request: Request) -> dict:
        access_token = get_validator_context().access_token
        assert access_token  # nosec
        email = access_token.get_scope_email()
        return get_adapter().get_claims(
            "userinfo", request.user, request.client, request.scopes, email=email
        )

    def get_default_redirect_uri(
        self, client_id, request: Request, *args, **kwargs
    ) -> None:
        # https://openid.net/specs/openid-financial-api-part-1-1_0.html#section-5.2.2
        # 9. shall require the redirect_uri in the authorization request;
        # So, don't support a default.
        return None

    def validate_user(
        self, username, password, client, request: Request, *args, **kwargs
    ) -> bool:
        """
        Note that this bypasses MFA, which is why the password grant is not
        recommended and hence disabled. This could work:

            try:
                user = get_account_adapter().authenticate(
                    context.request, username=username, password=password
                )
            except ValidationError:
                return False
            else:
                if not user:
                    return False
                request.user = user
                return True
        """
        return False

    def validate_refresh_token(
        self, refresh_token, client, request: Request, *args, **kwargs
    ) -> bool:
        token = Token.objects.filter(client=client).lookup(
            Token.Type.REFRESH_TOKEN, refresh_token
        )
        if not token:
            return False
        if not token.user or not token.user.is_active:
            return False
        request.user = token.user
        get_validator_context().refresh_token = token
        return True

    def get_original_scopes(
        self, refresh_token, request: Request, *args, **kwargs
    ) -> list[str]:
        rt = get_validator_context().refresh_token
        assert rt is not None  # nosec
        return rt.get_scopes()

    def client_authentication_required(self, request: Request, *args, **kwargs) -> bool:
        if request.client_id and request.client_secret:
            return True

        client = self._lookup_client(request, request.client_id)
        if client and client.type == Client.Type.PUBLIC:
            return False
        return super().client_authentication_required(request, *args, **kwargs)

    def _lookup_client(self, request: Request, client_id: str) -> Client | None:
        """
        In various places, oauthlib documents:

            Note, while not strictly necessary it can often be very convenient
            to set request.client to the client object associated with the
            given client_id.

        It's unclear though that if this is not explicitly stated, and, we still
        were to set request.client, whether that could have adverse side
        effects. So, don't assign request.client here.
        """
        cache = get_validator_context().clients
        if client_id in cache:
            client = cache[client_id]
        else:
            client = Client.objects.filter(id=client_id).first()
            cache[client_id] = client
        return client

    def _use_client(self, request: Request, client: Client) -> None:
        request.client = client
        request.client.client_id = client.id

    def _lookup_authorization_code(
        self, request: Request, client_id: str, code: str
    ) -> dict | None:
        cache = get_validator_context().codes
        key = (client_id, code)
        if key in cache:
            authorization_code = cache[key]
        else:
            authorization_code = authorization_codes.lookup(client_id, code)
            cache[key] = authorization_code
        return authorization_code

    def is_origin_allowed(
        self, client_id, origin, request: Request, *args, **kwargs
    ) -> bool:
        client = self._lookup_client(request, client_id)
        return bool(
            client
            and is_origin_allowed(
                origin, client.get_cors_origins(), client.allow_uri_wildcards
            )
        )

    def rotate_refresh_token(self, request: Request) -> bool:
        return app_settings.ROTATE_REFRESH_TOKEN

    def validate_silent_login(self, request: Request) -> bool:
        if context.request.user.is_authenticated:
            request.user = context.request.user
            return True
        return False

    def validate_silent_authorization(self, request: Request) -> bool:
        granted_scopes = set()
        tokens = Token.objects.valid().filter(
            user=context.request.user,
            type__in=[Token.Type.REFRESH_TOKEN, Token.Type.ACCESS_TOKEN],
        )
        for token in tokens.iterator():
            granted_scopes.update(token.get_scopes())
        return set(request.scopes).issubset(granted_scopes)

    def validate_jwt_bearer_token(self, token, scopes, request: Request) -> bool:
        payload = decode_jwt_token(token, verify_iss=True, verify_exp=True)
        if not payload:
            return False
        token_use = payload.get("token_use")
        if token_use == "access":  # nosec
            return self._validate_jwt_bearer_access_token(
                token, scopes, request, payload
            )
        return self._validate_jwt_bearer_id_token(token, scopes, request, payload)

    def _validate_jwt_bearer_id_token(self, token, scopes, request, payload) -> bool:
        if scopes:
            # We don't have scope for the ID token
            return False
        client_id = payload.get("aud")
        return self.validate_client_id(client_id, request)

    def _validate_jwt_bearer_access_token(
        self, token, scopes, request, payload
    ) -> bool:
        client_id = payload.get("client_id")
        if not self.validate_client_id(client_id, request):
            return False
        return self.validate_bearer_token(token, scopes, request)
