package com.example.gym.cart.service;

import com.example.gym.auth.support.AuthConstants;
import com.example.gym.auth.support.AuthUser;
import com.example.gym.auth.support.UserContext;
import com.example.gym.cart.dto.AddCartItemDTO;
import com.example.gym.cart.dto.UpdateCartItemDTO;
import com.example.gym.cart.entity.CartItem;
import com.example.gym.cart.mapper.CartItemMapper;
import com.example.gym.cart.vo.CartItemVO;
import com.example.gym.commodity.entity.Commodity;
import com.example.gym.commodity.service.CommodityService;
import com.example.gym.common.api.ResultCode;
import com.example.gym.common.exception.BusinessException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class CartService {

    private static final String COMMODITY_STATUS_ON_SALE = "ON_SALE";

    private final CartItemMapper cartItemMapper;
    private final CommodityService commodityService;

    public CartService(CartItemMapper cartItemMapper, CommodityService commodityService) {
        this.cartItemMapper = cartItemMapper;
        this.commodityService = commodityService;
    }

    @Transactional
    public CartItemVO addCartItem(AddCartItemDTO dto) {
        AuthUser currentUser = requireMemberUser();
        Commodity commodity = validateCommodityAvailable(dto.getCommodityId());

        CartItem existing = cartItemMapper.findByMemberIdAndCommodityId(currentUser.getUserId(), commodity.getId());
        if (existing != null) {
            int newQuantity = existing.getQuantity() + dto.getQuantity();
            validateStock(commodity, newQuantity);
            existing.setQuantity(newQuantity);
            existing.setSelected(Boolean.TRUE);
            cartItemMapper.update(existing);
        } else {
            validateStock(commodity, dto.getQuantity());
            CartItem cartItem = new CartItem();
            cartItem.setMemberId(currentUser.getUserId());
            cartItem.setCommodityId(commodity.getId());
            cartItem.setQuantity(dto.getQuantity());
            cartItem.setSelected(Boolean.TRUE);
            cartItemMapper.insert(cartItem);
        }

        return listMyCartItems().stream()
                .filter(item -> item.getCommodityId().equals(commodity.getId()))
                .findFirst()
                .orElseThrow(() -> new BusinessException("failed to load cart item"));
    }

    public List<CartItemVO> listMyCartItems() {
        AuthUser currentUser = requireMemberUser();
        return cartItemMapper.findByMemberId(currentUser.getUserId());
    }

    @Transactional
    public CartItemVO updateCartItem(Long cartItemId, UpdateCartItemDTO dto) {
        AuthUser currentUser = requireMemberUser();
        CartItem cartItem = findOwnedCartItem(currentUser.getUserId(), cartItemId);
        Commodity commodity = commodityService.findExistingCommodity(cartItem.getCommodityId());
        validateCommodityAvailableForCart(commodity);
        validateStock(commodity, dto.getQuantity());

        cartItem.setQuantity(dto.getQuantity());
        cartItem.setSelected(dto.getSelected());
        cartItemMapper.update(cartItem);
        return listMyCartItems().stream()
                .filter(item -> item.getId().equals(cartItemId))
                .findFirst()
                .orElseThrow(() -> new BusinessException("failed to load cart item"));
    }

    @Transactional
    public void deleteCartItem(Long cartItemId) {
        AuthUser currentUser = requireMemberUser();
        findOwnedCartItem(currentUser.getUserId(), cartItemId);
        cartItemMapper.deleteById(cartItemId);
    }

    public List<CartItem> getOwnedCartItemsByIds(Long memberId, List<Long> cartItemIds) {
        List<CartItem> cartItems = cartItemMapper.findByMemberIdAndIds(memberId, cartItemIds);
        if (cartItems.size() != cartItemIds.size()) {
            throw new BusinessException("some cart items do not belong to current user or do not exist");
        }
        return cartItems;
    }

    @Transactional
    public void deleteCartItems(List<Long> cartItemIds) {
        for (Long cartItemId : cartItemIds) {
            cartItemMapper.deleteById(cartItemId);
        }
    }

    private CartItem findOwnedCartItem(Long memberId, Long cartItemId) {
        CartItem cartItem = cartItemMapper.findById(cartItemId);
        if (cartItem == null) {
            throw new BusinessException("cart item does not exist");
        }
        if (!cartItem.getMemberId().equals(memberId)) {
            throw new BusinessException(ResultCode.FORBIDDEN, "you can only operate your own cart items");
        }
        return cartItem;
    }

    private Commodity validateCommodityAvailable(Long commodityId) {
        Commodity commodity = commodityService.findExistingCommodity(commodityId);
        validateCommodityAvailableForCart(commodity);
        return commodity;
    }

    private void validateCommodityAvailableForCart(Commodity commodity) {
        if (!COMMODITY_STATUS_ON_SALE.equalsIgnoreCase(commodity.getStatus())) {
            throw new BusinessException("commodity is not available for sale");
        }
    }

    private void validateStock(Commodity commodity, int quantity) {
        if (commodity.getStock() < quantity) {
            throw new BusinessException("commodity stock is insufficient");
        }
    }

    private AuthUser requireMemberUser() {
        AuthUser authUser = UserContext.get();
        if (authUser == null) {
            throw new BusinessException(ResultCode.UNAUTHORIZED, "login required");
        }
        if (!AuthConstants.USER_TYPE_MEMBER.equals(authUser.getUserType())) {
            throw new BusinessException(ResultCode.FORBIDDEN, "member login required");
        }
        return authUser;
    }
}
