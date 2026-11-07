import ipaddress


class FakeResolver:
    """Answers name lookups from a table instead of DNS, so a test decides whether a host
    is public or private. An IP literal resolves to itself, as it does with getaddrinfo;
    any other host missing from the table resolves to a public documentation address.
    Every lookup is recorded, so a test can prove a redirect was checked again."""

    PUBLIC_ADDRESS = "93.184.216.34"

    def __init__(self, table = None) -> None:
        self._table = dict(table or {})
        self.lookups = []

    def __call__(self, host, port):
        self.lookups.append(host)
        if host in self._table:
            return list(self._table[host])
        try:
            return [str(ipaddress.ip_address(host))]
        except ValueError:
            return [self.PUBLIC_ADDRESS]
