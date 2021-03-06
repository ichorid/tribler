import os

from twisted.internet.defer import fail
from Tribler.Core.Modules.channel.channel_manager import ChannelManager
from Tribler.Core.Modules.restapi.channels.base_channels_endpoint import UNKNOWN_CHANNEL_RESPONSE_MSG, \
    UNAUTHORIZED_RESPONSE_MSG
from Tribler.Test.Core.Modules.RestApi.Channels.test_channels_endpoint import AbstractTestChannelsEndpoint
from Tribler.Test.test_as_server import TESTS_DATA_DIR
from Tribler.Test.tools import trial_timeout


class TestChannelsRssEndpoints(AbstractTestChannelsEndpoint):

    @trial_timeout(10)
    def test_rss_feeds_endpoint_with_channel(self):
        """
        Testing whether the API returns the right JSON data if a rss feeds from a channel are fetched
        """
        expected_json = {u'rssfeeds': [{u'url': u'http://test1.com/feed.xml'}, {u'url': u'http://test2.com/feed.xml'}]}
        channel_name = "my channel"
        self.create_fake_channel(channel_name, "this is a short description")
        channel_obj = self.session.lm.channel_manager.get_channel(channel_name)
        for rss_item in expected_json[u'rssfeeds']:
            channel_obj.create_rss_feed(rss_item[u'url'])

        return self.do_request('channels/discovered/%s/rssfeeds' % 'fakedispersyid'.encode('hex'),
                               expected_code=200, expected_json=expected_json)

    @trial_timeout(10)
    def test_add_rss_feed_no_my_channel(self):
        """
        Testing whether the API returns a 404 if no channel has been created when adding a rss feed
        """
        self.session.lm.channel_manager = ChannelManager(self.session)
        channel_cid = 'fakedispersyid'.encode('hex')
        expected_json = {"error": UNKNOWN_CHANNEL_RESPONSE_MSG}
        return self.do_request('channels/discovered/' + channel_cid +
                               '/rssfeeds/http%3A%2F%2Frssfeed.com%2Frss.xml',
                               expected_code=404, expected_json=expected_json, request_type='PUT')

    @trial_timeout(10)
    def test_add_rss_feed_conflict(self):
        """
        Testing whether the API returns error 409 if a channel the rss feed already exists
        """
        expected_json = {"error": "this rss feed already exists"}
        my_channel_id = self.create_fake_channel("my channel", "this is a short description")
        channel_obj = self.session.lm.channel_manager.get_my_channel(my_channel_id)
        channel_obj.create_rss_feed("http://rssfeed.com/rss.xml")

        return self.do_request('channels/discovered/' + 'fakedispersyid'.encode('hex') +
                               '/rssfeeds/http%3A%2F%2Frssfeed.com%2Frss.xml', expected_code=409,
                               expected_json=expected_json, request_type='PUT')

    @trial_timeout(10)
    def test_add_rss_feed_with_channel(self):
        """
        Testing whether the API returns a 200 if a channel has been created and when adding a rss feed
        """

        def verify_rss_added(_):
            channel_obj = self.session.lm.channel_manager.get_my_channel(my_channel_id)
            self.assertEqual(channel_obj.get_rss_feed_url_list(), ["http://rssfeed.com/rss.xml"])

        expected_json = {"added": True}
        my_channel_id = self.create_fake_channel("my channel", "this is a short description")
        return self.do_request('channels/discovered/' + 'fakedispersyid'.encode('hex') +
                               '/rssfeeds/http%3A%2F%2Frssfeed.com%2Frss.xml', expected_code=200,
                               expected_json=expected_json, request_type='PUT')\
            .addCallback(verify_rss_added)

    @trial_timeout(10)
    def test_remove_rss_feed_no_channel(self):
        """
        Testing whether the API returns a 404 if no channel has been removed when adding a rss feed
        """
        self.session.lm.channel_manager = ChannelManager(self.session)
        expected_json = {"error": UNKNOWN_CHANNEL_RESPONSE_MSG}
        return self.do_request('channels/discovered/' + 'fakedispersyid'.encode('hex') +
                               '/rssfeeds/http%3A%2F%2Frssfeed.com%2Frss.xml',
                               expected_code=404, expected_json=expected_json, request_type='DELETE')

    @trial_timeout(10)
    def test_remove_rss_feed_invalid_url(self):
        """
        Testing whether the API returns a 404 and error if the url parameter does not exist in the existing feeds
        """
        expected_json = {"error": "this url is not added to your RSS feeds"}
        self.create_fake_channel("my channel", "this is a short description")
        return self.do_request('channels/discovered/' + 'fakedispersyid'.encode('hex') +
                               '/rssfeeds/http%3A%2F%2Frssfeed.com%2Frss.xml', expected_code=404,
                               expected_json=expected_json, request_type='DELETE')

    @trial_timeout(10)
    def test_remove_rss_feed_with_channel(self):
        """
        Testing whether the API returns a 200 if a channel has been created and when removing a rss feed
        """
        def verify_rss_removed(_):
            channel_obj = self.session.lm.channel_manager.get_my_channel(my_channel_id)
            self.assertEqual(channel_obj.get_rss_feed_url_list(), [])

        expected_json = {"removed": True}
        my_channel_id = self.create_fake_channel("my channel", "this is a short description")
        channel_obj = self.session.lm.channel_manager.get_my_channel(my_channel_id)
        channel_obj.create_rss_feed("http://rssfeed.com/rss.xml")

        return self.do_request('channels/discovered/' + 'fakedispersyid'.encode('hex') +
                               '/rssfeeds/http%3A%2F%2Frssfeed.com%2Frss.xml', expected_code=200,
                               expected_json=expected_json, request_type='DELETE').addCallback(verify_rss_removed)

    @trial_timeout(10)
    def test_recheck_rss_feeds_no_channel(self):
        """
        Testing whether the API returns a 404 if no channel has been created when rechecking rss feeds
        """
        self.session.lm.channel_manager = ChannelManager(self.session)
        expected_json = {"error": UNKNOWN_CHANNEL_RESPONSE_MSG}
        return self.do_request('channels/discovered/%s/recheckfeeds' % 'fakedispersyid'.encode('hex'),
                               expected_code=404, expected_json=expected_json, request_type='POST')

    @trial_timeout(10)
    def test_recheck_rss_feeds(self):
        """
        Testing whether the API returns a 200 if the rss feeds are rechecked in your channel
        """
        expected_json = {"rechecked": True}
        my_channel_id = self.create_fake_channel("my channel", "this is a short description")
        channel_obj = self.session.lm.channel_manager.get_my_channel(my_channel_id)
        channel_obj._is_created = True
        channel_obj.create_rss_feed(os.path.join(TESTS_DATA_DIR, 'test_rss_empty.xml'))

        return self.do_request('channels/discovered/%s/recheckfeeds' % 'fakedispersyid'.encode('hex'),
                               expected_code=200, expected_json=expected_json, request_type='POST')

    @trial_timeout(10)
    def test_recheck_rss_feeds_error(self):
        """
        Testing whether the API returns error 500 if refresh of rss feeds is failing
        """
        my_channel_id = self.create_fake_channel("my channel", "this is a short description")
        channel_obj = self.session.lm.channel_manager.get_my_channel(my_channel_id)
        channel_obj._is_created = True
        channel_obj.create_rss_feed(os.path.join(TESTS_DATA_DIR, 'test_rss_empty.xml'))

        def mocked_refresh_all_feeds():
            return fail(RuntimeError("test fail"))

        channel_obj.refresh_all_feeds = mocked_refresh_all_feeds

        self.should_check_equality = False
        return self.do_request('channels/discovered/%s/recheckfeeds' % 'fakedispersyid'.encode('hex'),
                               expected_code=500, request_type='POST')

    @trial_timeout(10)
    def test_get_rss_feed_no_authorization(self):
        """
        Testing whether the API returns unauthorized error if attempting to recheck feeds in another channel
        """
        self.channel_db_handler.on_channel_from_dispersy('fake', 3, 'test name', 'test description')

        expected_json = {"error": UNAUTHORIZED_RESPONSE_MSG}

        return self.do_request('channels/discovered/%s/rssfeeds' % 'fake'.encode('hex'),
                               expected_code=401, expected_json=expected_json, request_type='GET')

    @trial_timeout(10)
    def test_get_rss_feed_no_channel_obj(self):
        """
        Testing whether the API returns error 404 if no channel object exists in the channel manager
        """
        self.create_fake_channel("my channel", "this is a short description")
        self.session.lm.channel_manager._channel_list = []

        expected_json = {"error": UNKNOWN_CHANNEL_RESPONSE_MSG}

        return self.do_request('channels/discovered/%s/rssfeeds' % 'fakedispersyid'.encode('hex'),
                               expected_code=404, expected_json=expected_json, request_type='GET')
