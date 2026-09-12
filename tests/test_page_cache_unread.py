from page_cache import classify_body


def test_bot_challenge_is_not_read():
    assert classify_body(
        "<html>Checking your browser before accessing... Cloudflare</html>",
        200) == "blocked"


def test_stub_is_not_read():
    assert classify_body("<html><body>ok</body></html>", 200) == "stub"


def test_pdf_bytes_are_not_read():
    assert classify_body("%PDF-1.7 binary...", 200) == "pdf"


def test_js_shell_is_not_read():
    body = ("<html><head><script src='app.js'></script></head>"
             "<body><div id='root'></div></body></html>") + " " * 2000
    assert classify_body(body, 200) == "js-shell"


def test_real_page_is_verified():
    body = ("<html><body>"
            + "Pip Care announced a total Series A raise of $5 million. " * 40
            + "</body></html>")
    assert classify_body(body, 200) == "verified"
