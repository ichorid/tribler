import logging

from ipv8.peerdiscovery.discovery import EdgeWalk


class DiscoveryBooster:
    def __init__(self, timeout_in_sec=10.0, max_peers=200, take_step_interval_in_sec=0.05):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.timeout_in_sec = timeout_in_sec
        self.max_peers = max_peers
        self.take_step_interval_in_sec = take_step_interval_in_sec

        self.community = None
        self.saved_max_peers = None
        self.walker = None

        self._take_step_task_name = 'take step'

    def apply(self, community):
        if not community:
            return

        self.logger.info(
            f'Apply. Timeout: {self.timeout_in_sec}s, '
            f'Max peers: {self.max_peers}, '
            f'Take step interval: {self.take_step_interval_in_sec}s'
        )

        self.community = community
        self.saved_max_peers = community.max_peers

        community.max_peers = self.max_peers

        # values for neighborhood_size and edge_length were found empirically to
        # maximize peer count at the end of a 30 seconds period
        self.walker = EdgeWalk(community, neighborhood_size=25, edge_length=25)

        community.register_task(self._take_step_task_name, self.take_step, interval=self.take_step_interval_in_sec)

        community.register_anonymous_task('', self.finish, delay=self.timeout_in_sec)

    def finish(self):
        self.logger.info(
            f'Finish. Set self.max_peers={self.saved_max_peers}. Cancel pending task: {self._take_step_task_name}'
        )
        self.community.max_peers = self.saved_max_peers
        self.community.cancel_pending_task(self._take_step_task_name)

    def take_step(self):
        self.logger.debug('Take a step')
        self.walker.take_step()
