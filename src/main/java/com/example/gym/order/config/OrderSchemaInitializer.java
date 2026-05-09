package com.example.gym.order.config;

import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class OrderSchemaInitializer {

    private static final Logger log = LoggerFactory.getLogger(OrderSchemaInitializer.class);

    private final JdbcTemplate jdbcTemplate;

    public OrderSchemaInitializer(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @PostConstruct
    public void initialize() {
        ensureCommodityOrderTable();
        ensureCommodityOrderItemTable();
        ensureCommodityOrderColumns();
        ensureCommodityOrderItemColumns();
    }

    private void ensureCommodityOrderTable() {
        jdbcTemplate.execute("""
                CREATE TABLE IF NOT EXISTS commodity_order (
                  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '订单ID',
                  order_no VARCHAR(64) NOT NULL COMMENT '订单编号',
                  member_id BIGINT NOT NULL COMMENT '会员ID',
                  total_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '订单总额',
                  pay_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '支付金额',
                  status VARCHAR(32) NOT NULL DEFAULT 'CREATED' COMMENT '订单状态',
                  payment_status VARCHAR(32) NOT NULL DEFAULT 'UNPAID' COMMENT '支付状态',
                  payment_time DATETIME DEFAULT NULL COMMENT '支付时间',
                  receiver_name VARCHAR(64) NOT NULL COMMENT '收货人',
                  receiver_phone VARCHAR(20) NOT NULL COMMENT '联系电话',
                  receiver_address VARCHAR(255) NOT NULL COMMENT '收货地址',
                  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                  PRIMARY KEY (id),
                  UNIQUE KEY uk_commodity_order_no (order_no),
                  KEY idx_commodity_order_member (member_id),
                  KEY idx_commodity_order_status (status),
                  KEY idx_commodity_order_payment_status (payment_status),
                  CONSTRAINT fk_commodity_order_member FOREIGN KEY (member_id) REFERENCES member (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品订单表'
                """);
        log.info("Ensured table exists: commodity_order");
    }

    private void ensureCommodityOrderItemTable() {
        jdbcTemplate.execute("""
                CREATE TABLE IF NOT EXISTS commodity_order_item (
                  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '订单明细ID',
                  order_id BIGINT NOT NULL COMMENT '订单ID',
                  commodity_id BIGINT NOT NULL COMMENT '商品ID',
                  commodity_name_snapshot VARCHAR(128) NOT NULL COMMENT '商品名快照',
                  unit_price DECIMAL(10,2) NOT NULL COMMENT '下单单价',
                  quantity INT NOT NULL COMMENT '购买数量',
                  subtotal_amount DECIMAL(10,2) NOT NULL COMMENT '小计金额',
                  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                  PRIMARY KEY (id),
                  KEY idx_order_item_order (order_id),
                  KEY idx_order_item_commodity (commodity_id),
                  CONSTRAINT fk_order_item_order FOREIGN KEY (order_id) REFERENCES commodity_order (id),
                  CONSTRAINT fk_order_item_commodity FOREIGN KEY (commodity_id) REFERENCES commodity (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品订单明细表'
                """);
        log.info("Ensured table exists: commodity_order_item");
    }

    private void ensureCommodityOrderColumns() {
        ensureColumn(
                "commodity_order",
                "payment_time",
                "DATETIME DEFAULT NULL COMMENT '支付时间'"
        );
        ensureColumn(
                "commodity_order",
                "receiver_name",
                "VARCHAR(64) NOT NULL COMMENT '收货人'"
        );
        ensureColumn(
                "commodity_order",
                "receiver_phone",
                "VARCHAR(20) NOT NULL COMMENT '联系电话'"
        );
        ensureColumn(
                "commodity_order",
                "receiver_address",
                "VARCHAR(255) NOT NULL COMMENT '收货地址'"
        );
        ensureColumn(
                "commodity_order",
                "created_at",
                "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'"
        );
        ensureColumn(
                "commodity_order",
                "updated_at",
                "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'"
        );
    }

    private void ensureCommodityOrderItemColumns() {
        ensureColumn(
                "commodity_order_item",
                "commodity_name_snapshot",
                "VARCHAR(128) NOT NULL COMMENT '商品名快照'"
        );
        ensureColumn(
                "commodity_order_item",
                "unit_price",
                "DECIMAL(10,2) NOT NULL COMMENT '下单单价'"
        );
        ensureColumn(
                "commodity_order_item",
                "quantity",
                "INT NOT NULL COMMENT '购买数量'"
        );
        ensureColumn(
                "commodity_order_item",
                "subtotal_amount",
                "DECIMAL(10,2) NOT NULL COMMENT '小计金额'"
        );
        ensureColumn(
                "commodity_order_item",
                "created_at",
                "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'"
        );
    }

    private void ensureColumn(String tableName, String columnName, String definition) {
        if (hasColumn(tableName, columnName)) {
            return;
        }
        jdbcTemplate.execute("ALTER TABLE " + tableName + " ADD COLUMN " + columnName + " " + definition);
        log.info("Added missing column {}.{}", tableName, columnName);
    }

    private boolean hasColumn(String tableName, String columnName) {
        List<Integer> rows = jdbcTemplate.queryForList(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                  AND table_name = ?
                  AND column_name = ?
                LIMIT 1
                """,
                Integer.class,
                tableName,
                columnName
        );
        return !rows.isEmpty();
    }
}
