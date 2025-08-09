# Context Versioning System Documentation

## Overview

The Context Versioning System provides comprehensive version management for knowledge bases (contexts) in the RAG Chatbot PWA. This system enables users to track changes, create snapshots, compare versions, and restore previous states of their knowledge bases.

## Key Features

### 🔄 **Automatic Version Creation**
- Automatic versions created after document processing
- Smart version numbering (semantic versioning)
- Impact-based major/minor version determination
- Processing statistics tracking

### 📝 **Manual Version Management**
- User-created manual versions with descriptions
- Milestone and backup version types
- Version tagging and categorization
- Custom change tracking

### 🔍 **Version Comparison**
- Detailed diff analysis between versions
- Statistical comparisons (documents, chunks, tokens)
- Configuration change tracking
- Document addition/removal detection

### 🔒 **Data Integrity**
- SHA-256 content hash verification
- Integrity checks before restore operations
- Complete state snapshot preservation
- Atomic rollback operations

### 🏷️ **Version Organization**
- Named tags for important versions
- Color-coded categorization
- Search and filtering capabilities
- Version protection from deletion

## Architecture

### Database Models

#### ContextVersion
The core model storing complete version snapshots:

```python
class ContextVersion(db.Model):
    # Core identification
    id = Column(Integer, primary_key=True)
    context_id = Column(Integer, ForeignKey('contexts.id'))
    version_number = Column(String(20))  # e.g., "1.0", "1.1", "2.0"
    version_type = Column(String(20))    # auto, manual, milestone, backup, rollback
    content_hash = Column(String(64))    # SHA-256 integrity hash
    
    # Complete state snapshots
    config_snapshot = Column(Text)       # JSON context configuration
    documents_snapshot = Column(Text)    # JSON documents metadata
    processing_snapshot = Column(Text)   # JSON processing state
    
    # Statistics and metadata
    total_chunks = Column(Integer)
    total_tokens = Column(Integer)
    total_documents = Column(Integer)
    status = Column(String(50))
    is_current = Column(Boolean)
    is_protected = Column(Boolean)
```

#### ContextVersionDiff
Detailed change tracking between versions:

```python
class ContextVersionDiff(db.Model):
    version_id = Column(Integer, ForeignKey('context_versions.id'))
    previous_version_id = Column(Integer, ForeignKey('context_versions.id'))
    change_type = Column(String(50))      # config, document, processing
    change_operation = Column(String(20)) # added, removed, modified
    change_data = Column(Text)            # JSON specific changes
    impact_score = Column(Integer)        # 1-10 impact scale
```

#### VersionTag
Named tags for version organization:

```python
class VersionTag(db.Model):
    version_id = Column(Integer, ForeignKey('context_versions.id'))
    tag_name = Column(String(100))
    tag_description = Column(Text)
    tag_type = Column(String(50))    # user, system, milestone, release
    tag_color = Column(String(7))    # Hex color for UI
```

### Service Layer

#### ContextVersionService
Business logic for version management:

```python
class ContextVersionService:
    @staticmethod
    def create_version(context, user_id, description, version_type='auto', 
                      changes=None, force_major=False) -> ContextVersion
    
    @staticmethod
    def restore_version(context_id, version_id, user_id) -> ContextVersion
    
    @staticmethod
    def compare_versions(version1_id, version2_id) -> Dict[str, Any]
    
    @staticmethod
    def get_version_history(context_id, limit=50) -> List[ContextVersion]
```

## API Endpoints

### Version Management

#### `GET /api/contexts/{id}/versions`
Get version history for a context.

**Query Parameters:**
- `limit`: Maximum versions to return (default: 20, max: 100)
- `offset`: Number of versions to skip
- `version_type`: Filter by type (auto, manual, milestone)
- `include_snapshots`: Include full snapshot data

**Response:**
```json
{
  "versions": [
    {
      "id": 123,
      "version_number": "1.2",
      "version_type": "auto",
      "description": "Auto-version after processing 3 documents",
      "created_at": "2024-01-15T10:30:00Z",
      "total_documents": 15,
      "total_chunks": 450,
      "total_tokens": 12000,
      "integrity_verified": true,
      "is_current": true,
      "tags": [
        {
          "tag_name": "stable",
          "tag_type": "milestone",
          "tag_color": "#28a745"
        }
      ]
    }
  ],
  "pagination": {
    "total": 5,
    "has_more": false
  }
}
```

#### `POST /api/contexts/{id}/versions`
Create a new manual version.

**Request Body:**
```json
{
  "description": "Before major refactoring",
  "version_type": "milestone",
  "force_major": false,
  "tags": [
    {
      "tag_name": "pre-refactor",
      "tag_description": "Version before major code refactoring",
      "tag_type": "milestone",
      "tag_color": "#ffc107"
    }
  ],
  "changes": {
    "config_change": {
      "operation": "modified",
      "description": "Updated chunking strategy",
      "impact_score": 7
    }
  }
}
```

#### `GET /api/versions/{id}`
Get detailed version information.

**Query Parameters:**
- `include_snapshots`: Include full snapshot data
- `include_diffs`: Include change diffs

#### `POST /api/versions/{id}/restore`
Restore context to a specific version.

**Request Body:**
```json
{
  "confirm": true,
  "backup_description": "Backup before restore to v1.0"
}
```

#### `GET /api/versions/{id1}/compare/{id2}`
Compare two versions.

**Response:**
```json
{
  "version_info": {
    "version1": { "id": 123, "number": "1.0" },
    "version2": { "id": 124, "number": "1.1" }
  },
  "statistics_comparison": {
    "documents": { "version1": 10, "version2": 13, "difference": 3 },
    "chunks": { "version1": 250, "version2": 400, "difference": 150 }
  },
  "document_changes": {
    "added_documents": [15, 16, 17],
    "removed_documents": [],
    "document_count_change": 3
  }
}
```

### Version Organization

#### `POST /api/versions/{id}/tags`
Add a tag to a version.

#### `DELETE /api/versions/{id}`
Delete a version (with protection checks).

## Integration Points

### Automatic Versioning

Automatic versions are created at key points:

1. **After Document Processing** (upload.py):
```python
# In process_uploaded_documents()
version = ContextVersionService.create_version(
    context=context,
    user_id=context.user_id,
    description=f"Auto-version after processing {processed_documents} documents",
    version_type='auto',
    changes=changes,
    force_major=processed_documents >= 5
)
```

2. **Configuration Changes**:
```python
# When context configuration is updated
changes = {
    'config_change': {
        'operation': 'modified',
        'description': 'Updated embedding model',
        'impact_score': 8
    }
}
```

3. **Manual Snapshots**:
```python
# User-initiated version creation
version = ContextVersionService.create_version(
    context=context,
    user_id=user_id,
    description="Before major changes",
    version_type='milestone'
)
```

### Database Migration

The versioning system requires database migration:

```bash
# Initialize database with versioning tables
python init_database.py

# Or run the migration script
python migrate_add_versioning.py
```

## Usage Examples

### Creating Manual Versions

```bash
# Create a milestone version
curl -X POST "/api/contexts/123/versions" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "description": "Stable version with all documentation",
       "version_type": "milestone",
       "tags": [
         {
           "tag_name": "v1.0-stable",
           "tag_type": "release",
           "tag_color": "#28a745"
         }
       ]
     }'
```

### Version Comparison

```bash
# Compare two versions
curl -X GET "/api/versions/123/compare/124" \
     -H "Authorization: Bearer <token>"
```

### Restoring Versions

```bash
# Restore to previous version
curl -X POST "/api/versions/123/restore" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"confirm": true}'
```

## Version Numbering

The system uses semantic versioning:

- **Major versions** (1.0 → 2.0): Breaking changes or significant updates
  - 5+ documents added at once
  - 1000+ chunks created
  - Configuration changes
  - Embedding model changes

- **Minor versions** (1.0 → 1.1): Incremental updates
  - Small document additions
  - Minor configuration tweaks
  - Regular processing updates

## Best Practices

### 1. Version Management
- Create manual versions before major changes
- Use descriptive version descriptions
- Tag important versions with meaningful names
- Regular cleanup of old, unprotected versions

### 2. Performance Optimization
- Limit version history size for large contexts
- Use snapshots sparingly for frequently updated contexts
- Monitor storage usage for version data

### 3. Security Considerations
- Versions contain complete context snapshots
- Ensure proper access control for version operations
- Consider data retention policies for old versions

### 4. Monitoring and Maintenance
- Monitor version creation frequency
- Check integrity of important versions regularly
- Set up alerts for version system failures

## Troubleshooting

### Common Issues

#### 1. Version Creation Failures
```python
# Check for missing dependencies
try:
    from models.context_version import ContextVersionService
except ImportError:
    # Version models not imported
```

#### 2. Integrity Check Failures
```python
# Verify version integrity
version = ContextVersion.query.get(version_id)
if not version.verify_integrity():
    # Version data corrupted
```

#### 3. Restore Operation Issues
- Ensure version integrity before restore
- Check user permissions for context
- Verify target version exists and is accessible

### Debugging

Enable debug logging:
```python
import logging
logging.getLogger('context_version').setLevel(logging.DEBUG)
logging.getLogger('version_routes').setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features
1. **Branch Management**: Support for branching and merging contexts
2. **Selective Restore**: Restore only specific aspects of a version
3. **Version Scheduling**: Automated version creation schedules
4. **Export/Import**: Version export for backup and migration
5. **Advanced Comparison**: Visual diff tools for version comparison

### API Extensions
1. **Bulk Operations**: Batch version operations
2. **Version Search**: Full-text search across version history
3. **Analytics**: Version usage and performance analytics
4. **Webhooks**: Event notifications for version operations

## Conclusion

The Context Versioning System provides comprehensive version management for RAG knowledge bases, enabling safe experimentation, change tracking, and reliable rollback capabilities. The system integrates seamlessly with existing workflows while providing powerful tools for managing complex knowledge base evolution.