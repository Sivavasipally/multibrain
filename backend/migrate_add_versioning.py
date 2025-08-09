#!/usr/bin/env python3
"""
Database Migration Script for Context Versioning System

This script adds the context versioning tables to an existing RAG Chatbot database.
It creates the necessary tables and indexes for the enhanced versioning system
while preserving all existing data.

Tables Added:
- context_versions: Enhanced version snapshots with full state preservation
- context_version_diffs: Detailed change tracking between versions
- version_tags: Named tags for important versions

Features:
- Safe migration with rollback capability
- Preserves all existing data
- Adds indexes for optimal performance
- Creates initial versions for existing contexts

Usage:
    python migrate_add_versioning.py [--test] [--rollback]
    
Options:
    --test: Run in test mode (no changes made)
    --rollback: Rollback the migration (drop new tables)
    
Environment Variables:
    DATABASE_URL: Database connection string (default: SQLite)
    
Author: RAG Chatbot Development Team
Version: 1.0.0
"""

import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import Flask and database components
from flask import Flask

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from database import db, Context, User
from context_versioning import ContextVersion, ContextVersionDiff, VersionTag, ContextVersionService

# Try to import logging config, fallback to basic logging
try:
    from logging_config import setup_logging, get_logger
except ImportError:
    import logging
    def setup_logging(**kwargs):
        logging.basicConfig(level=logging.INFO)
    def get_logger(name):
        return logging.getLogger(name)

# Initialize logging
logger = get_logger('migration')

def create_app():
    """Create Flask app for migration"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'migration-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ragchatbot.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def create_versioning_tables():
    """Create the new versioning tables"""
    logger.info("Creating context versioning tables...")
    
    try:
        # Create all versioning tables
        db.create_all()
        logger.info("Successfully created versioning tables")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create versioning tables: {e}")
        return False

def create_initial_versions():
    """Create initial versions for existing contexts"""
    logger.info("Creating initial versions for existing contexts...")
    
    try:
        contexts = Context.query.all()
        created_versions = 0
        
        for context in contexts:
            try:
                # Check if context already has versions
                existing_version = ContextVersion.query.filter_by(context_id=context.id).first()
                if existing_version:
                    logger.info(f"Context {context.id} already has versions, skipping")
                    continue
                
                # Create initial version for context
                version = ContextVersionService.create_version(
                    context=context,
                    user_id=context.user_id,
                    description=f"Initial version created during migration",
                    version_type='auto'
                )
                
                created_versions += 1
                logger.info(f"Created initial version {version.version_number} for context {context.id}: {context.name}")
                
            except Exception as e:
                logger.error(f"Failed to create initial version for context {context.id}: {e}")
                continue
        
        db.session.commit()
        logger.info(f"Successfully created {created_versions} initial versions")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create initial versions: {e}")
        db.session.rollback()
        return False

def verify_migration():
    """Verify that the migration was successful"""
    logger.info("Verifying migration...")
    
    try:
        # Check that versioning tables exist and are accessible
        version_count = ContextVersion.query.count()
        diff_count = ContextVersionDiff.query.count()
        tag_count = VersionTag.query.count()
        
        logger.info(f"Migration verification successful:")
        logger.info(f"  - Context versions: {version_count}")
        logger.info(f"  - Version diffs: {diff_count}")
        logger.info(f"  - Version tags: {tag_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration verification failed: {e}")
        return False

def rollback_migration():
    """Rollback the migration by dropping versioning tables"""
    logger.info("Rolling back context versioning migration...")
    
    try:
        # Drop versioning tables in correct order (foreign key dependencies)
        db.engine.execute("DROP TABLE IF EXISTS version_tags")
        db.engine.execute("DROP TABLE IF EXISTS context_version_diffs") 
        db.engine.execute("DROP TABLE IF EXISTS context_versions")
        
        logger.info("Successfully rolled back versioning migration")
        return True
        
    except Exception as e:
        logger.error(f"Failed to rollback migration: {e}")
        return False

def main():
    """Main migration function"""
    parser = argparse.ArgumentParser(description='Migrate database to add context versioning')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no changes)')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    args = parser.parse_args()
    
    # Initialize logging
    setup_logging(
        log_level=os.getenv('LOG_LEVEL', 'INFO'),
        console_output=True,
        json_format=False
    )
    
    logger.info("Starting context versioning migration...")
    logger.info(f"Database URL: {os.getenv('DATABASE_URL', 'sqlite:///ragchatbot.db')}")
    logger.info(f"Test mode: {args.test}")
    logger.info(f"Rollback mode: {args.rollback}")
    
    # Create Flask app and push application context
    app = create_app()
    
    with app.app_context():
        if args.rollback:
            # Rollback migration
            if args.test:
                logger.info("TEST MODE: Would rollback versioning migration")
                return 0
            
            if rollback_migration():
                logger.info("Migration rollback completed successfully")
                return 0
            else:
                logger.error("Migration rollback failed")
                return 1
        
        else:
            # Forward migration
            if args.test:
                logger.info("TEST MODE: Would create versioning tables and initial versions")
                return 0
            
            # Create versioning tables
            if not create_versioning_tables():
                logger.error("Failed to create versioning tables")
                return 1
            
            # Create initial versions for existing contexts
            if not create_initial_versions():
                logger.error("Failed to create initial versions")
                return 1
            
            # Verify migration
            if not verify_migration():
                logger.error("Migration verification failed")
                return 1
            
            logger.info("Context versioning migration completed successfully!")
            logger.info("The system now supports comprehensive version management for contexts.")
            return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)