import logging
from onedrive import auth
from onedrive import api

import unittest


class TestApi(unittest.TestCase):

    def test_exists_mkdir(self):
        header = auth.login()
        self.assertFalse(api.exists("/api_test", header))
        self.assertEqual(api.mkdir("/api_test", header).status_code, 201)
        self.assertTrue(api.exists("/api_test", header))
        # clean up
        self.assertEqual(api.delete("/api_test", header).status_code, 204)

    def test_get_meta(self):
        header = auth.login()
        res = api.get_metadata("/", header)
        self.assertEqual(res.status_code, 200)
        self.assertIsNotNone(res.json_body()["folder"])

    def test_mkdir_parents(self):
        header = auth.login()
        res = api.mkdir("/api_test/foo/bar/foobar", header, parents=False)
        self.assertEqual(res.status_code, 400)
        res = api.mkdir("/api_test/foo/bar/foobar", header, parents=True)
        self.assertEqual(res.status_code, 201)
        # clean up
        self.assertEqual(api.delete("/api_test", header).status_code, 204)

    def test_delete(self):
        header = auth.login()
        api.mkdir("/api_test", header)
        self.assertEqual(api.delete("/api_test", header).status_code, 204)

    def test_copy(self):
        header = auth.login()
        api.mkdir("/api_test", header)
        self.assertTrue(api.exists("/api_test", header))
        res = api.copy("/api_test", "/api_test2", header)
        self.assertEqual(res.status_code, 202)
        self.assertIsNotNone(res.headers.get('Location', None))
        api.delete("/api_test", header)
        api.delete("/api_test2", header)

    # def test_get_sha1(self):
    #     print("needs test with real file -> needs create file")


if __name__ == '__main__':
    logger = logging.getLogger('onedrive')
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    unittest.main()
