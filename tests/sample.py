import logging

import io

from onedrive import auth
from onedrive import api

import unittest


class TestApi(unittest.TestCase):

    def test_exists_mkdir(self):
        header = auth.login()
        api.delete("/api_test", header)
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

    def test_upload_success(self):
        header = auth.login()
        api.mkdir("/api_test", header)
        dst_file = "/api_test/upload.tmp"
        api.delete(dst_file, header)
        self.assertFalse(api.exists(dst_file, header))

        content = "test content".encode("utf-8")
        res = api.upload_simple(data=content, dst=dst_file, auth=header)
        self.assertEqual(res.status_code, 201)
        self.assertTrue(api.exists(dst_file, header))

        api.delete("/api_test", header)

    def test_upload_conflict_replace(self):
        header = auth.login()
        api.mkdir("/api_test", header)
        dst_file = "/api_test/upload.tmp"
        api.delete(dst_file, header)  # just to be sure

        content = "1".encode("utf-8")
        res1 = api.upload_simple(data=content, dst=dst_file, auth=header)
        self.assertEqual(res1.status_code, 201)

        content = ("x"*1000).encode("utf-8")
        res2 = api.upload_simple(data=content, dst=dst_file, auth=header)
        self.assertEqual(res2.status_code, 200)
        size = api.get_metadata(dst_file, auth=header).json_body().get('size')

        self.assertEqual(size, 1000)
        api.delete("/api_test", header)

    def test_upload_conflict_rename(self):
        header = auth.login()
        api.mkdir("/api_test", header)
        dst_file = "/api_test/upload.tmp"
        api.delete(dst_file, header)  # just to be sure

        content = "1".encode("utf-8")
        res1 = api.upload_simple(data=content, dst=dst_file, auth=header)
        self.assertEqual(res1.status_code, 201)

        content = "2".encode("utf-8")
        res2 = api.upload_simple(data=content, dst=dst_file, auth=header, conflict='rename')
        self.assertEqual(res2.status_code, 201)  # renamed to upload 1.tmp

        self.assertTrue(api.exists("/api_test/upload 1.tmp", auth=header))
        api.delete("/api_test", auth=header)

    def test_upload_conflict_fail(self):
        header = auth.login()
        api.mkdir("/api_test", header)
        dst_file = "/api_test/upload.tmp"
        api.delete(dst_file, header)  # just to be sure

        content = "1".encode("utf-8")
        res1 = api.upload_simple(data=content, dst=dst_file, auth=header)
        self.assertEqual(res1.status_code, 201)

        content = "2".encode("utf-8")
        res2 = api.upload_simple(data=content, dst=dst_file, auth=header, conflict='fail')
        self.assertEqual(res2.status_code, 409)

        api.delete("/api_test", auth=header)

    def test_download(self):
        #header = auth.login()
        #api.mkdir("/api_test", header)
        #self.assertTrue(api.exists("/api_test/upload.tmp", header))

        pass


if __name__ == '__main__':
    logger = logging.getLogger('onedrive')
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    unittest.main()
