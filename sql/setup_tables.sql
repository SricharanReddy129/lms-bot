create database lms_bot;
use lms_bot;

create table leave_balance(
sno int AUTO_INCREMENT  primary key,
employee_id int not null,
earned_leaves int,
sick_leaves int,
parental_leaves int);

create table employee_data(
sno int auto_increment primary key,
employee_id int not null,
employee_name varchar(50) not null);

create table employee_password(
sno int auto_increment primary key,
employee_id int not null,
employee_email_id varchar(50) not null,
password varchar(50) not null);

create table employee_role(
sno int auto_increment primary key,
employee_id int not null,
employee_role varchar(50) not null);
ALTER TABLE employee_role
MODIFY COLUMN employee_role ENUM('approver', 'applicant') NOT NULL;

create table pending_leaves(
sno int auto_increment primary key,
employee_id int not null,
leave_type enum ("earned", "sick", "parental") not null,
start_date date not null,
end_date date not null);
ALTER TABLE pending_leaves
ADD COLUMN reason TEXT;

create table approved_leaves(
sno int auto_increment primary key,
leave_id int references pending_leaves.sno,
employee_id int not null,
start_date date not null,
end_date date not null);

create table rejected_leaves(
sno int auto_increment primary key,
leave_id int references pending_leaves.sno,
employee_id int not null,
reason text);

create table holidays_calendar(
sno int auto_increment primary key,
holiday_name varchar(50) not null,
holiday_date date not null);

CREATE TABLE chat_history (
    employee_id INT PRIMARY KEY,
    thread_id VARCHAR(255) NOT NULL,
    messages JSON NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

ALTER TABLE employee_data
ADD CONSTRAINT uk_employee_id UNIQUE (employee_id);

-- Link Security & Roles
ALTER TABLE employee_password
ADD CONSTRAINT fk_password_emp 
FOREIGN KEY (employee_id) REFERENCES employee_data(employee_id)
ON DELETE CASCADE;

ALTER TABLE employee_role
ADD CONSTRAINT fk_role_emp 
FOREIGN KEY (employee_id) REFERENCES employee_data(employee_id)
ON DELETE CASCADE;

-- Link Balances
ALTER TABLE leave_balance
ADD CONSTRAINT fk_balance_emp 
FOREIGN KEY (employee_id) REFERENCES employee_data(employee_id)
ON DELETE CASCADE;

-- Link Leave Tables (Now independent from each other, but linked to the employee)
ALTER TABLE pending_leaves
ADD CONSTRAINT fk_pending_emp 
FOREIGN KEY (employee_id) REFERENCES employee_data(employee_id)
ON DELETE CASCADE;

ALTER TABLE approved_leaves
ADD CONSTRAINT fk_approved_emp 
FOREIGN KEY (employee_id) REFERENCES employee_data(employee_id)
ON DELETE CASCADE;

ALTER TABLE rejected_leaves
ADD CONSTRAINT fk_rejected_emp 
FOREIGN KEY (employee_id) REFERENCES employee_data(employee_id)
ON DELETE CASCADE;