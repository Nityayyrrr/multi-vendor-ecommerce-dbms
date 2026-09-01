-- Database creation script for Multi-Vendor E-Commerce project
-- Uses utf8mb4 for full unicode support

CREATE DATABASE IF NOT EXISTS `multivendor_ecommerce_db`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `multivendor_ecommerce_db`;

-- Check active database
SELECT DATABASE() AS `active_database`, 'Database initialized successfully.' AS `status`;
