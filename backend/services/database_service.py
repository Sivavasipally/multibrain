"""
Database connection service for multiple database types
"""

import sqlite3
import pymongo
import pandas as pd
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text, inspect
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

class DatabaseService:
    """Service for connecting to various database types"""
    
    def __init__(self):
        self.supported_types = ['sqlite', 'mysql', 'postgresql', 'oracle', 'mongodb', 'cassandra']
    
    def test_connection(self, db_type: str, connection_string: str) -> Dict[str, Any]:
        """Test database connection"""
        try:
            if db_type in ['sqlite', 'mysql', 'postgresql', 'oracle']:
                return self._test_sql_connection(db_type, connection_string)
            elif db_type == 'mongodb':
                return self._test_mongodb_connection(connection_string)
            elif db_type == 'cassandra':
                return self._test_cassandra_connection(connection_string)
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_schema_info(self, db_type: str, connection_string: str) -> Dict[str, Any]:
        """Get database schema information"""
        try:
            if db_type in ['sqlite', 'mysql', 'postgresql', 'oracle']:
                return self._get_sql_schema(db_type, connection_string)
            elif db_type == 'mongodb':
                return self._get_mongodb_schema(connection_string)
            elif db_type == 'cassandra':
                return self._get_cassandra_schema(connection_string)
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def extract_table_data(self, db_type: str, connection_string: str, table_name: str, 
                          limit: Optional[int] = 1000) -> pd.DataFrame:
        """Extract data from a specific table"""
        if db_type in ['sqlite', 'mysql', 'postgresql', 'oracle']:
            return self._extract_sql_table_data(db_type, connection_string, table_name, limit)
        elif db_type == 'mongodb':
            return self._extract_mongodb_collection_data(connection_string, table_name, limit)
        elif db_type == 'cassandra':
            return self._extract_cassandra_table_data(connection_string, table_name, limit)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def execute_query(self, db_type: str, connection_string: str, query: str) -> pd.DataFrame:
        """Execute custom query and return results"""
        if db_type in ['sqlite', 'mysql', 'postgresql', 'oracle']:
            return self._execute_sql_query(db_type, connection_string, query)
        elif db_type == 'mongodb':
            # MongoDB queries would need to be in MongoDB query format
            raise NotImplementedError("Custom MongoDB queries not implemented")
        elif db_type == 'cassandra':
            return self._execute_cassandra_query(connection_string, query)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def _test_sql_connection(self, db_type: str, connection_string: str) -> Dict[str, Any]:
        """Test SQL database connection"""
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        return {
            'success': True,
            'message': f'Successfully connected to {db_type} database'
        }
    
    def _test_mongodb_connection(self, connection_string: str) -> Dict[str, Any]:
        """Test MongoDB connection"""
        client = pymongo.MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        client.server_info()  # Will raise exception if connection fails
        client.close()
        
        return {
            'success': True,
            'message': 'Successfully connected to MongoDB'
        }
    
    def _test_cassandra_connection(self, connection_string: str) -> Dict[str, Any]:
        """Test Cassandra connection"""
        # Parse connection string (simplified)
        # Format: cassandra://username:password@host:port/keyspace
        parts = connection_string.replace('cassandra://', '').split('@')
        if len(parts) == 2:
            auth_part, host_part = parts
            username, password = auth_part.split(':')
            auth_provider = PlainTextAuthProvider(username=username, password=password)
        else:
            host_part = parts[0]
            auth_provider = None
        
        host, port_keyspace = host_part.split(':')
        port, keyspace = port_keyspace.split('/')
        
        cluster = Cluster([host], port=int(port), auth_provider=auth_provider)
        session = cluster.connect()
        session.shutdown()
        cluster.shutdown()
        
        return {
            'success': True,
            'message': 'Successfully connected to Cassandra'
        }
    
    def _get_sql_schema(self, db_type: str, connection_string: str) -> Dict[str, Any]:
        """Get SQL database schema"""
        engine = create_engine(connection_string)
        inspector = inspect(engine)
        
        tables = []
        for table_name in inspector.get_table_names():
            columns = []
            for column in inspector.get_columns(table_name):
                columns.append({
                    'name': column['name'],
                    'type': str(column['type']),
                    'nullable': column['nullable'],
                    'default': column.get('default')
                })
            
            tables.append({
                'name': table_name,
                'columns': columns,
                'row_count': self._get_table_row_count(engine, table_name)
            })
        
        return {
            'success': True,
            'database_type': db_type,
            'tables': tables
        }
    
    def _get_mongodb_schema(self, connection_string: str) -> Dict[str, Any]:
        """Get MongoDB schema"""
        client = pymongo.MongoClient(connection_string)
        db_name = connection_string.split('/')[-1]
        db = client[db_name]
        
        collections = []
        for collection_name in db.list_collection_names():
            collection = db[collection_name]
            
            # Sample documents to infer schema
            sample_docs = list(collection.find().limit(100))
            fields = set()
            
            for doc in sample_docs:
                fields.update(doc.keys())
            
            collections.append({
                'name': collection_name,
                'fields': list(fields),
                'document_count': collection.count_documents({})
            })
        
        client.close()
        
        return {
            'success': True,
            'database_type': 'mongodb',
            'collections': collections
        }
    
    def _get_cassandra_schema(self, connection_string: str) -> Dict[str, Any]:
        """Get Cassandra schema"""
        # Parse connection and connect
        parts = connection_string.replace('cassandra://', '').split('@')
        if len(parts) == 2:
            auth_part, host_part = parts
            username, password = auth_part.split(':')
            auth_provider = PlainTextAuthProvider(username=username, password=password)
        else:
            host_part = parts[0]
            auth_provider = None
        
        host, port_keyspace = host_part.split(':')
        port, keyspace = port_keyspace.split('/')
        
        cluster = Cluster([host], port=int(port), auth_provider=auth_provider)
        session = cluster.connect(keyspace)
        
        # Get tables
        tables = []
        rows = session.execute("SELECT table_name FROM system_schema.tables WHERE keyspace_name = %s", [keyspace])
        
        for row in rows:
            table_name = row.table_name
            
            # Get columns
            columns = []
            col_rows = session.execute(
                "SELECT column_name, type FROM system_schema.columns WHERE keyspace_name = %s AND table_name = %s",
                [keyspace, table_name]
            )
            
            for col_row in col_rows:
                columns.append({
                    'name': col_row.column_name,
                    'type': col_row.type
                })
            
            tables.append({
                'name': table_name,
                'columns': columns
            })
        
        session.shutdown()
        cluster.shutdown()
        
        return {
            'success': True,
            'database_type': 'cassandra',
            'keyspace': keyspace,
            'tables': tables
        }
    
    def _get_table_row_count(self, engine, table_name: str) -> int:
        """Get row count for SQL table"""
        try:
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                return result.scalar()
        except:
            return 0
    
    def _extract_sql_table_data(self, db_type: str, connection_string: str, 
                               table_name: str, limit: Optional[int] = 1000) -> pd.DataFrame:
        """Extract data from SQL table"""
        engine = create_engine(connection_string)
        
        query = f"SELECT * FROM {table_name}"
        if limit:
            if db_type in ['mysql', 'postgresql']:
                query += f" LIMIT {limit}"
            elif db_type == 'oracle':
                query = f"SELECT * FROM (SELECT * FROM {table_name}) WHERE ROWNUM <= {limit}"
            elif db_type == 'sqlite':
                query += f" LIMIT {limit}"
        
        return pd.read_sql(query, engine)
    
    def _extract_mongodb_collection_data(self, connection_string: str, 
                                       collection_name: str, limit: Optional[int] = 1000) -> pd.DataFrame:
        """Extract data from MongoDB collection"""
        client = pymongo.MongoClient(connection_string)
        db_name = connection_string.split('/')[-1]
        db = client[db_name]
        collection = db[collection_name]
        
        cursor = collection.find()
        if limit:
            cursor = cursor.limit(limit)
        
        documents = list(cursor)
        client.close()
        
        return pd.DataFrame(documents)
    
    def _extract_cassandra_table_data(self, connection_string: str, 
                                    table_name: str, limit: Optional[int] = 1000) -> pd.DataFrame:
        """Extract data from Cassandra table"""
        # Parse connection and connect
        parts = connection_string.replace('cassandra://', '').split('@')
        if len(parts) == 2:
            auth_part, host_part = parts
            username, password = auth_part.split(':')
            auth_provider = PlainTextAuthProvider(username=username, password=password)
        else:
            host_part = parts[0]
            auth_provider = None
        
        host, port_keyspace = host_part.split(':')
        port, keyspace = port_keyspace.split('/')
        
        cluster = Cluster([host], port=int(port), auth_provider=auth_provider)
        session = cluster.connect(keyspace)
        
        query = f"SELECT * FROM {table_name}"
        if limit:
            query += f" LIMIT {limit}"
        
        rows = session.execute(query)
        data = [dict(row._asdict()) for row in rows]
        
        session.shutdown()
        cluster.shutdown()
        
        return pd.DataFrame(data)
    
    def _execute_sql_query(self, db_type: str, connection_string: str, query: str) -> pd.DataFrame:
        """Execute SQL query"""
        engine = create_engine(connection_string)
        return pd.read_sql(query, engine)
    
    def _execute_cassandra_query(self, connection_string: str, query: str) -> pd.DataFrame:
        """Execute Cassandra query"""
        # Similar to extract_cassandra_table_data but with custom query
        parts = connection_string.replace('cassandra://', '').split('@')
        if len(parts) == 2:
            auth_part, host_part = parts
            username, password = auth_part.split(':')
            auth_provider = PlainTextAuthProvider(username=username, password=password)
        else:
            host_part = parts[0]
            auth_provider = None
        
        host, port_keyspace = host_part.split(':')
        port, keyspace = port_keyspace.split('/')
        
        cluster = Cluster([host], port=int(port), auth_provider=auth_provider)
        session = cluster.connect(keyspace)
        
        rows = session.execute(query)
        data = [dict(row._asdict()) for row in rows]
        
        session.shutdown()
        cluster.shutdown()
        
        return pd.DataFrame(data)
