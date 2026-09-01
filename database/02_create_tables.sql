-- Create the 12 core tables for the Multi-Vendor E-Commerce database

USE `multivendor_ecommerce_db`;

-- Drop existing tables in reverse dependency order for clean re-runs
DROP TABLE IF EXISTS `payment`;
DROP TABLE IF EXISTS `order_item`;
DROP TABLE IF EXISTS `orders`;
DROP TABLE IF EXISTS `inventory`;
DROP TABLE IF EXISTS `product_tag`;
DROP TABLE IF EXISTS `address`;
DROP TABLE IF EXISTS `customer_phone`;
DROP TABLE IF EXISTS `product`;
DROP TABLE IF EXISTS `warehouse`;
DROP TABLE IF EXISTS `category`;
DROP TABLE IF EXISTS `vendor`;
DROP TABLE IF EXISTS `customer`;

-- 1. Customer table
-- Stores basic customer profile information
CREATE TABLE `customer` (
    `customer_id` VARCHAR(32) NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(150) NOT NULL,
    `join_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Vendor table
-- Stores seller / merchant profiles
CREATE TABLE `vendor` (
    `vendor_id` VARCHAR(32) NOT NULL,
    `vendor_name` VARCHAR(100) NOT NULL,
    `rating` DECIMAL(3, 2) NOT NULL DEFAULT 5.00,
    `gst_number` VARCHAR(20) NOT NULL,
    PRIMARY KEY (`vendor_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Category table
-- Product category hierarchy. parent_category_id allows subcategories to reference a parent category (NULL for root)
CREATE TABLE `category` (
    `category_id` INT UNSIGNED AUTO_INCREMENT NOT NULL,
    `category_name` VARCHAR(100) NOT NULL,
    `parent_category_id` INT UNSIGNED NULL DEFAULT NULL,
    PRIMARY KEY (`category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Warehouse table
-- Stores warehouse locations and their storage capacities
CREATE TABLE `warehouse` (
    `warehouse_id` INT UNSIGNED AUTO_INCREMENT NOT NULL,
    `location` VARCHAR(100) NOT NULL,
    `capacity` INT UNSIGNED NOT NULL,
    PRIMARY KEY (`warehouse_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Product table
-- Stores catalog products and links each product to a category and vendor
CREATE TABLE `product` (
    `product_id` VARCHAR(32) NOT NULL,
    `product_name` VARCHAR(150) NOT NULL,
    `description` TEXT NULL DEFAULT NULL,
    `price` DECIMAL(10, 2) NOT NULL,
    `category_id` INT UNSIGNED NOT NULL,
    `vendor_id` VARCHAR(32) NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'Active',
    PRIMARY KEY (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Customer Phone table
-- Separate table because phone numbers are a multivalued customer attribute
CREATE TABLE `customer_phone` (
    `customer_id` VARCHAR(32) NOT NULL,
    `phone_number` VARCHAR(20) NOT NULL,
    `phone_type` VARCHAR(20) NOT NULL DEFAULT 'Mobile',
    PRIMARY KEY (`customer_id`, `phone_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Address table
-- Stores customer shipping and billing addresses (weak entity dependent on customer)
CREATE TABLE `address` (
    `customer_id` VARCHAR(32) NOT NULL,
    `address_type` VARCHAR(20) NOT NULL DEFAULT 'Shipping',
    `street` VARCHAR(150) NOT NULL,
    `city` VARCHAR(50) NOT NULL,
    `state` CHAR(2) NOT NULL,
    `pincode` VARCHAR(10) NOT NULL,
    `is_default` BOOLEAN NOT NULL DEFAULT 0,
    PRIMARY KEY (`customer_id`, `address_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Product Tag table
-- Stores descriptive keyword tags (multivalued attribute normalized into 1NF)
CREATE TABLE `product_tag` (
    `product_id` VARCHAR(32) NOT NULL,
    `tag` VARCHAR(50) NOT NULL,
    PRIMARY KEY (`product_id`, `tag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Inventory table
-- Connects products to warehouses and tracks stock levels (resolves M:N relationship)
CREATE TABLE `inventory` (
    `product_id` VARCHAR(32) NOT NULL,
    `warehouse_id` INT UNSIGNED NOT NULL,
    `stock_quantity` INT NOT NULL DEFAULT 0,
    `reorder_level` INT NOT NULL DEFAULT 10,
    `last_updated` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`product_id`, `warehouse_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Orders table
-- Stores customer order transactions and order lifecycle status
CREATE TABLE `orders` (
    `order_id` VARCHAR(32) NOT NULL,
    `customer_id` VARCHAR(32) NOT NULL,
    `order_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `status` VARCHAR(20) NOT NULL DEFAULT 'PLACED',
    PRIMARY KEY (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. Order Item table
-- Resolves the many-to-many relationship between orders and products
-- price_at_purchase keeps the historical price actually paid at time of order
CREATE TABLE `order_item` (
    `order_id` VARCHAR(32) NOT NULL,
    `product_id` VARCHAR(32) NOT NULL,
    `quantity` INT NOT NULL DEFAULT 1,
    `price_at_purchase` DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (`order_id`, `product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. Payment table
-- Payment depends on an order, so (order_id, payment_id) forms the composite primary key
-- Supports multiple payments per order (e.g. split between voucher and card)
CREATE TABLE `payment` (
    `order_id` VARCHAR(32) NOT NULL,
    `payment_id` INT UNSIGNED NOT NULL,
    `amount` DECIMAL(10, 2) NOT NULL,
    `mode` VARCHAR(20) NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'Success',
    `payment_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `transaction_reference` VARCHAR(64) NOT NULL,
    PRIMARY KEY (`order_id`, `payment_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
