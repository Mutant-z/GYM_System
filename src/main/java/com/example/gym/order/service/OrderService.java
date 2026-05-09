package com.example.gym.order.service;

import com.example.gym.auth.support.AuthConstants;
import com.example.gym.auth.support.AuthUser;
import com.example.gym.auth.support.UserContext;
import com.example.gym.cart.entity.CartItem;
import com.example.gym.cart.service.CartService;
import com.example.gym.commodity.entity.Commodity;
import com.example.gym.commodity.mapper.CommodityMapper;
import com.example.gym.commodity.service.CommodityService;
import com.example.gym.common.api.ResultCode;
import com.example.gym.common.exception.BusinessException;
import com.example.gym.common.util.IdGenerator;
import com.example.gym.order.dto.CreateOrderDTO;
import com.example.gym.order.entity.CommodityOrder;
import com.example.gym.order.entity.CommodityOrderItem;
import com.example.gym.order.mapper.OrderMapper;
import com.example.gym.order.vo.OrderDetailVO;
import com.example.gym.order.vo.OrderItemVO;
import com.example.gym.order.vo.OrderVO;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class OrderService {

    private static final Logger log = LoggerFactory.getLogger(OrderService.class);
    private static final String ORDER_STATUS_CREATED = "CREATED";
    private static final String ORDER_STATUS_CANCELED = "CANCELED";
    private static final String PAYMENT_STATUS_UNPAID = "UNPAID";
    private static final String PAYMENT_STATUS_CANCELED = "CANCELED";
    private static final String COMMODITY_STATUS_ON_SALE = "ON_SALE";

    private final OrderMapper orderMapper;
    private final CartService cartService;
    private final CommodityService commodityService;
    private final CommodityMapper commodityMapper;

    public OrderService(
            OrderMapper orderMapper,
            CartService cartService,
            CommodityService commodityService,
            CommodityMapper commodityMapper
    ) {
        this.orderMapper = orderMapper;
        this.cartService = cartService;
        this.commodityService = commodityService;
        this.commodityMapper = commodityMapper;
    }

    @Transactional
    public OrderDetailVO createOrder(CreateOrderDTO dto) {
        AuthUser currentUser = requireMemberUser();
        List<CartItem> cartItems = cartService.getOwnedCartItemsByIds(currentUser.getUserId(), dto.getCartItemIds());
        if (cartItems.isEmpty()) {
            throw new BusinessException("no cart items selected");
        }

        List<CommodityOrderItem> orderItems = new ArrayList<>();
        BigDecimal totalAmount = BigDecimal.ZERO;

        for (CartItem cartItem : cartItems) {
            if (!Boolean.TRUE.equals(cartItem.getSelected())) {
                throw new BusinessException("all order cart items must be selected");
            }

            Commodity commodity = commodityService.findExistingCommodity(cartItem.getCommodityId());
            if (!COMMODITY_STATUS_ON_SALE.equalsIgnoreCase(commodity.getStatus())) {
                throw new BusinessException("commodity is not available for sale");
            }
            if (commodity.getStock() < cartItem.getQuantity()) {
                throw new BusinessException("commodity stock is insufficient");
            }

            BigDecimal subtotal = commodity.getPrice().multiply(BigDecimal.valueOf(cartItem.getQuantity()));
            totalAmount = totalAmount.add(subtotal);

            CommodityOrderItem orderItem = new CommodityOrderItem();
            orderItem.setCommodityId(commodity.getId());
            orderItem.setCommodityNameSnapshot(commodity.getName());
            orderItem.setUnitPrice(commodity.getPrice());
            orderItem.setQuantity(cartItem.getQuantity());
            orderItem.setSubtotalAmount(subtotal);
            orderItems.add(orderItem);
        }

        CommodityOrder order = new CommodityOrder();
        order.setOrderNo(IdGenerator.businessId("od"));
        order.setMemberId(currentUser.getUserId());
        order.setTotalAmount(totalAmount);
        order.setPayAmount(totalAmount);
        order.setStatus(ORDER_STATUS_CREATED);
        order.setPaymentStatus(PAYMENT_STATUS_UNPAID);
        order.setReceiverName(dto.getReceiverName());
        order.setReceiverPhone(dto.getReceiverPhone());
        order.setReceiverAddress(dto.getReceiverAddress());
        orderMapper.insertOrder(order);

        for (int i = 0; i < orderItems.size(); i++) {
            CommodityOrderItem orderItem = orderItems.get(i);
            orderItem.setOrderId(order.getId());
            orderMapper.insertOrderItem(orderItem);
            CartItem cartItem = cartItems.get(i);
            int updated = commodityMapper.decreaseStock(cartItem.getCommodityId(), cartItem.getQuantity());
            if (updated == 0) {
                throw new BusinessException("commodity stock is insufficient");
            }
        }

        cartService.deleteCartItems(dto.getCartItemIds());
        return getOrderDetail(order.getId());
    }

    public List<OrderVO> listOrders() {
        AuthUser currentUser = requireCurrentUser();
        log.info(
                "Listing orders for userId={}, userType={}, username={}",
                currentUser.getUserId(),
                currentUser.getUserType(),
                currentUser.getUsername()
        );
        if (isAdminUser(currentUser)) {
            List<OrderVO> orders = orderMapper.findAllOrders();
            log.info("Order list query finished for admin userId={}, count={}", currentUser.getUserId(), orders.size());
            return orders;
        }
        List<OrderVO> orders = orderMapper.findByMemberId(currentUser.getUserId());
        log.info("Order list query finished for member userId={}, count={}", currentUser.getUserId(), orders.size());
        return orders;
    }

    @Transactional
    public boolean cancelUnpaidOrder(Long orderId) {
        int updated = orderMapper.markOrderCanceledIfUnpaid(orderId, ORDER_STATUS_CANCELED, PAYMENT_STATUS_CANCELED);
        if (updated == 0) {
            return false;
        }

        List<OrderItemVO> items = orderMapper.findItemsByOrderId(orderId);
        for (OrderItemVO item : items) {
            commodityMapper.increaseStock(item.getCommodityId(), item.getQuantity());
        }
        return true;
    }

    @Transactional
    public void cancelOrder(Long orderId) {
        AuthUser currentUser = requireMemberUser();
        CommodityOrder order = orderMapper.findById(orderId);
        if (order == null) {
            throw new BusinessException("order does not exist");
        }
        if (!order.getMemberId().equals(currentUser.getUserId())) {
            throw new BusinessException(ResultCode.FORBIDDEN, "you can only cancel your own orders");
        }
        if (!ORDER_STATUS_CREATED.equalsIgnoreCase(order.getStatus())
                || !PAYMENT_STATUS_UNPAID.equalsIgnoreCase(order.getPaymentStatus())) {
            throw new BusinessException("current order cannot be canceled");
        }
        if (!cancelUnpaidOrder(orderId)) {
            throw new BusinessException("current order cannot be canceled");
        }
    }

    public OrderDetailVO getOrderDetail(Long orderId) {
        AuthUser currentUser = requireCurrentUser();
        log.info(
                "Loading order detail: orderId={}, userId={}, userType={}",
                orderId,
                currentUser.getUserId(),
                currentUser.getUserType()
        );
        CommodityOrder order = orderMapper.findById(orderId);
        if (order == null) {
            throw new BusinessException("order does not exist");
        }
        if (!isAdminUser(currentUser) && !order.getMemberId().equals(currentUser.getUserId())) {
            throw new BusinessException(ResultCode.FORBIDDEN, "you can only view your own orders");
        }

        OrderVO orderVO = orderMapper.findOrderVOById(orderId);
        List<OrderItemVO> items = orderMapper.findItemsByOrderId(orderId);
        log.info(
                "Order detail loaded: orderId={}, orderNo={}, itemCount={}",
                orderId,
                orderVO.getOrderNo(),
                items.size()
        );
        OrderDetailVO detailVO = new OrderDetailVO();
        detailVO.setId(orderVO.getId());
        detailVO.setOrderNo(orderVO.getOrderNo());
        detailVO.setMemberId(orderVO.getMemberId());
        detailVO.setMemberUsername(orderVO.getMemberUsername());
        detailVO.setMemberDisplayName(orderVO.getMemberDisplayName());
        detailVO.setTotalAmount(orderVO.getTotalAmount());
        detailVO.setPayAmount(orderVO.getPayAmount());
        detailVO.setStatus(orderVO.getStatus());
        detailVO.setPaymentStatus(orderVO.getPaymentStatus());
        detailVO.setPaymentTime(orderVO.getPaymentTime());
        detailVO.setReceiverName(orderVO.getReceiverName());
        detailVO.setReceiverPhone(orderVO.getReceiverPhone());
        detailVO.setReceiverAddress(orderVO.getReceiverAddress());
        detailVO.setCreatedAt(orderVO.getCreatedAt());
        detailVO.setItems(items);
        return detailVO;
    }

    private AuthUser requireCurrentUser() {
        AuthUser authUser = UserContext.get();
        if (authUser == null) {
            throw new BusinessException(ResultCode.UNAUTHORIZED, "login required");
        }
        return authUser;
    }

    private AuthUser requireMemberUser() {
        AuthUser authUser = requireCurrentUser();
        if (!AuthConstants.USER_TYPE_MEMBER.equals(authUser.getUserType())) {
            throw new BusinessException(ResultCode.FORBIDDEN, "member login required");
        }
        return authUser;
    }

    private boolean isAdminUser(AuthUser authUser) {
        return AuthConstants.USER_TYPE_ADMIN.equals(authUser.getUserType());
    }
}
