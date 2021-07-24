# Algorithms

## Overview

This directory contains code for the running the recommender algorithms server. This server has been
separated from the main server to isolate large dependencies. The `/preferences` endpoint
accepts a series of ratings and outputs preference predictions. See `tests/test_ratings.json` for
example ratings schema.

## Usage

To run the server, start by installing all the dependencies.

| Algorithms  |  src/algs/lenskit.yml |
| Server      |  requirements.txt     |
| Testing     |  requirements.txt     |

Then configure `src/config.json` and start the server with `python src/app.py`.

