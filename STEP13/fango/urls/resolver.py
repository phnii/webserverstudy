from typing import Callable

from fango.http.request import HTTPRequest
from fango.http.response import HTTPResponse
from fango.views.static import static
from urls import url_patterns

class URLResolver:
    def resolve(self, request: HTTPRequest) -> Callable[[HTTPRequest], HTTPResponse]:
        """
        URL解決を行う
        pathにマッチするurlパターンが存在した場合は対応するviewを返す
        存在しなかった場合はNoneを返す
        """
        for url_pattern in url_patterns:
            match = url_pattern.match(request.path)
            if match:
                request.params.update(match.groupdict())
                return url_pattern.view

        return static