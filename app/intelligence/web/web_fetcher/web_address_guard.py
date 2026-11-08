import httpx
import socket
import ipaddress
from typing import Callable, Optional

from app.intelligence.web import WebAccessError

NAT64_NETWORK = ipaddress.ip_network("64:ff9b::/96")


class WebAddressGuard:
    """Decides whether a URL may be fetched at all, and answers with the address to
    fetch it from.

    Every URL a tool fetches was chosen by a model, and a model can be steered — by the
    user, or by a page it just read telling it to fetch something else. On EC2 the
    address 169.254.169.254 hands out the instance's IAM credentials, and the database
    and every internal service sit on private addresses. So only http and https to
    hosts whose every resolved address is public are allowed: loopback, private,
    link-local, shared, multicast and reserved ranges are refused, including when they
    hide inside an IPv6 address (IPv4-mapped, 6to4, Teredo, NAT64).

    The check returns the address it approved, and the fetcher connects to exactly that
    address. Resolving once here and letting the HTTP client resolve again would leave
    a window for DNS rebinding — a name that answers with a public address for the
    check and a private one for the connection.

    The resolver is injectable so tests can decide what a name resolves to without a
    network."""

    ALLOWED_SCHEMES = {"http", "https"}

    def __init__(self, resolver: Optional[Callable[[str, int], list[str]]] = None) -> None:
        self._resolver: Callable[[str, int], list[str]] = (
            resolver if resolver is not None else self._resolve
        )

    def _resolve(self, host: str, port: int) -> list[str]:
        try:
            infos = socket.getaddrinfo(host, port, type = socket.SOCK_STREAM)
        except (socket.gaierror, UnicodeError):
            raise WebAccessError(f"'{host}' could not be resolved.") from None
        return list(dict.fromkeys(str(current_info[4][0]) for current_info in infos))

    def _embedded(self, address: ipaddress.IPv6Address) -> list[ipaddress.IPv4Address]:
        embedded = [address.ipv4_mapped, address.sixtofour, address.teredo[1] if address.teredo else None]
        if address in NAT64_NETWORK:
            embedded.append(ipaddress.IPv4Address(int(address) & 0xFFFFFFFF))
        return [current_address for current_address in embedded if current_address is not None]

    def is_public(self, address: str) -> bool:
        try:
            parsed = ipaddress.ip_address(address.split("%")[0])
        except ValueError:
            return False

        candidates = [parsed]
        if isinstance(parsed, ipaddress.IPv6Address):
            candidates.extend(self._embedded(parsed))

        return all(
            current_candidate.is_global and not current_candidate.is_multicast
            for current_candidate in candidates
        )

    def check(self, url: httpx.URL) -> str:
        if url.scheme not in self.ALLOWED_SCHEMES:
            raise WebAccessError(f"Only http and https URLs can be fetched, not '{url.scheme}:'.")
        if not url.host:
            raise WebAccessError(f"'{url}' names no host.")
        if url.userinfo:
            raise WebAccessError("URLs that carry a user name or password are refused.")

        addresses = self._resolver(url.host, url.port or (443 if url.scheme == "https" else 80))
        if not addresses:
            raise WebAccessError(f"'{url.host}' did not resolve to any address.")

        for current_address in addresses:
            if not self.is_public(current_address):
                raise WebAccessError(
                    f"'{url.host}' resolves to {current_address}, which is not a public "
                    f"address, so it was refused."
                )
        return addresses[0]
