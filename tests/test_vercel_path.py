import io
import json
import unittest
from pathlib import Path

from vercel_path import VercelPathMiddleware


class VercelRewriteConfigTests(unittest.TestCase):
    def test_rewrite_passes_the_original_path_to_middleware(self):
        config_path = Path(__file__).resolve().parents[1] / 'vercel.json'
        config = json.loads(config_path.read_text(encoding='utf-8'))

        self.assertEqual(config['rewrites'], [{
            'source': '/:path*',
            'destination': '/api/index?__tse_path=/:path*',
        }])


class VercelPathMiddlewareTests(unittest.TestCase):
    def setUp(self):
        self.seen = None

        def app(environ, start_response):
            self.seen = (environ['SCRIPT_NAME'], environ['PATH_INFO'], environ['QUERY_STRING'])
            start_response('200 OK', [('Content-Type', 'text/plain')])
            return [b'ok']

        self.middleware = VercelPathMiddleware(app)

    def invoke(self, query):
        environ = {
            'SCRIPT_NAME': '',
            'PATH_INFO': '/api/index',
            'QUERY_STRING': query,
            'REQUEST_METHOD': 'GET',
            'wsgi.input': io.BytesIO(),
        }
        response = {}

        def start_response(status, headers):
            response['status'] = status

        body = b''.join(self.middleware(environ, start_response))
        return response['status'], body

    def test_restores_original_path_and_keeps_user_query(self):
        status, body = self.invoke('__tse_path=%2Fschools%2Fbangalore&q=primary')

        self.assertEqual(status, '200 OK')
        self.assertEqual(body, b'ok')
        self.assertEqual(self.seen, ('', '/schools/bangalore', 'q=primary'))

    def test_restores_root_path(self):
        self.invoke('__tse_path=%2F')

        self.assertEqual(self.seen, ('', '/', ''))

    def test_rejects_non_rooted_path(self):
        status, body = self.invoke('__tse_path=//outside')

        self.assertEqual(status, '400 Bad Request')
        self.assertEqual(body, b'Invalid routed path')
        self.assertIsNone(self.seen)


if __name__ == '__main__':
    unittest.main()
