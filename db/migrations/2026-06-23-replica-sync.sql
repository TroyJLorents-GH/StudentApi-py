/* ============================================================
   Replica Sync — schema + seed for portfolio RBAC
   RUN THIS AGAINST BOTH DATABASES:
     1) local  : Troyjl\SQLEXPRESS  ->  samsdb
     2) Azure  : <server>.database.windows.net -> MyStudentDb_v2
   Idempotent-ish: uses guards where practical. Review before running.
   ============================================================ */

/* ---------- Task 0.1: AdminAuditLog ---------- */
-- Inspect existing stub first:
-- SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='admin_audit_log';
-- SELECT COUNT(*) FROM dbo.admin_audit_log;
-- If columns already match and you want the data: EXEC sp_rename 'dbo.admin_audit_log','AdminAuditLog';  -- then skip CREATE

IF OBJECT_ID('dbo.AdminAuditLog','U') IS NULL
BEGIN
    CREATE TABLE dbo.AdminAuditLog (
        id          INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        admin_user  NVARCHAR(100)  NOT NULL,
        action_type NVARCHAR(50)   NOT NULL,
        [timestamp] DATETIME2      NOT NULL CONSTRAINT DF_AdminAuditLog_timestamp  DEFAULT SYSUTCDATETIME(),
        [status]    NVARCHAR(20)   NOT NULL,
        summary     NVARCHAR(500)  NULL,
        details     NVARCHAR(MAX)  NULL,
        created_at  DATETIME2      NOT NULL CONSTRAINT DF_AdminAuditLog_created_at DEFAULT SYSUTCDATETIME()
    );
    CREATE INDEX IX_AdminAuditLog_admin_user  ON dbo.AdminAuditLog (admin_user);
    CREATE INDEX IX_AdminAuditLog_action_type ON dbo.AdminAuditLog (action_type);
    CREATE INDEX IX_AdminAuditLog_timestamp   ON dbo.AdminAuditLog ([timestamp]);
END
-- After verifying AdminAuditLog exists and stub is empty:
-- DROP TABLE dbo.admin_audit_log;

/* ---------- Task 0.2: user_access RBAC flags ---------- */
IF COL_LENGTH('dbo.user_access','analytics') IS NULL
    ALTER TABLE dbo.user_access ADD analytics BIT NOT NULL CONSTRAINT DF_user_access_analytics DEFAULT 0;
IF COL_LENGTH('dbo.user_access','chat') IS NULL
    ALTER TABLE dbo.user_access ADD chat BIT NOT NULL CONSTRAINT DF_user_access_chat DEFAULT 0;

/* ---------- Task 0.3: ClassSchedule term tables — analytics cols ----------
   Repeat per term table that EXISTS in this DB. Skip ones that don't exist. */
IF OBJECT_ID('dbo.ClassSchedule2254','U') IS NOT NULL AND COL_LENGTH('dbo.ClassSchedule2254','ClassType') IS NULL
    ALTER TABLE dbo.ClassSchedule2254 ADD ClassType NVARCHAR(5) NULL, ClassStatus NVARCHAR(5) NULL, AssocClassNum INT NULL;
IF OBJECT_ID('dbo.ClassSchedule2261','U') IS NOT NULL AND COL_LENGTH('dbo.ClassSchedule2261','ClassType') IS NULL
    ALTER TABLE dbo.ClassSchedule2261 ADD ClassType NVARCHAR(5) NULL, ClassStatus NVARCHAR(5) NULL, AssocClassNum INT NULL;
IF OBJECT_ID('dbo.ClassSchedule2264','U') IS NOT NULL AND COL_LENGTH('dbo.ClassSchedule2264','ClassType') IS NULL
    ALTER TABLE dbo.ClassSchedule2264 ADD ClassType NVARCHAR(5) NULL, ClassStatus NVARCHAR(5) NULL, AssocClassNum INT NULL;

-- Backfill so analytics enrollment filter (ClassType='E' AND ClassStatus='A') returns demo data:
IF OBJECT_ID('dbo.ClassSchedule2254','U') IS NOT NULL
    UPDATE dbo.ClassSchedule2254 SET ClassType='E', ClassStatus='A' WHERE ClassType IS NULL;
IF OBJECT_ID('dbo.ClassSchedule2261','U') IS NOT NULL
    UPDATE dbo.ClassSchedule2261 SET ClassType='E', ClassStatus='A' WHERE ClassType IS NULL;
IF OBJECT_ID('dbo.ClassSchedule2264','U') IS NOT NULL
    UPDATE dbo.ClassSchedule2264 SET ClassType='E', ClassStatus='A' WHERE ClassType IS NULL;

/* ---------- Task 0.4: Assignment + Student parity cols ---------- */
IF COL_LENGTH('dbo.StudentData','Prog_Reason_Descr') IS NULL
    ALTER TABLE dbo.StudentData ADD
        Prog_Reason_Descr NVARCHAR(100) NULL,
        Residency NVARCHAR(10) NULL,
        Residency_Status NVARCHAR(10) NULL,
        Market NVARCHAR(50) NULL;

IF COL_LENGTH('dbo.StudentClassAssignments','Prog_Reason_Descr') IS NULL
    ALTER TABLE dbo.StudentClassAssignments ADD
        Prog_Reason_Descr NVARCHAR(100) NULL,
        Residency NVARCHAR(10) NULL,
        Residency_Status NVARCHAR(10) NULL,
        Market NVARCHAR(50) NULL;
IF COL_LENGTH('dbo.StudentClassAssignments','Offer_Signed_Workday') IS NULL
    ALTER TABLE dbo.StudentClassAssignments ADD Offer_Signed_Workday BIT NULL;
-- Only if Status is missing:
IF COL_LENGTH('dbo.StudentClassAssignments','Status') IS NULL
    ALTER TABLE dbo.StudentClassAssignments ADD [Status] NVARCHAR(MAX) NULL;

/* ---------- Task 5.1: Seed 3 fake portfolio users ----------
   asu_ids MUST match the Login.js buttons: demo_faculty / demo_chair / demo_admin */
IF NOT EXISTS (SELECT 1 FROM dbo.user_access WHERE asu_id='demo_faculty')
    INSERT INTO dbo.user_access (asu_id, role, name, email, login, analytics, chat,
        faculty_dashboard, applications, faculty_quickassign, faculty_grader_uploads)
    VALUES ('demo_faculty', 'faculty_grader', 'Demo Faculty', 'faculty@example.edu', 1, 0, 0, 1, 1, 1, 1);

IF NOT EXISTS (SELECT 1 FROM dbo.user_access WHERE asu_id='demo_chair')
    INSERT INTO dbo.user_access (asu_id, role, name, email, login, analytics, chat,
        faculty_dashboard, applications, student_summary_page, bulk_upload_assignments,
        assignment_adder, program_chair_uploads)
    VALUES ('demo_chair', 'program_chair', 'Demo Chair', 'chair@example.edu', 1, 0, 0, 1, 1, 1, 1, 1, 1);

IF NOT EXISTS (SELECT 1 FROM dbo.user_access WHERE asu_id='demo_admin')
    INSERT INTO dbo.user_access (asu_id, role, name, email, login, analytics, chat, master_dashboard)
    VALUES ('demo_admin', 'admin', 'Demo Admin', 'admin@example.edu', 1, 1, 1, 1);

/* ---------- Verify ---------- */
SELECT 'AdminAuditLog' t, COUNT(*) n FROM dbo.AdminAuditLog
UNION ALL SELECT 'demo_users', COUNT(*) FROM dbo.user_access WHERE asu_id LIKE 'demo_%';
