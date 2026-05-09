package com.example.gym.order.vo;

import java.math.BigDecimal;

public class OrderItemVO {

    private Long id;
    private Long commodityId;
    private String commodityNameSnapshot;
    private BigDecimal unitPrice;
    private Integer quantity;
    private BigDecimal subtotalAmount;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getCommodityId() {
        return commodityId;
    }

    public void setCommodityId(Long commodityId) {
        this.commodityId = commodityId;
    }

    public String getCommodityNameSnapshot() {
        return commodityNameSnapshot;
    }

    public void setCommodityNameSnapshot(String commodityNameSnapshot) {
        this.commodityNameSnapshot = commodityNameSnapshot;
    }

    public BigDecimal getUnitPrice() {
        return unitPrice;
    }

    public void setUnitPrice(BigDecimal unitPrice) {
        this.unitPrice = unitPrice;
    }

    public Integer getQuantity() {
        return quantity;
    }

    public void setQuantity(Integer quantity) {
        this.quantity = quantity;
    }

    public BigDecimal getSubtotalAmount() {
        return subtotalAmount;
    }

    public void setSubtotalAmount(BigDecimal subtotalAmount) {
        this.subtotalAmount = subtotalAmount;
    }
}
