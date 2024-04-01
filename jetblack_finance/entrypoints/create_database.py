"""Entry point for creating the database"""

import logging

from jetblack_finance.db.builder.create import start


def main():
    start()
    logging.shutdown()


if __name__ == '__main__':
    main()
