#!/usr/bin/env python
"""Seed an admin user into MongoDB.

Usage:
  python scripts/seed_admin.py --username admin --password changeme --client-id default

This script is safe to run multiple times; it will not overwrite an existing user with the same username.
"""
import argparse
import os
from dotenv import load_dotenv

load_dotenv()

from backend.services.db import get_db
from backend.services.auth import get_password_hash


def seed_admin(username: str, password: str, client_id: str):
    db = get_db()
    users = db.get_collection("users")

    existing = users.find_one({"username": username})
    if existing:
        print(f"User '{username}' already exists (id={existing.get('_id')}). No changes made.")
        return

    hashed = get_password_hash(password)
    doc = {
        "username": username,
        "password_hash": hashed,
        "role": "admin",
        "client_id": client_id,
    }

    res = users.insert_one(doc)
    print(f"Created admin user '{username}' with id: {res.inserted_id}")


def main():
    parser = argparse.ArgumentParser(description="Seed admin user into MongoDB")
    parser.add_argument("--username", default="admin", help="Admin username")
    parser.add_argument("--password", required=True, help="Admin password (choose a strong password)")
    parser.add_argument("--client-id", default="default", help="Client/tenant id to associate with this admin")

    args = parser.parse_args()
    seed_admin(args.username, args.password, args.client_id)


if __name__ == "__main__":
    main()
