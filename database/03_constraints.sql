-- Add constraints and indexes to the tables

USE `multivendor_ecommerce_db`;

-- Unique constraints
ALTER TABLE `customer`
    ADD CONSTRAINT `uq_customer_email` UNIQUE (`email`);

ALTER TABLE `vendor`
    ADD CONSTRAINT `uq_vendor_gst` UNIQUE (`gst_number`);

ALTER TABLE `category`
    ADD CONSTRAINT `uq_category_name` UNIQUE (`category_name`);

ALTER TABLE `payment`
    ADD CONSTRAINT `uq_payment_txn_ref` UNIQUE (`transaction_reference`);


-- Check constraints for valid values and formats

-- Customer validation (email format and valid join date)
ALTER TABLE `customer`
    ADD CONSTRAINT `chk_customer_email_format` CHECK (`email` LIKE '%_@__%.__%'),
    ADD CONSTRAINT `chk_customer_join_date` CHECK (`join_date` >= '2016-01-01 00:00:00');

-- Vendor rating must be between 1 and 5 stars
ALTER TABLE `vendor`
    ADD CONSTRAINT `chk_vendor_rating` CHECK (`rating` >= 1.00 AND `rating` <= 5.00),
    ADD CONSTRAINT `chk_vendor_gst_len` CHECK (CHAR_LENGTH(`gst_number`) >= 8);

-- Warehouse capacity must be positive
ALTER TABLE `warehouse`
    ADD CONSTRAINT `chk_warehouse_capacity` CHECK (`capacity` > 0);

-- Product price cannot be negative
ALTER TABLE `product`
    ADD CONSTRAINT `chk_product_price` CHECK (`price` >= 0.00),
    ADD CONSTRAINT `chk_product_status` CHECK (`status` IN ('Active', 'Inactive', 'Out of Stock', 'Discontinued', 'ACTIVE', 'INACTIVE', 'OUT_OF_STOCK', 'DISCONTINUED'));

-- Customer phone validation
ALTER TABLE `customer_phone`
    ADD CONSTRAINT `chk_phone_number_length` CHECK (CHAR_LENGTH(`phone_number`) >= 8),
    ADD CONSTRAINT `chk_phone_type` CHECK (`phone_type` IN ('Mobile', 'Home', 'Work', 'Office', 'Other'));

-- Address validation
ALTER TABLE `address`
    ADD CONSTRAINT `chk_address_type` CHECK (`address_type` IN ('Shipping', 'Billing', 'Home', 'Office', 'Work', 'Other')),
    ADD CONSTRAINT `chk_address_state_len` CHECK (CHAR_LENGTH(`state`) = 2);

-- Tag length check
ALTER TABLE `product_tag`
    ADD CONSTRAINT `chk_tag_length` CHECK (CHAR_LENGTH(`tag`) >= 2);

-- Stock and reorder levels cannot be negative
ALTER TABLE `inventory`
    ADD CONSTRAINT `chk_inventory_stock` CHECK (`stock_quantity` >= 0),
    ADD CONSTRAINT `chk_inventory_reorder` CHECK (`reorder_level` >= 0);

-- Allowed order status values
ALTER TABLE `orders`
    ADD CONSTRAINT `chk_orders_status` CHECK (`status` IN ('PLACED', 'CONFIRMED', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'PROCESSING', 'INVOICED', 'UNAVAILABLE', 'CREATED', 'APPROVED', 'delivered', 'shipped', 'canceled', 'unavailable', 'invoiced', 'processing', 'created', 'approved'));

-- Order item quantity must be at least 1 and price cannot be negative
ALTER TABLE `order_item`
    ADD CONSTRAINT `chk_order_item_quantity` CHECK (`quantity` > 0),
    ADD CONSTRAINT `chk_order_item_price` CHECK (`price_at_purchase` >= 0.00);

-- Payment checks: amount > 0, valid payment modes, valid statuses
ALTER TABLE `payment`
    ADD CONSTRAINT `chk_payment_amount` CHECK (`amount` > 0.00),
    ADD CONSTRAINT `chk_payment_mode` CHECK (`mode` IN ('credit_card', 'boleto', 'voucher', 'debit_card', 'not_defined', 'Credit Card', 'Debit Card', 'UPI', 'Net Banking', 'Cash on Delivery', 'Voucher', 'Wallet')),
    ADD CONSTRAINT `chk_payment_status` CHECK (`status` IN ('Success', 'Pending', 'Failed', 'Refunded', 'SUCCESS', 'PENDING', 'FAILED', 'REFUNDED'));


-- Foreign keys

-- Category self-reference for subcategories
ALTER TABLE `category`
    ADD CONSTRAINT `fk_category_parent`
    FOREIGN KEY (`parent_category_id`) REFERENCES `category` (`category_id`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE;

-- Product belongs to a category and a vendor
ALTER TABLE `product`
    ADD CONSTRAINT `fk_product_category`
    FOREIGN KEY (`category_id`) REFERENCES `category` (`category_id`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
    ADD CONSTRAINT `fk_product_vendor`
    FOREIGN KEY (`vendor_id`) REFERENCES `vendor` (`vendor_id`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE;

-- Delete phones and addresses when customer is removed
ALTER TABLE `customer_phone`
    ADD CONSTRAINT `fk_customer_phone_customer`
    FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE;

ALTER TABLE `address`
    ADD CONSTRAINT `fk_address_customer`
    FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE;

-- Delete tags when product is removed
ALTER TABLE `product_tag`
    ADD CONSTRAINT `fk_product_tag_product`
    FOREIGN KEY (`product_id`) REFERENCES `product` (`product_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE;

-- Inventory links product and warehouse
ALTER TABLE `inventory`
    ADD CONSTRAINT `fk_inventory_product`
    FOREIGN KEY (`product_id`) REFERENCES `product` (`product_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
    ADD CONSTRAINT `fk_inventory_warehouse`
    FOREIGN KEY (`warehouse_id`) REFERENCES `warehouse` (`warehouse_id`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE;

-- Keep customer record if they have existing orders
ALTER TABLE `orders`
    ADD CONSTRAINT `fk_orders_customer`
    FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE;

-- Order items link orders and products
ALTER TABLE `order_item`
    ADD CONSTRAINT `fk_order_item_orders`
    FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
    ADD CONSTRAINT `fk_order_item_product`
    FOREIGN KEY (`product_id`) REFERENCES `product` (`product_id`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE;

-- Payments are tied to orders (cascade on delete)
ALTER TABLE `payment`
    ADD CONSTRAINT `fk_payment_orders`
    FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE;


-- Performance indexes on foreign keys and frequently filtered columns

CREATE INDEX `idx_product_category` ON `product` (`category_id`);
CREATE INDEX `idx_product_vendor` ON `product` (`vendor_id`);
CREATE INDEX `idx_product_tag_name` ON `product_tag` (`tag`);
CREATE INDEX `idx_inventory_warehouse` ON `inventory` (`warehouse_id`);
CREATE INDEX `idx_orders_customer` ON `orders` (`customer_id`);
CREATE INDEX `idx_orders_date` ON `orders` (`order_date`);
CREATE INDEX `idx_orders_status` ON `orders` (`status`);
CREATE INDEX `idx_order_item_product` ON `order_item` (`product_id`);
CREATE INDEX `idx_payment_order` ON `payment` (`order_id`);
CREATE INDEX `idx_payment_mode` ON `payment` (`mode`);
CREATE INDEX `idx_payment_status` ON `payment` (`status`);
