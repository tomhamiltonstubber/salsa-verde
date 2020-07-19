#!/usr/bin/env bash
set -e

psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS salsaverde"
psql -h localhost -U postgres -c "CREATE DATABASE salsaverde"
