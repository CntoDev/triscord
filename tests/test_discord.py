# -*- coding: utf-8 -*-

"""triscord.discord unit tests."""

from unittest.mock import ANY

import requests

from triscord import discord as unit


def test_webhook_message_sending(mocker):
    """Asserts that DiscordWebhook properly formats messages to DiscordApp's API."""

    mocker.patch('requests.post')

    url = "https://dummy.tld/api/webhooks/000000000000000000" \
          "/aaaaaaaaaaaa-aaaaaaaaaaaaaaaaaaa-aaaaaaa-aaaaaaaaaaaaaaaaaaaa_aaaaaa"
    message = "test message"

    webhook = unit.DiscordWebhook(url=url)
    webhook.send_message(message)

    requests.post.assert_called_with(  # pylint:disable=E1101
        url,
        data={'content': message},
        params=ANY,
    )


#  vim: set tabstop=4 shiftwidth=4 expandtab autoindent :
