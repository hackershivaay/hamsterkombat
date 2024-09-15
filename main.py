import os
import sys

from src.core import main
from src.__init__ import _banner, log, mrh

PORT = int(os.environ.get('PORT', 3001))

if __name__ == "__main__":
    while True:
        try:
            _banner()
            main()
        except KeyboardInterrupt:
            print()
            log(mrh + f"Successfully logged out of the bot\n")
            sys.exit()

    # Start the application on the specified port
    print(f"Starting application on port {PORT}")
