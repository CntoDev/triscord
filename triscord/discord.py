# -*- coding: utf-8 -*-

"""Discord-related operations module."""

import logging

import requests


class DiscordWebhook(object):  # pylint: disable=R0903
    """Discord webhook-based interaction class."""

    def __init__(self, url):
        self.url = url

    def send_message(self, message):
        """Send a message through the Discord webhook.

        See https://discordapp.com/developers/docs/resources/webhook#execute-webhook
        """

        logging.debug("DiscordWebhook.send_message(%s)", message)
        response = requests.post(
            self.url,
            params={
                'wait': True,
            },
            data={
                'content': message,
            },
        )
        response.raise_for_status()
        return response.json()

#  vim: set tabstop=4 shiftwidth=4 expandtab autoindent :
