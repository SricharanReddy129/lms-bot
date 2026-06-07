-- =========================================================================
-- 1. POPULATE EMPLOYEE_DATA (The Core Directory)
-- =========================================================================
INSERT INTO employee_data (employee_id, employee_name) VALUES
(1001, 'Srinivas Kumar'),
(1002, 'Ananya Rao'),
(1003, 'Rahul Sharma'),
(1004, 'Priya Patel'),
(1005, 'Vikram Malhotra'),
(1006, 'Sneha Reddy'),
(1007, 'Amit Verma'),
(1008, 'Meera Nair'),
(1009, 'Rohan Das'),
(1010, 'Kriti Joshi');

-- =========================================================================
-- 2. POPULATE EMPLOYEE_ROLE (3 Approvers, 7 Applicants)
-- =========================================================================
INSERT INTO employee_role (employee_id, employee_role) VALUES
(1001, 'approver'),  -- Executive / Top Manager
(1002, 'approver'),  -- Line Manager A
(1003, 'approver'),  -- Line Manager B
(1004, 'applicant'),
(1005, 'applicant'),
(1006, 'applicant'),
(1007, 'applicant'),
(1008, 'applicant'),
(1009, 'applicant'),
(1010, 'applicant');

-- =========================================================================
-- 3. POPULATE EMPLOYEE_PASSWORD (All passwords set to 'password123' for testing)
-- =========================================================================
INSERT INTO employee_password (employee_id, employee_email_id, password) VALUES
(1001, 'srinivas.kumar@pavesglobal.com', 'password123'),
(1002, 'ananya.rao@pavesglobal.com', 'password123'),
(1003, 'rahul.sharma@pavesglobal.com', 'password123'),
(1004, 'priya.patel@pavesglobal.com', 'password123'),
(1005, 'vikram.malhotra@pavesglobal.com', 'password123'),
(1006, 'sneha.reddy@pavesglobal.com', 'password123'),
(1007, 'amit.verma@pavesglobal.com', 'password123'),
(1008, 'meera.nair@pavesglobal.com', 'password123'),
(1009, 'rohan.das@pavesglobal.com', 'password123'),
(1010, 'kriti.joshi@pavesglobal.com', 'password123');

-- =========================================================================
-- 4. POPULATE LEAVE_BALANCE (Varying allocations for testing edge cases)
-- =========================================================================
INSERT INTO leave_balance (employee_id, earned_leaves, sick_leaves, parental_leaves) VALUES
(1001, 24, 12, 10), -- Approver balances
(1002, 20, 10, 0),
(1003, 18, 8, 10),
(1004, 15, 6, 12),  -- Standard applicant
(1005, 0, 2, 0),    -- Edge Case: Low/exhausted balances
(1006, 14, 12, 10),
(1007, 22, 9, 0),
(1008, 11, 5, 12),
(1009, 5, 1, 0),    -- Edge Case: Low balances
(1010, 16, 7, 10);

-- =========================================================================
-- 5. BONUS: POPULATE HOLIDAYS_CALENDAR (Useful for testing leave duration calculation)
-- =========================================================================
INSERT INTO holidays_calendar (holiday_name, holiday_date) VALUES
('New Year Day', '2026-01-01'),
('Republic Day', '2026-01-26'),
('Good Friday', '2026-04-03'),
('Independence Day', '2026-08-15'),
('Gandhi Jayanti', '2026-10-02'),
('Christmas', '2026-12-25');