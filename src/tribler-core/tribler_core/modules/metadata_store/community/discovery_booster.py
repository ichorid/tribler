import logging

from ipv8.peerdiscovery.discovery import EdgeWalk

from tribler_core.modules.metadata_store.community.remote_query_community import RemoteQueryCommunity


class DiscoveryBoosterMixin(RemoteQueryCommunity):
    TIMEOUT_IN_SEC = 10.0
    MAX_PEERS = 200

    TAKE_STEP_INTERVAL_IN_SEC = 0.05

    def __init__(self, *args, **kwargs):
        super(DiscoveryBoosterMixin, self).__init__(*args, **kwargs)
        self.mixin_logger = logging.getLogger('ChannelDiscoveryBoosterMixin')
        self.mixin_logger.info(
            f'Init. Timeout: {DiscoveryBoosterMixin.TIMEOUT_IN_SEC}s, '
            f'Max peers: {DiscoveryBoosterMixin.MAX_PEERS}, '
            f'Take step interval: {DiscoveryBoosterMixin.TAKE_STEP_INTERVAL_IN_SEC}s'
        )

        self.saved_max_peers = self.max_peers
        self.max_peers = DiscoveryBoosterMixin.MAX_PEERS

        # values for neighborhood_size and edge_length were found empirically to
        # maximize peer count at the end of a 30 seconds period
        self.walker = EdgeWalk(self, neighborhood_size=25, edge_length=25)

        self._take_step_task_name = 'take step'
        self.register_task(
            self._take_step_task_name, self.take_step, interval=DiscoveryBoosterMixin.TAKE_STEP_INTERVAL_IN_SEC
        )
        self.register_anonymous_task('', self.finish, delay=DiscoveryBoosterMixin.TIMEOUT_IN_SEC)

    def finish(self):
        self.mixin_logger.info(
            f'Finish. Set self.max_peers={self.saved_max_peers}. '
            f'Cancel pending task: {self._take_step_task_name}'
        )
        self.cancel_pending_task(self._take_step_task_name)

    def take_step(self):
        self.mixin_logger.debug('Take a step')
        self.walker.take_step()
