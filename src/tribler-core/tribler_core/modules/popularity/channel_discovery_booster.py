import logging

from pony.orm import count, db_session

from ipv8.peerdiscovery.discovery import EdgeWalk
from tribler_core.modules.metadata_store.community.remote_query_community import RemoteQueryCommunity
from tribler_core.modules.metadata_store.serialization import CHANNEL_TORRENT


class ChannelDiscoveryBoosterMixin(RemoteQueryCommunity):
    TIMEOUT_IN_SEC = 30.0
    MAX_PEERS = 200
    RESULTS_PER_QUERY = 50

    TAKE_STEP_INTERVAL_IN_SEC = 0.05

    def __init__(self, *args, **kwargs):
        super(ChannelDiscoveryBoosterMixin, self).__init__(*args, **kwargs)
        self.mixin_logger = logging.getLogger('ChannelDiscoveryBoosterMixin')
        self.mixin_logger.info(f'Init. Timeout: {ChannelDiscoveryBoosterMixin.TIMEOUT_IN_SEC}s, '
                               f'Max peers: {ChannelDiscoveryBoosterMixin.MAX_PEERS}, '
                               f'Take step interval: {ChannelDiscoveryBoosterMixin.TAKE_STEP_INTERVAL_IN_SEC}s')

        self.saved_max_peers = self.max_peers
        self.max_peers = ChannelDiscoveryBoosterMixin.MAX_PEERS

        # values for neighborhood_size and edge_length were found empirically to
        # maximize peer count at the end of a 30 seconds period
        self.walker = EdgeWalk(self, neighborhood_size=25, edge_length=25)

        self._registered_tasks_names = []
        self.register_task_until_timeout('take step', self.take_step,
                                         interval=ChannelDiscoveryBoosterMixin.TAKE_STEP_INTERVAL_IN_SEC)

        self._time = 0
        self._introduction_response_count = 0
        self.register_task('measure', self.measure, interval=1)

        self.register_task('clean', self.clean,
                           delay=ChannelDiscoveryBoosterMixin.TIMEOUT_IN_SEC)

    def register_task_until_timeout(self, name, task, *args, delay=None, interval=None, ignore=()):
        self.mixin_logger.info(f'Register task until timeout: {name}')
        self.register_task(name, task, *args, delay=delay, interval=interval, ignore=ignore)
        self._registered_tasks_names.append(name)

    def measure(self):
        with db_session:
            channels_count = count(ts for ts in self.mds.ChannelNode if ts.metadata_type == CHANNEL_TORRENT)
        print(f'{self._time}, {len(self.get_peers())}, {self._introduction_response_count}, {channels_count}')

        self._time += 1

    def clean(self):
        self.mixin_logger.info(f'Clean. Set self.max_peers={self.saved_max_peers}. '
                               f'Cancel pending tasks: {self._registered_tasks_names}')
        self.max_peers = self.saved_max_peers
        for registered_task_name in self._registered_tasks_names:
            self.cancel_pending_task(registered_task_name)

    def take_step(self):
        self.mixin_logger.debug('Take step')
        self.walker.take_step()

    def introduction_response_callback(self, peer, dist, payload):
        super().introduction_response_callback(peer, dist, payload)
        self.mixin_logger.debug('Introduction response callback')

        if peer.address in self.network.blacklist:
            self.mixin_logger.debug(f'Peer {peer.address} in blacklist')
            return

        self._introduction_response_count += 1

        self.mixin_logger.info('Send remote select')
        # self.send_remote_select(peer=peer, metadata_type=CHANNEL_TORRENT,
        #                         attribute_ranges=(("num_entries", 1, None),),
        #                         last=ChannelDiscoveryBoosterMixin.RESULTS_PER_QUERY)
