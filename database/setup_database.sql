-- Multi-Vendor E-Commerce & Inventory Management System
-- Master Database Setup Entry Point for MySQL 8.4
-- Creates the database and all 12 canonical tables with full integrity constraints.
-- Non-destructive: Uses CREATE DATABASE IF NOT EXISTS and CREATE TABLE IF NOT EXISTS.

CREATE DATABASE IF NOT EXISTS `multivendor_ecommerce_db`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `multivendor_ecommerce_db`;

-- 1. Customer table
-- Stores registered customer accounts
CREATE TABLE IF NOT EXISTS `customer` (
    `customer_id` VARCHAR(32) NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(150) NOT NULL,
    `join_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`customer_id`),
    CONSTRAINT `uq_customer_email` UNIQUE (`email`),
    CONSTRAINT `chk_customer_email_format` CHECK (`email` LIKE '%_@__%.__%'),
    CONSTRAINT `chk_customer_join_date` CHECK (`join_date` >= '2016-01-01 00:00:00')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Vendor table
-- Stores marketplace seller / merchant information
CREATE TABLE IF NOT EXISTS `vendor` (
    `vendor_id` VARCHAR(32) NOT NULL,
    `vendor_name` VARCHAR(100) NOT NULL,
    `rating` DECIMAL(3, 2) NOT NULL DEFAULT 5.00,
    `gst_number` VARCHAR(20) NOT NULL,
    PRIMARY KEY (`vendor_id`),
    CONSTRAINT `uq_vendor_gst` UNIQUE (`gst_number`),
    CONSTRAINT `chk_vendor_rating` CHECK (`rating` >= 1.00 AND `rating` <= 5.00),
    CONSTRAINT `chk_vendor_gst_len` CHECK (CHAR_LENGTH(`gst_number`) >= 8)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Category table
-- Self-referencing hierarchy where parent_category_id links subcategories to a parent category
CREATE TABLE IF NOT EXISTS `category` (
    `category_id` INT UNSIGNED AUTO_INCREMENT NOT NULL,
    `category_name` VARCHAR(100) NOT NULL,
    `parent_category_id` INT UNSIGNED NULL DEFAULT NULL,
    PRIMARY KEY (`category_id`),
    CONSTRAINT `uq_category_name` UNIQUE (`category_name`),
    CONSTRAINT `fk_category_parent` FOREIGN KEY (`parent_category_id`) REFERENCES `category` (`category_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Warehouse table
-- Stores warehouse locations and their maximum unit capacity
CREATE TABLE IF NOT EXISTS `warehouse` (
    `warehouse_id` INT UNSIGNED AUTO_INCREMENT NOT NULL,
    `location` VARCHAR(100) NOT NULL,
    `capacity` INT UNSIGNED NOT NULL,
    PRIMARY KEY (`warehouse_id`),
    CONSTRAINT `chk_warehouse_capacity` CHECK (`capacity` > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Product table
-- Stores products on the platform and links each product to a category and vendor
CREATE TABLE IF NOT EXISTS `product` (
    `product_id` VARCHAR(32) NOT NULL,
    `product_name` VARCHAR(150) NOT NULL,
    `description` TEXT NULL DEFAULT NULL,
    `price` DECIMAL(10, 2) NOT NULL,
    `category_id` INT UNSIGNED NOT NULL,
    `vendor_id` VARCHAR(32) NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'Active',
    PRIMARY KEY (`product_id`),
    CONSTRAINT `fk_product_category` FOREIGN KEY (`category_id`) REFERENCES `category` (`category_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_product_vendor` FOREIGN KEY (`vendor_id`) REFERENCES `vendor` (`vendor_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `chk_product_price` CHECK (`price` >= 0.00),
    CONSTRAINT `chk_product_status` CHECK (`status` IN ('Active', 'Inactive', 'Out of Stock', 'Discontinued', 'ACTIVE', 'INACTIVE', 'OUT_OF_STOCK', 'DISCONTINUED')),
    INDEX `idx_product_category` (`category_id`),
    INDEX `idx_product_vendor` (`vendor_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Customer Phone table
-- Separate table because phone numbers are a multivalued customer attribute
CREATE TABLE IF NOT EXISTS `customer_phone` (
    `customer_id` VARCHAR(32) NOT NULL,
    `phone_number` VARCHAR(20) NOT NULL,
    `phone_type` VARCHAR(20) NOT NULL DEFAULT 'Mobile',
    PRIMARY KEY (`customer_id`, `phone_number`),
    CONSTRAINT `fk_customer_phone_customer` FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `chk_phone_number_length` CHECK (CHAR_LENGTH(`phone_number`) >= 8),
    CONSTRAINT `chk_phone_type` CHECK (`phone_type` IN ('Mobile', 'Home', 'Work', 'Office', 'Other'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Address table
-- Stores customer shipping and billing addresses (weak entity dependent on customer)
CREATE TABLE IF NOT EXISTS `address` (
    `customer_id` VARCHAR(32) NOT NULL,
    `address_type` VARCHAR(20) NOT NULL DEFAULT 'Shipping',
    `street` VARCHAR(150) NOT NULL,
    `city` VARCHAR(50) NOT NULL,
    `state` CHAR(2) NOT NULL,
    `pincode` VARCHAR(10) NOT NULL,
    `is_default` BOOLEAN NOT NULL DEFAULT 0,
    PRIMARY KEY (`customer_id`, `address_type`),
    CONSTRAINT `fk_address_customer` FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `chk_address_type` CHECK (`address_type` IN ('Shipping', 'Billing', 'Home', 'Office', 'Work', 'Other')),
    CONSTRAINT `chk_address_state_len` CHECK (CHAR_LENGTH(`state`) = 2)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Product Tag table
-- Stores product search tags (multivalued attribute kept in 1NF)
CREATE TABLE IF NOT EXISTS `product_tag` (
    `product_id` VARCHAR(32) NOT NULL,
    `tag` VARCHAR(50) NOT NULL,
    PRIMARY KEY (`product_id`, `tag`),
    CONSTRAINT `fk_product_tag_product` FOREIGN KEY (`product_id`) REFERENCES `product` (`product_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `chk_tag_length` CHECK (CHAR_LENGTH(`tag`) >= 2),
    INDEX `idx_product_tag_name` (`tag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Inventory table
-- Connects products to warehouses and tracks stock levels (resolves M:N relationship)
CREATE TABLE IF NOT EXISTS `inventory` (
    `product_id` VARCHAR(32) NOT NULL,
    `warehouse_id` INT UNSIGNED NOT NULL,
    `stock_quantity` INT NOT NULL DEFAULT 0,
    `reorder_level` INT NOT NULL DEFAULT 10,
    `last_updated` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`product_id`, `warehouse_id`),
    CONSTRAINT `fk_inventory_product` FOREIGN KEY (`product_id`) REFERENCES `product` (`product_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_inventory_warehouse` FOREIGN KEY (`warehouse_id`) REFERENCES `warehouse` (`warehouse_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `chk_inventory_stock` CHECK (`stock_quantity` >= 0),
    CONSTRAINT `chk_inventory_reorder` CHECK (`reorder_level` >= 0),
    INDEX `idx_inventory_warehouse` (`warehouse_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Orders table
-- Stores customer orders and their current status
CREATE TABLE IF NOT EXISTS `orders` (
    `order_id` VARCHAR(32) NOT NULL,
    `customer_id` VARCHAR(32) NOT NULL,
    `order_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `status` VARCHAR(20) NOT NULL DEFAULT 'PLACED',
    PRIMARY KEY (`order_id`),
    CONSTRAINT `fk_orders_customer` FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `chk_orders_status` CHECK (`status` IN ('PLACED', 'CONFIRMED', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'PROCESSING', 'INVOICED', 'UNAVAILABLE', 'CREATED', 'APPROVED', 'delivered', 'shipped', 'canceled', 'unavailable', 'invoiced', 'processing', 'created', 'approved')),
    INDEX `idx_orders_customer` (`customer_id`),
    INDEX `idx_orders_date` (`order_date`),
    INDEX `idx_orders_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. Order Item table
-- Resolves many-to-many relationship between orders and products
-- price_at_purchase stores the price at the time of purchase, separate from current product.price
CREATE TABLE IF NOT EXISTS `order_item` (
    `order_id` VARCHAR(32) NOT NULL,
    `product_id` VARCHAR(32) NOT NULL,
    `quantity` INT NOT NULL DEFAULT 1,
    `price_at_purchase` DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (`order_id`, `product_id`),
    CONSTRAINT `fk_order_item_orders` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_order_item_product` FOREIGN KEY (`product_id`) REFERENCES `product` (`product_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `chk_order_item_quantity` CHECK (`quantity` > 0),
    CONSTRAINT `chk_order_item_price` CHECK (`price_at_purchase` >= 0.00),
    INDEX `idx_order_item_product` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. Payment table
-- Payment depends on an order, so (order_id, payment_id) forms the composite primary key
-- Supports multiple payments per order (e.g. split between voucher and card)
CREATE TABLE IF NOT EXISTS `payment` (
    `order_id` VARCHAR(32) NOT NULL,
    `payment_id` INT UNSIGNED NOT NULL,
    `amount` DECIMAL(10, 2) NOT NULL,
    `mode` VARCHAR(20) NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'Success',
    `payment_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `transaction_reference` VARCHAR(64) NOT NULL,
    PRIMARY KEY (`order_id`, `payment_id`),
    CONSTRAINT `fk_payment_orders` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `uq_payment_txn_ref` UNIQUE (`transaction_reference`),
    CONSTRAINT `chk_payment_amount` CHECK (`amount` > 0.00),
    CONSTRAINT `chk_payment_mode` CHECK (`mode` IN ('credit_card', 'boleto', 'voucher', 'debit_card', 'not_defined', 'Credit Card', 'Debit Card', 'UPI', 'Net Banking', 'Cash on Delivery', 'Voucher', 'Wallet')),
    CONSTRAINT `chk_payment_status` CHECK (`status` IN ('Success', 'Pending', 'Failed', 'Refunded', 'SUCCESS', 'PENDING', 'FAILED', 'REFUNDED')),
    INDEX `idx_payment_order` (`order_id`),
    INDEX `idx_payment_mode` (`mode`),
    INDEX `idx_payment_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
