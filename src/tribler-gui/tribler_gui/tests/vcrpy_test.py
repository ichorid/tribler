import json
import unittest
from urllib.request import urlopen

from PyQt5 import QtCore
from PyQt5.QtCore import QCoreApplication

import tribler_gui
import tribler_gui.tribler_request_manager

import vcr
from vcr.errors import CannotOverwriteExistingCassetteException
from vcr.request import Request

app = QCoreApplication([])


class TriblerVCRRequest(tribler_gui.tribler_request_manager.TriblerNetworkRequest):
    _baseclass = tribler_gui.tribler_request_manager.TriblerNetworkRequest
    cassette = None

    def __init__(self, *args, **kwargs):
        self._vcr_request = None
        super().__init__(*args, **kwargs)

    def add_to_request_manager(self):
        self._vcr_request = Request(method=self.method, uri=self.url, body="", headers={})
        if self.cassette.can_play_response_for(self._vcr_request):
            # These are parts of TriblerRequest manager copy-pasted for simplicity
            response = self.cassette.play_response(self._vcr_request)
            self.reply_data = response['body']['string'].decode('latin_1')
            if not self.decode_json_response:
                self.received_json.emit(self.reply_data, None)
            else:
                json_result = json.loads(self.reply_data, encoding='latin_1')
                if (
                    'error' in json_result
                    and self.capture_errors
                    and not tribler_gui.tribler_request_manager.TriblerRequestManager.window.core_manager.shutting_down
                ):
                    tribler_gui.tribler_request_manager.request_manager.show_error(
                        tribler_gui.tribler_request_manager.TriblerRequestManager.get_message_from_error(json_result)
                    )
                self.received_json.emit(json_result, None)
            self.destruct()
        else:
            if self.cassette.write_protected and self.cassette.filter_request(self._vcr_request):
                raise CannotOverwriteExistingCassetteException(cassette=self.cassette, failed_request=self._vcr_request)
            super().add_to_request_manager()

    def on_finished(self, request):
        headers = {}
        for k, v in self.reply.rawHeaderPairs():
            headers[str(k, encoding='latin_1')] = [str(v, encoding='latin_1')]

        super().on_finished(request)
        response = {
            "status": {"code": self.status_code, "message": None},
            "headers": headers,
            "body": {"string": self.reply_data},
        }
        self.cassette.append(self._vcr_request, response)


my_vcr = vcr.config.VCR(
    custom_patches=((tribler_gui.tribler_request_manager, 'TriblerNetworkRequest', TriblerVCRRequest),)
)


class MyTestCase(unittest.TestCase):
    def test_vcrpy(self):
        with vcr.use_cassette('fixtures/vcr_cassettes/synopsis.yaml'):
            response = urlopen('http://httpbin.org/get')
            str_response = str(response.read())
            print(response.headers)
            print(str_response)

    def test_vcrpy2(self):
        with my_vcr.use_cassette('fixtures/vcr_cassettes/test_qt2.yaml'):
            loop = QtCore.QEventLoop()

            already_finished = []

            def null_callback(result):
                print(result)
                if loop.isRunning():
                    loop.quit()
                already_finished.append(1)
                print("QUITE")

            req = tribler_gui.tribler_request_manager.TriblerNetworkRequest(
                "http://httpbin.org/get", null_callback, capture_errors=True, on_cancel=null_callback
            )
            if not already_finished:
                loop.exec_()
            print("loop_exec2")

        # print (request_manager.requests_in_flight)
