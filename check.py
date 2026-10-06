"""Run with local Python 3: python check.py [blocking|detection]."""
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "blocking"
    if mode not in ("blocking", "detection"):
        raise SystemExit("Usage: python check.py [blocking|detection]")
    cases = [
        ("Normal search", {"q": "laptop"}, 200),
        ("Custom rule", {"message": "waf-test"}, 403),
        ("SQL injection pattern", {"q": "1' OR '1'='1' -- "}, 403),
        ("XSS pattern", {"q": "<script>alert(1)</script>"}, 403),
    ]
    failures = 0
    for name, params, expected in cases:
        if mode == "detection":
            expected = 200
        url = "http://waf:8080/api/search?" + urlencode(params)
        try:
            with urlopen(url, timeout=10) as response:
                actual = response.status
        except HTTPError as error:
            actual = error.code
            error.close()
        except URLError as error:
            raise SystemExit(f"Cannot reach the lab: {error}. Start Docker Compose first.")
        passed = actual == expected
        failures += not passed
        print(f"{'PASS' if passed else 'FAIL'}: {name}: HTTP {actual}, expected {expected}")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()

