# A trimmed copy of what html.duckduckgo.com/html/ answers, with the cases the parser must
# handle: a direct result, one sent through the uddg redirect, an advertisement, a repeat.

DUCKDUCKGO_PAGE = """<!DOCTYPE html>
<html><head><title>pytest parametrize at DuckDuckGo</title></head>
<body>
  <div id="links" class="results">
    <div class="result results_links results_links_deep result--ad">
      <div class="links_main links_deep result__body">
        <h2 class="result__title">
          <a rel="nofollow" class="result__a" href="https://duckduckgo.com/y.js?ad_domain=ads.example&amp;u3=x">Buy test tools</a>
        </h2>
        <a class="result__snippet" href="https://duckduckgo.com/y.js?ad_domain=ads.example">Sponsored.</a>
      </div>
    </div>
    <div class="result results_links results_links_deep web-result ">
      <div class="links_main links_deep result__body">
        <h2 class="result__title">
          <a rel="nofollow" class="result__a" href="https://docs.pytest.org/en/stable/how-to/parametrize.html">How to parametrize fixtures and test functions - pytest documentation</a>
        </h2>
        <a class="result__url" href="https://docs.pytest.org/en/stable/how-to/parametrize.html">docs.pytest.org/en/stable/how-to/parametrize.html</a>
        <a class="result__snippet" href="https://docs.pytest.org/en/stable/how-to/parametrize.html"><b>pytest</b> enables test   parametrization at several levels &amp; more.</a>
      </div>
    </div>
    <div class="result results_links results_links_deep web-result ">
      <div class="links_main links_deep result__body">
        <h2 class="result__title">
          <a rel="nofollow" class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.org%2Fguide%3Fa%3D1&amp;rut=abc">A guide to <b>parametrize</b></a>
        </h2>
        <a class="result__snippet" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.org%2Fguide%3Fa%3D1">A wrapped result.</a>
      </div>
    </div>
    <div class="result results_links results_links_deep web-result ">
      <div class="links_main links_deep result__body">
        <h2 class="result__title">
          <a rel="nofollow" class="result__a" href="https://docs.pytest.org/en/stable/how-to/parametrize.html">How to parametrize (again)</a>
        </h2>
        <a class="result__snippet" href="https://docs.pytest.org/en/stable/how-to/parametrize.html">The same page twice.</a>
      </div>
    </div>
    <div class="nav-link"><form action="/html/" method="post"><input type="submit" value="Next" /></form></div>
  </div>
</body></html>"""

DUCKDUCKGO_CHALLENGE_PAGE = """<!DOCTYPE html>
<html><body><div class="anomaly-modal__title">Unfortunately, bots use DuckDuckGo too.</div>
<form id="challenge-form" action="/anomaly.js"></form></body></html>"""
