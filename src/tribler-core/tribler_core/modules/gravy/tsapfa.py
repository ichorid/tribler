from dataclasses import dataclass
from typing import Set


@dataclass
class Host:
    pass


@dataclass
class ResId:
    numeric_id: int
    providers: Set[Host]
    resource: None  # backreference to the corresponding Resource, if known

    def __hash__(self):
        return hash(self.numeric_id)


@dataclass
class Resource:
    id_: ResId
    parent_id: ResId
    children_ids: Set[ResId]

    def __hash__(self):
        return hash(self.id_)


class GravyTsapfa:
    def __init__(self):
        self.resources_cache = Set[ResId]  # resources this host knows about
        self.my_resources = Set[ResId]  # resources this host provides to the network
        self.permanent_peers = Set[Host]  # Our permanent connections


    def add_resource(self, res: Resource):
        pass

    def fetch_resources_recursively(self, swarm_id: ResId):
        pass


    def join_swarm(self, swarm_id: ResId):

        # Recursively download all the resources in the joined swarm
        self.my_resources.update(self.fetch_resources_recursively(swarm_id))

        # Add parent link providers to permanent peers
        self.permanent_peers.update(swarm_id.providers)

        # Add child link providers to permanent peers
        for child_id in swarm_id.resource.children_ids:
            self.permanent_peers.update(child_id.providers)
