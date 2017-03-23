#!/bin/bash
# -*- coding: utf-8 -*-

pytest \
  "$@" \
  --pep8 \
  --pylint \
  --cov=triscord --cov=tests --cov-report term-missing \
#  --mypy \ FIXME: pylint-mypy being outdated
