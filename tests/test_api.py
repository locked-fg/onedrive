import logging
from onedrive import auth
from onedrive import api
from onedrive.api import AsyncOperationStatus
import unittest


class TestApi(unittest.TestCase):

    def setUp(self):
        self.header = auth.login()
        api.mkdir("/api_test", self.header)

    def tearDown(self):
        api.delete("/api_test", self.header)
        api.delete("/api_test2", self.header)
        api.delete("/api_test_src", self.header)
        api.delete("/api_test_dst", self.header)

    def test_exists_mkdir(self):
        api.delete("/api_test", self.header)

        self.assertEqual(api.mkdir("/api_test", self.header).status_code, 201)
        self.assertTrue(api.exists("/api_test", self.header))

        self.assertEqual(api.delete("/api_test", self.header).status_code, 204)

    def test_get_meta(self):
        res = api.get_metadata("/", self.header)
        self.assertEqual(res.status_code, 200)
        self.assertIsNotNone(res.json_body()["folder"])

    def test_mkdir_parents(self):
        res = api.mkdir("/api_test/foo/bar/foobar", self.header, parents=False)
        self.assertEqual(res.status_code, 400)
        res = api.mkdir("/api_test/foo/bar/foobar", self.header, parents=True)
        self.assertEqual(res.status_code, 201)

        self.assertEqual(api.delete("/api_test", self.header).status_code, 204)

    def test_delete(self):
        self.assertEqual(api.delete("/api_test", self.header).status_code, 204)

    def test_copy_dir(self):
        self.assertTrue(api.exists("/api_test", self.header))
        res = api.copy("/api_test", "/api_test2", self.header)
        self.assertEqual(res.status_code, 202)
        self.assertIsNotNone(res.headers.get('Location', None))

        api.delete("/api_test", self.header)
        api.delete("/api_test2", self.header)

    def test_copy_file(self):
        api.mkdir("/api_test/x", self.header, parents=True)
        self.assertTrue(api.exists("/api_test", self.header))
        self.assertTrue(api.exists("/api_test/x", self.header))

        content = "1".encode("utf-8")
        api.upload_simple(data=content, dst="/api_test/foo.tmp", auth=self.header)
        self.assertTrue(api.exists("/api_test/foo.tmp", auth=self.header))

        res = api.copy("/api_test/foo.tmp", "/api_test/x/foo2.tmp", self.header)
        self.assertEqual(res.status_code, 202)
        location = res.headers.get('Location', None)
        self.assertIsNotNone(location)
        AsyncOperationStatus(location, self.header).block()

        self.assertTrue(api.exists("/api_test/foo.tmp", auth=self.header))
        self.assertTrue(api.exists("/api_test/x/foo2.tmp", auth=self.header))

        api.delete("/api_test", self.header)

    def test_upload_success(self):
        dst_file = "/api_test/upload.tmp"
        api.delete(dst_file, self.header)
        self.assertFalse(api.exists(dst_file, self.header))

        content = "test content".encode("utf-8")
        res = api.upload_simple(data=content, dst=dst_file, auth=self.header)
        self.assertEqual(res.status_code, 201)
        self.assertTrue(api.exists(dst_file, self.header))

        api.delete("/api_test", self.header)

    def test_upload_conflict_replace(self):
        dst_file = "/api_test/upload.tmp"
        api.delete(dst_file, self.header)  # just to be sure

        content = "1".encode("utf-8")
        res1 = api.upload_simple(data=content, dst=dst_file, auth=self.header)
        self.assertEqual(res1.status_code, 201)

        content = ("x"*1000).encode("utf-8")
        res2 = api.upload_simple(data=content, dst=dst_file, auth=self.header)
        self.assertEqual(res2.status_code, 200)
        size = api.get_metadata(dst_file, auth=self.header).json_body().get('size')

        self.assertEqual(size, 1000)
        api.delete("/api_test", self.header)

    def test_upload_conflict_rename(self):
        dst_file = "/api_test/upload.tmp"
        api.delete(dst_file, self.header)  # just to be sure

        content = "1".encode("utf-8")
        res1 = api.upload_simple(data=content, dst=dst_file, auth=self.header)
        self.assertEqual(res1.status_code, 201)

        content = "2".encode("utf-8")
        res2 = api.upload_simple(data=content, dst=dst_file, auth=self.header, conflict='rename')
        self.assertEqual(res2.status_code, 201)  # renamed to upload 1.tmp

        self.assertTrue(api.exists("/api_test/upload 1.tmp", auth=self.header))
        api.delete("/api_test", auth=self.header)

    def test_upload_conflict_fail(self):
        dst_file = "/api_test/upload.tmp"
        api.delete(dst_file, self.header)  # just to be sure

        content = "1".encode("utf-8")
        res1 = api.upload_simple(data=content, dst=dst_file, auth=self.header)
        self.assertEqual(res1.status_code, 201)

        content = "2".encode("utf-8")
        res2 = api.upload_simple(data=content, dst=dst_file, auth=self.header, conflict='fail')
        self.assertEqual(res2.status_code, 409)

        api.delete("/api_test", auth=self.header)

    def test_download(self):
        dst_file = "/api_test/upload.tmp"
        content = "12345".encode("utf-8")
        upload_result = api.upload_simple(data=content, dst=dst_file, auth=self.header)
        self.assertEqual(upload_result.status_code, 201)

        res = api.download(path=dst_file, auth=self.header)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(content, res.text.encode("utf-8"))

        api.delete("/api_test", auth=self.header)

    def test_move(self):
        api.mkdir("/api_test_src", self.header)
        api.mkdir("/api_test_dst", self.header)
        src_file = "/api_test_src/upload.tmp"
        api.upload_simple(data="1".encode("utf-8"), dst=src_file, auth=self.header)

        res = api.move(src_file, "/api_test_dst", auth=self.header)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(api.exists(src_file, auth=self.header))
        self.assertTrue(api.exists("/api_test_dst/upload.tmp", auth=self.header))

    def test_rename(self):
        src_file = "/api_test/upload.tmp"
        api.upload_simple(data="1".encode("utf-8"), dst=src_file, auth=self.header)
        res = api.rename(src_file, "renamed.tmp", auth=self.header)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(api.exists(src_file, auth=self.header))
        self.assertTrue(api.exists("/api_test/renamed.tmp", auth=self.header))


if __name__ == '__main__':
    logger = logging.getLogger('onedrive')
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    unittest.main()
