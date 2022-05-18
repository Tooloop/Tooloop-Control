from zeroconf import ServiceBrowser, ServiceListener, Zeroconf, IPVersion


class TooloopServiceListener(ServiceListener):
    def __init__(self, servers):
        super(TooloopServiceListener, self).__init__()
        self.servers = servers

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self.servers[name] = self.get_server_info(zc, type_, name)
        print(f"Service {name} updated")

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self.servers.pop(name)
        print(f"Service {name} removed")

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self.servers[name] = self.get_server_info(zc, type_, name)
        print(f"Service {name} added")

    def get_server_info(self, zc, type_, name):
        info = zc.get_service_info(type_, name)
        hostname = info.server.rstrip('.local.')
        for address in info.parsed_addresses(IPVersion.V4Only):
            if address != '127.0.0.1':
                ip = address
        return {'hostname': hostname, 'ip': ip}


class NetworkDiscovery(object):
    """Holds information of available servers in the network."""

    def __init__(self):
        super(NetworkDiscovery, self).__init__()
        self.servers = {}
        self.zeroconf = Zeroconf()
        self.listener = TooloopServiceListener(self.servers)
        self.browser = ServiceBrowser(
            self.zeroconf, "_tooloop-control-center._tcp.local.", self.listener)

    def get_servers(self):
        return self.servers.values()
