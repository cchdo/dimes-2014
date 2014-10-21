from django.conf import settings
from django.test import TestCase

from dimesfs.views import _delete_dir

from tagstore.client import TagStoreClient, Query


class DimesFSTestCase(TestCase):

    def setUp(self):
        settings.TS_API_ENDPOINT = 'http://sui.ucsd.edu:5000/api/v1'
        self.tsc = TagStoreClient(settings.TS_API_ENDPOINT)

        data = self.tsc.query_data(Query.tags_any('like', 'test:%'))
        for datum in data:
            self.tsc.delete(datum.id)

    def test_delete(self):
        """Make sure delete does not delete too much."""
        uri = 'test'
        data0 = self.tsc.create(uri, 'test', ['test:dir:test0'])
        data1 = self.tsc.create(uri, 'test', ['test:dir:test1/test2'])
        data2 = self.tsc.create(uri, 'test', ['test:dir:test1/test2'])
        self.assertEqual(
            1, len(self.tsc.query_data(Query.tags_any('eq', 'test:dir:test0'))))

        _delete_dir('test:dir:test1')
        self.assertEqual(
            0, len(self.tsc.query_data(Query.tags_any('like', 'test:dir:test1%'))))
        self.assertEqual(
            1, len(self.tsc.query_data(Query.tags_any('eq', 'test:dir:test0'))))
        self.tsc.delete(data0.id)
