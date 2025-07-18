# Database Migration Fix - Detailed Steps

## Current Problem Analysis
- Database logs show old migrations still running (DROP INDEX ix_runs_created_at)
- Multiple migrations trying to drop same tables/indexes
- Migration timing issues causing "users" table to not exist when test data runs
- Old problematic migrations still being executed despite creating clean migration

## Root Cause CONFIRMED
After examining the old migration files in versions_backup/versions/, I can confirm:

1. **The old migration chain DOES create all required tables**:
   - 001_current_schema.py: Creates users, runs tables with indexes
   - 002_add_unified_tasks.py: Adds tasks and task_outputs tables
   - cf94a9256bdb_add_archived_field_to_tasks_table.py: Adds archived field to tasks

2. **The clean migration I created ALSO creates all required tables**:
   - Creates tasks table WITH archived field
   - Creates users table with all GitHub fields
   - Creates task_outputs table with proper foreign keys

3. **The system is running OLD migrations instead of the clean one**:
   - Database logs show "DROP INDEX ix_runs_created_at" errors
   - This comes from the old migration chain trying to drop runs table
   - The clean migration doesn't reference runs table at all

4. **Alembic is still pointing to old migration chain**:
   - The alembic_version table likely contains a reference to the old migration chain
   - When alembic upgrade head runs, it tries to execute remaining old migrations
   - The clean migration is ignored because alembic thinks it's already at a newer version

## Detailed Fix Steps

### Step 1: Verify Current State
**Action**: Check what migrations alembic thinks exist
```bash
# Check current alembic revision
DATABASE_URL="postgresql+asyncpg://aideator:aideator123@localhost:5432/aideator" uv run alembic current

# Check migration history
DATABASE_URL="postgresql+asyncpg://aideator:aideator123@localhost:5432/aideator" uv run alembic history

# Check what migration files exist
ls -la /Users/alchang/dev/aideator/alembic/versions/
ls -la /Users/alchang/dev/aideator/alembic/versions_backup/
```

**Expected Result**: Should show only the clean migration (0b228e9fec0b_initial_clean_schema.py)

### Step 2: Verify Database State
**Action**: Check what tables actually exist in database
```bash
# Connect to database and check tables
psql -h localhost -U aideator -d aideator -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"

# Check alembic version table
psql -h localhost -U aideator -d aideator -c "SELECT * FROM alembic_version;"
```

**Expected Result**: Should show what tables exist and what alembic thinks is the current revision

### Step 3: Check Migration File Content
**Action**: Verify the clean migration creates all necessary tables
```bash
# Check that our clean migration creates users, tasks, task_outputs tables
cat /Users/alchang/dev/aideator/alembic/versions/0b228e9fec0b_initial_clean_schema.py | grep -A 5 -B 5 "create_table"
```

**Expected Result**: Should show op.create_table calls for users, tasks, task_outputs

### Step 4: Reset Alembic State Completely
**Action**: Clear all alembic tracking and start fresh
```bash
# Drop alembic version table to clear state
psql -h localhost -U aideator -d aideator -c "DROP TABLE IF EXISTS alembic_version CASCADE;"

# Drop all existing tables to ensure clean state
psql -h localhost -U aideator -d aideator -c "DROP TABLE IF EXISTS users, tasks, task_outputs, runs CASCADE;"

# Verify database is completely empty
psql -h localhost -U aideator -d aideator -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
```

**Expected Result**: Database should be completely empty (no tables)

### Step 5: Ensure Only Clean Migration Exists
**Action**: Remove any references to old migrations
```bash
# Ensure versions_backup is not being used
rm -rf /Users/alchang/dev/aideator/alembic/versions_backup/

# Verify only clean migration exists
ls -la /Users/alchang/dev/aideator/alembic/versions/
```

**Expected Result**: Only 0b228e9fec0b_initial_clean_schema.py should exist

### Step 6: Test Clean Migration
**Action**: Run the clean migration on empty database
```bash
# Run migration on empty database
DATABASE_URL="postgresql+asyncpg://aideator:aideator123@localhost:5432/aideator" uv run alembic upgrade head

# Verify tables were created
psql -h localhost -U aideator -d aideator -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"

# Check alembic version is set correctly
psql -h localhost -U aideator -d aideator -c "SELECT * FROM alembic_version;"
```

**Expected Result**: 
- Tables: alembic_version, task_outputs, tasks, users
- alembic_version should contain: 0b228e9fec0b

### Step 7: Verify Table Structure
**Action**: Check that tables have correct columns including archived field
```bash
# Check users table structure
psql -h localhost -U aideator -d aideator -c "\\d users;"

# Check tasks table structure (should include archived field)
psql -h localhost -U aideator -d aideator -c "\\d tasks;"

# Check task_outputs table structure
psql -h localhost -U aideator -d aideator -c "\\d task_outputs;"
```

**Expected Result**: 
- users table should have: id, email, github_id, github_username, etc.
- tasks table should have: id, github_url, prompt, archived, etc.
- task_outputs table should have: id, task_id, variation_id, content, etc.

### Step 8: Test Mock Data Script
**Action**: Verify test data script works with clean tables
```bash
# Run test data script
DATABASE_URL="postgresql+asyncpg://aideator:aideator123@localhost:5432/aideator" uv run python scripts/add_mock_task_data.py

# Verify data was created
psql -h localhost -U aideator -d aideator -c "SELECT count(*) FROM users;"
psql -h localhost -U aideator -d aideator -c "SELECT count(*) FROM tasks;"
psql -h localhost -U aideator -d aideator -c "SELECT count(*) FROM task_outputs;"
```

**Expected Result**: Should show test data was successfully created

### Step 9: Update Tiltfile to Use Clean Migration
**Action**: Verify Tiltfile database-migrate command works correctly
```bash
# Check that Tiltfile migration command is correct
grep -A 5 -B 5 "database-migrate" /Users/alchang/dev/aideator/Tiltfile
```

**Expected Result**: Should show the migration command uses correct database URL and alembic upgrade head

### Step 10: Test Full System
**Action**: Run complete system test
```bash
# Run force-rebuild-agent.sh to test full system
./force-rebuild-agent.sh
```

**Expected Result**: Should complete without migration errors

## Risk Assessment

**High Risk Steps**:
- Step 4: Dropping all database tables (irreversible)
- Step 5: Removing backup migrations (irreversible)

**Mitigation**:
- Take database dump before Step 4
- Keep backup of versions_backup directory

**Recovery Plan**:
- If migration fails, restore from backup
- If clean migration is incorrect, recreate from backed up old migrations

## Success Criteria

1. ✅ Only one migration file exists (clean migration)
2. ✅ Database starts empty after cleanup
3. ✅ Clean migration creates all required tables
4. ✅ Tasks table includes archived field
5. ✅ Test data script succeeds
6. ✅ force-rebuild-agent.sh completes without errors
7. ✅ No "DROP INDEX ix_runs_created_at" errors in database logs

## Failure Scenarios

**If Step 6 fails**: Clean migration is incorrect, needs to be regenerated
**If Step 8 fails**: Table structure doesn't match model expectations
**If Step 10 fails**: System-level integration issue, not migration issue

## Point of No Return

Step 4 (dropping all tables) is the point of no return. After this, we must complete the process or restore from backup.