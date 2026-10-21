"""Command line: python -m webport build | single | serve"""

from __future__ import annotations

import argparse
import functools
import http.server
from pathlib import Path

from .build import DOCS, ROOT, build, build_single_file


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="webport", description="Build the résumé site.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="render the site into docs/")
    single = sub.add_parser("single", help="render one self-contained HTML file")
    single.add_argument("--out", default=str(ROOT / "dist" / "bhushan-ladde.html"))
    serve = sub.add_parser("serve", help="build, then preview at http://localhost:PORT")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    if args.cmd == "build":
        print(f"Built {build()}")
    elif args.cmd == "single":
        print(f"Built {build_single_file(Path(args.out))}")
    elif args.cmd == "serve":
        build()
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DOCS))
        with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as httpd:
            print(f"Serving docs/ at http://localhost:{args.port}  (Ctrl+C to stop)")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                pass


if __name__ == "__main__":
    main()
