#!/bin/env python3
# -*- coding: utf-8 -*-

"""Main entrypoint for triscord."""

import argparse
import logging

import arrow
import requests

from . import discord
from . import persistence
from . import settings
from . import trello

PARSER = argparse.ArgumentParser(
    description="Trello to Discord synchronisation script",
)
PARSER.add_argument(
    '--debug',
    const=True,
    default=False,
    action='store_const',
    help="Set debugging on",
)
PARSER.add_argument(
    '--config-path',
    required=True,
    help="Path of the configuration file",
)
PARSER.add_argument(
    '--persist-path',
    required=True,
    help="Path of the persistence file",
)

LOGGER = logging.getLogger()


def main(config_path, persist_path, debug=False):
    """Main function."""

    if debug:
        LOGGER.setLevel(logging.DEBUG)
    logging.info("Setting debug to %s", debug)

    settings.CONFIG.read(config_path)

    api = trello.TrelloAPI(
        key=settings.CONFIG.get('Trello', 'key'),
        token=settings.CONFIG.get('Trello', 'token'),
    )
    last_update = arrow.now()
    with persistence.persistent_storage(persist_path) as storage:
        if 'last_update' in storage:
            last_update = arrow.get(storage['last_update'])
            logging.info('Last run detected, was on %s', last_update.isoformat())
    try:
        feed = trello.TrelloActivityFeed(
            api,
            board_id=settings.CONFIG.get('Trello', 'board_id'),
            muted_action_types=str(settings.CONFIG.get(
                'Trello',
                'muted_action_types',
                fallback="",
            )).split(','),
            muted_update_fields=str(settings.CONFIG.get(
                'Trello',
                'muted_update_fields',
                fallback="",
            )).split(','),
            last_update=last_update,
        )
        discord_hook = discord.DiscordWebhook(
            url=settings.CONFIG.get(
                'Discord',
                'webhook_url',
            ),
        )

        try:
            feed_actions = list(feed.actions)
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as exc:
            logging.error(exc)
            return
        for action in feed_actions:
            message = feed.format_action(action)
            discord_hook.send_message(message)
        last_update = feed.last_update
    finally:
        with persistence.persistent_storage(persist_path) as storage:
            storage['last_update'] = last_update.isoformat()


def entry_point():
    """Setuptools' CLI entry point."""

    args = PARSER.parse_args()
    LOGGER.setLevel(logging.WARNING)
    main(**args.__dict__)

if __name__ == '__main__':  # pragma: no cover
    entry_point()

#  vim: set tabstop=4 shiftwidth=4 expandtab autoindent :
