package com.example.gym.commodity.service;

import com.example.gym.commodity.entity.Commodity;
import com.example.gym.commodity.mapper.CommodityMapper;
import com.example.gym.commodity.vo.CommodityDetailVO;
import com.example.gym.commodity.vo.CommodityVO;
import com.example.gym.common.exception.BusinessException;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class CommodityService {

    private static final String COMMODITY_STATUS_ON_SALE = "ON_SALE";

    private final CommodityMapper commodityMapper;

    public CommodityService(CommodityMapper commodityMapper) {
        this.commodityMapper = commodityMapper;
    }

    public List<CommodityVO> listCommodities() {
        return commodityMapper.findOnSaleCommodities();
    }

    public CommodityDetailVO getCommodityDetail(Long id) {
        Commodity commodity = findExistingCommodity(id);
        CommodityVO detail = commodityMapper.findCommodityDetail(id);
        CommodityDetailVO vo = new CommodityDetailVO();
        vo.setId(detail.getId());
        vo.setName(detail.getName());
        vo.setCategory(detail.getCategory());
        vo.setPrice(detail.getPrice());
        vo.setStock(detail.getStock());
        vo.setCoverImage(detail.getCoverImage());
        vo.setDescription(detail.getDescription());
        vo.setStatus(detail.getStatus());
        vo.setPurchasable(COMMODITY_STATUS_ON_SALE.equalsIgnoreCase(commodity.getStatus()) && commodity.getStock() > 0);
        return vo;
    }

    public Commodity findExistingCommodity(Long id) {
        Commodity commodity = commodityMapper.findById(id);
        if (commodity == null) {
            throw new BusinessException("commodity does not exist");
        }
        return commodity;
    }
}
