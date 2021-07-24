# Algorithms

## Overview

This directory contains code for the running the recommender algorithms server. This server has been
separated from the main server to isolate large dependencies. The `/preferences` endpoint
accepts a series of ratings and outputs preference predictions. See `tests/test_ratings.json` for
example ratings schema.

## Usage

Start by installing all the dependencies (it is recommended to use `conda`):


|    Type     |        Location       |
|-------------|-----------------------|
| Algorithms  |  src/algs/lenskit.yml |
| Server      |  requirements.txt     |
| Testing     |  requirements.txt     |

Then configure `src/config.json` 
and finally start the server with `python src/app.py`. 



