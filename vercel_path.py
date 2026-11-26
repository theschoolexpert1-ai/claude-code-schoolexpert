from urllib.parse import parse_qsl, urlencode


class VercelPathMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        query = parse_qsl(environ.get('QUERY_STRING', ''), keep_blank_values=True)
        path_index = next((i for i, (key, _) in enumerate(query) if key == '__tse_path'), None)
        if path_index is None:
            return self.app(environ, start_response)

        path = query.pop(path_index)[1]
        if not path.startswith('/') or path.startswith('//'):
            start_response('400 Bad Request', [('Content-Type', 'text/plain; charset=utf-8')])
            return [b'Invalid routed path']

        environ['SCRIPT_NAME'] = ''
        environ['PATH_INFO'] = path
        environ['QUERY_STRING'] = urlencode(query)
        return self.app(environ, start_response)
