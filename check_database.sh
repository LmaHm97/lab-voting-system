#!/bin/bash
# Database Persistence Check Script
# Run this script to verify the database is accessible and contains data

DB_PATH="/home/ubuntu/lab_voting_backend/data/voting.db"

echo "=== Database Persistence Check ==="
echo "Date: $(date)"
echo "Database Path: $DB_PATH"
echo ""

if [ -f "$DB_PATH" ]; then
    echo "✅ Database file exists"
    echo "Size: $(du -h $DB_PATH | cut -f1)"
    echo "Last modified: $(stat -c %y $DB_PATH)"
    echo ""
    echo "=== Database Contents ==="
    echo "Total presentations:"
    sqlite3 $DB_PATH "SELECT COUNT(*) FROM presentations;"
    echo ""
    echo "Total votes:"
    sqlite3 $DB_PATH "SELECT COUNT(*) FROM votes;"
    echo ""
    echo "Total weeks:"
    sqlite3 $DB_PATH "SELECT COUNT(*) FROM weeks;"
    echo ""
    echo "Recent presentations:"
    sqlite3 $DB_PATH "SELECT title, presenter, votes, created_at FROM presentations ORDER BY created_at DESC LIMIT 5;" -header -column
else
    echo "❌ Database file not found at $DB_PATH"
fi
