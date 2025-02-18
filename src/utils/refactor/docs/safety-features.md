# Safety Features Guide

This guide details the comprehensive safety features built into the Python Code Refactoring Tool to ensure code integrity and prevent data loss.

## Table of Contents
- [Backup Mechanisms](#backup-mechanisms)
- [Rollback Procedures](#rollback-procedures)
- [Validation Checks](#validation-checks)
- [Syntax Verification](#syntax-verification)
- [Permission Checks](#permission-checks)
- [Error Recovery](#error-recovery)

## Backup Mechanisms

### Automated Backup System

```yaml
backup:
  enabled: true
  frequency: "per_change"  # Options: per_change, per_file, per_module
  retention:
    count: 5              # Keep last 5 backups
    duration: "7d"        # Keep backups for 7 days
  compression: true       # Enable backup compression
  location: ".backups"    # Backup directory
```

### Backup Types

1. **Full Project Backup**
```python
class BackupManager:
    def create_full_backup(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"full_backup_{timestamp}"
        
        # Create compressed archive
        with tarfile.open(f"{backup_path}.tar.gz", "w:gz") as tar:
            tar.add(self.project_dir)
        
        # Record backup metadata
        self._record_backup_metadata(backup_path, "full")
```

2. **Incremental Backup**
```python
def create_incremental_backup(self):
    """Creates backup of only modified files."""
    changed_files = self.get_modified_files()
    if not changed_files:
        return
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = self.backup_dir / f"incr_backup_{timestamp}"
    
    with tarfile.open(f"{backup_path}.tar.gz", "w:gz") as tar:
        for file in changed_files:
            tar.add(file)
```

3. **State Checkpoints**
```python
def create_checkpoint(self, description: str = None):
    """Creates a named checkpoint of current state."""
    checkpoint_id = uuid.uuid4().hex[:8]
    state = {
        'timestamp': datetime.now().isoformat(),
        'description': description,
        'files': self.get_file_checksums(),
        'id': checkpoint_id
    }
    
    self._save_checkpoint_state(checkpoint_id, state)
    return checkpoint_id
```

## Rollback Procedures

### Rollback Configuration

```yaml
rollback:
  enabled: true
  strategies:
    - full          # Complete project rollback
    - incremental   # Rollback specific changes
    - selective     # Rollback selected files
  verification: true  # Verify state after rollback
  auto_backup: true  # Backup before rollback
```

### Rollback Implementation

```python
class RollbackManager:
    def rollback_to_checkpoint(self, checkpoint_id: str):
        """Rollback to a specific checkpoint."""
        try:
            # Verify checkpoint exists
            if not self._verify_checkpoint(checkpoint_id):
                raise CheckpointNotFoundError(checkpoint_id)
            
            # Create safety backup
            if self.config['auto_backup']:
                self.backup_manager.create_full_backup()
            
            # Perform rollback
            checkpoint = self._load_checkpoint(checkpoint_id)
            self._restore_files(checkpoint['files'])
            
            # Verify rollback
            if not self._verify_state(checkpoint):
                raise RollbackVerificationError()
            
            self._record_rollback(checkpoint_id)
            
        except Exception as e:
            self._handle_rollback_error(e)
```

### Selective Rollback

```python
def selective_rollback(self, files: List[Path]):
    """Rollback specific files to their last known good state."""
    for file in files:
        last_good_version = self._find_last_good_version(file)
        if last_good_version:
            shutil.copy2(last_good_version, file)
            self._verify_file_integrity(file)
```

## Validation Checks

### Pre-Refactoring Validation

```python
class ValidationManager:
    def validate_project(self):
        """Comprehensive project validation."""
        checks = [
            self._validate_python_version(),
            self._validate_dependencies(),
            self._validate_file_structure(),
            self._validate_permissions(),
            self._validate_config()
        ]
        
        if not all(checks):
            raise ValidationError("Pre-refactoring validation failed")
```

### Code Quality Checks

```python
def validate_code_quality(self):
    """Validate code quality standards."""
    checks = {
        'syntax': self._check_syntax(),
        'imports': self._validate_imports(),
        'complexity': self._check_complexity(),
        'style': self._check_style_compliance(),
        'types': self._validate_type_hints()
    }
    
    return all(checks.values()), checks
```

### Configuration Validation

```python
def validate_config(self):
    """Validate refactoring configuration."""
    required_fields = {
        'project_name',
        'modules',
        'settings'
    }
    
    # Check required fields
    missing = required_fields - set(self.config.keys())
    if missing:
        raise ConfigValidationError(f"Missing required fields: {missing}")
    
    # Validate module definitions
    for module, config in self.config['modules'].items():
        self._validate_module_config(module, config)
```

## Syntax Verification

### Syntax Checking

```python
class SyntaxVerifier:
    def verify_syntax(self, file_path: Path) -> bool:
        """Verify Python syntax of a file."""
        try:
            with tokenize.open(file_path) as f:
                tokens = list(tokenize.generate_tokens(f.readline))
                
            ast.parse(file_path.read_text())
            return True
            
        except (SyntaxError, tokenize.TokenError) as e:
            self._log_syntax_error(file_path, e)
            return False
```

### AST Validation

```python
def validate_ast(self, source_code: str) -> bool:
    """Validate Abstract Syntax Tree integrity."""
    try:
        tree = ast.parse(source_code)
        for node in ast.walk(tree):
            # Validate node structure
            if not self._validate_node(node):
                return False
                
            # Check for common AST issues
            if not self._check_node_integrity(node):
                return False
                
        return True
        
    except Exception as e:
        self._log_ast_error(e)
        return False
```

## Permission Checks

### File System Permissions

```python
class PermissionChecker:
    def check_permissions(self):
        """Verify all required permissions."""
        required_checks = [
            self._check_read_permissions(),
            self._check_write_permissions(),
            self._check_execute_permissions(),
            self._check_directory_permissions()
        ]
        
        return all(required_checks)
    
    def _check_write_permissions(self):
        """Check write permissions for output directory."""
        try:
            test_file = self.output_dir / '.permission_test'
            test_file.touch()
            test_file.unlink()
            return True
        except (PermissionError, OSError):
            return False
```

### Directory Permissions

```python
def verify_directory_permissions(self):
    """Verify permissions for all required directories."""
    directories = {
        'source': self.source_dir,
        'output': self.output_dir,
        'backup': self.backup_dir,
        'temp': self.temp_dir
    }
    
    for name, path in directories.items():
        if not self._verify_directory_access(path):
            raise PermissionError(
                f"Insufficient permissions for {name} directory: {path}"
            )
```

## Error Recovery

### Recovery Strategies

```python
class ErrorRecovery:
    def handle_error(self, error: Exception):
        """Handle errors during refactoring."""
        try:
            # Log error details
            self._log_error(error)
            
            # Determine recovery strategy
            strategy = self._determine_recovery_strategy(error)
            
            # Execute recovery
            if strategy == 'rollback':
                self._perform_rollback()
            elif strategy == 'retry':
                self._retry_operation()
            elif strategy == 'skip':
                self._skip_problematic_section()
            else:
                self._emergency_stop()
                
        except Exception as recovery_error:
            # Handle recovery failure
            self._handle_recovery_failure(error, recovery_error)
```

### Automated Recovery

```python
def auto_recover(self):
    """Attempt automatic recovery from errors."""
    recovery_steps = [
        self._restore_last_known_good_state,
        self._clean_temporary_files,
        self._verify_project_state,
        self._rebuild_project_structure,
        self._reapply_changes
    ]
    
    for step in recovery_steps:
        try:
            step()
        except Exception as e:
            self._log_recovery_failure(step.__name__, e)
            return False
    
    return True
```

### Recovery Logging

```python
def log_recovery_attempt(self):
    """Log recovery attempt details."""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'error_type': self.error.__class__.__name__,
        'error_message': str(self.error),
        'recovery_strategy': self.strategy,
        'affected_files': self.affected_files,
        'recovery_status': self.status
    }
    
    self._write_recovery_log(log_entry)
```

---

This guide provides a comprehensive overview of the safety features implemented in the refactoring tool. Each section includes detailed examples and implementations of various safety mechanisms to ensure code integrity and prevent data loss during the refactoring process.
