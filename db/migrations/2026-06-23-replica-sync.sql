/* ============================================================
   Replica Sync — schema + seed for portfolio RBAC (SINGLE-TABLE model)
   Target: Azure SQL  MyStudentDb_v2  (and local samsdb if used).
   Idempotent/guarded. Already executed against Azure on 2026-06-24.

   Design: the replica uses ONE stacked dbo.ClassSchedule table (renamed from
   ClassSchedule2261), matching the source app — NOT per-term tables.
   ============================================================ */

/* ---------- Consolidate to a single ClassSchedule table ---------- */
-- Rename the 2261 term table to the generic ClassSchedule (only if not already done).
IF OBJECT_ID('dbo.ClassSchedule','U') IS NULL AND OBJECT_ID('dbo.ClassSchedule2261','U') IS NOT NULL
    EXEC sp_rename 'dbo.ClassSchedule2261', 'ClassSchedule';
-- ClassSchedule2254 is left in place, unused (drop manually if desired):
--   DROP TABLE dbo.ClassSchedule2254;

/* ---------- Analytics columns on ClassSchedule ----------
   NOTE: the real mode column is [InstructorMode]; the model maps attr
   InstructMode -> column "InstructorMode". No rename needed here. */
IF OBJECT_ID('dbo.ClassSchedule','U') IS NOT NULL AND COL_LENGTH('dbo.ClassSchedule','ClassType') IS NULL
    ALTER TABLE dbo.ClassSchedule ADD ClassType NVARCHAR(5) NULL, ClassStatus NVARCHAR(5) NULL, AssocClassNum INT NULL;
-- Backfill so analytics enrollment filter (ClassType='E' AND ClassStatus='A') returns demo data:
IF OBJECT_ID('dbo.ClassSchedule','U') IS NOT NULL
    UPDATE dbo.ClassSchedule SET ClassType='E', ClassStatus='A' WHERE ClassType IS NULL;

/* ---------- AdminAuditLog (model maps to dbo.AdminAuditLog) ---------- */
IF OBJECT_ID('dbo.AdminAuditLog','U') IS NULL
BEGIN
    CREATE TABLE dbo.AdminAuditLog (
        id          INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        admin_user  NVARCHAR(100)  NOT NULL,
        action_type NVARCHAR(50)   NOT NULL,
        [timestamp] DATETIME2      NOT NULL CONSTRAINT DF_AAL_ts DEFAULT SYSUTCDATETIME(),
        [status]    NVARCHAR(20)   NOT NULL,
        summary     NVARCHAR(500)  NULL,
        details     NVARCHAR(MAX)  NULL,
        created_at  DATETIME2      NOT NULL CONSTRAINT DF_AAL_ca DEFAULT SYSUTCDATETIME()
    );
    CREATE INDEX IX_AAL_admin_user  ON dbo.AdminAuditLog(admin_user);
    CREATE INDEX IX_AAL_action_type ON dbo.AdminAuditLog(action_type);
    CREATE INDEX IX_AAL_ts          ON dbo.AdminAuditLog([timestamp]);
END
-- Drop the empty lowercase stub once AdminAuditLog exists:
IF OBJECT_ID('dbo.admin_audit_log','U') IS NOT NULL AND NOT EXISTS (SELECT 1 FROM dbo.admin_audit_log)
    DROP TABLE dbo.admin_audit_log;

/* ---------- RBAC flag columns ---------- */
IF COL_LENGTH('dbo.user_access','analytics') IS NULL
    ALTER TABLE dbo.user_access ADD analytics BIT NOT NULL CONSTRAINT DF_ua_analytics DEFAULT 0;
IF COL_LENGTH('dbo.user_access','chat') IS NULL
    ALTER TABLE dbo.user_access ADD chat BIT NOT NULL CONSTRAINT DF_ua_chat DEFAULT 0;

/* ---------- Parity columns ---------- */
IF COL_LENGTH('dbo.StudentData','Prog_Reason_Descr') IS NULL
    ALTER TABLE dbo.StudentData ADD
        Prog_Reason_Descr NVARCHAR(100) NULL, Residency NVARCHAR(10) NULL,
        Residency_Status NVARCHAR(10) NULL, Market NVARCHAR(50) NULL;
IF COL_LENGTH('dbo.StudentClassAssignments','Prog_Reason_Descr') IS NULL
    ALTER TABLE dbo.StudentClassAssignments ADD
        Prog_Reason_Descr NVARCHAR(100) NULL, Residency NVARCHAR(10) NULL,
        Residency_Status NVARCHAR(10) NULL, Market NVARCHAR(50) NULL;
IF COL_LENGTH('dbo.StudentClassAssignments','Offer_Signed_Workday') IS NULL
    ALTER TABLE dbo.StudentClassAssignments ADD Offer_Signed_Workday BIT NULL;

/* ---------- Seed 3 fake portfolio users (match Login.js buttons) ---------- */
IF NOT EXISTS (SELECT 1 FROM dbo.user_access WHERE asu_id='demo_faculty')
    INSERT INTO dbo.user_access (asu_id, role, name, email, login, analytics, chat,
        faculty_dashboard, applications, faculty_quickassign, faculty_grader_uploads)
    VALUES ('demo_faculty','faculty_grader','Demo Faculty','faculty@example.edu',1,0,0,1,1,1,1);
IF NOT EXISTS (SELECT 1 FROM dbo.user_access WHERE asu_id='demo_chair')
    INSERT INTO dbo.user_access (asu_id, role, name, email, login, analytics, chat,
        faculty_dashboard, applications, student_summary_page, bulk_upload_assignments,
        assignment_adder, program_chair_uploads)
    VALUES ('demo_chair','program_chair','Demo Chair','chair@example.edu',1,0,0,1,1,1,1,1,1);
IF NOT EXISTS (SELECT 1 FROM dbo.user_access WHERE asu_id='demo_admin')
    INSERT INTO dbo.user_access (asu_id, role, name, email, login, analytics, chat, master_dashboard)
    VALUES ('demo_admin','admin','Demo Admin','admin@example.edu',1,1,1,1);

/* Active term for this data is 2261 — set ACTIVE_TERM=2261 in .env / Azure config. */
