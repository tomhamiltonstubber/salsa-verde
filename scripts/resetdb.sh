#!/usr/bin/env bash
set -e

psql -h localhost -U postgres -c "DROP DATABASE salsaverde"
psql -h localhost -U postgres -c "CREATE DATABASE salsaverde"
