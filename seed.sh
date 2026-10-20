#!/bin/sh
set -e

python3 manage.py seed
python3 manage.py seed_members
python3 manage.py seed_plans
python3 manage.py seed_memberships
python3 manage.py seed_payments
python3 manage.py seed_attendance
