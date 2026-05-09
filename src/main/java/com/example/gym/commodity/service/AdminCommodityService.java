package com.example.gym.commodity.service;

import com.example.gym.admin.service.AdminGuard;
import com.example.gym.commodity.dto.AdminCommoditySaveDTO;
import com.example.gym.commodity.entity.Commodity;
import com.example.gym.commodity.mapper.CommodityMapper;
import com.example.gym.commodity.vo.CommodityDetailVO;
import com.example.gym.commodity.vo.CommodityVO;
import com.example.gym.common.exception.BusinessException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class AdminCommodityService {

    private final AdminGuard adminGuard;
    private final CommodityMapper commodityMapper;

    public AdminCommodityService(AdminGuard adminGuard, CommodityMapper commodityMapper) {
        this.adminGuard = adminGuard;
        this.commodityMapper = commodityMapper;
    }

    public List<CommodityVO> listCommodities() {
        adminGuard.requireAdmin();
        return commodityMapper.findAllCommodities();
    }

    public CommodityDetailVO getCommodityDetail(Long commodityId) {
        adminGuard.requireAdmin();
        Commodity commodity = requireExistingCommodity(commodityId);
        return toDetailVO(commodity);
    }

    @Transactional
    public CommodityDetailVO createCommodity(AdminCommoditySaveDTO dto) {
        adminGuard.requireAdmin();
        validateNameUnique(dto.getName(), null);

        Commodity commodity = new Commodity();
        fillCommodity(commodity, dto);
        commodityMapper.insert(commodity);
        return getCommodityDetail(commodity.getId());
    }

    @Transactional
    public CommodityDetailVO updateCommodity(Long commodityId, AdminCommoditySaveDTO dto) {
        adminGuard.requireAdmin();
        Commodity commodity = requireExistingCommodity(commodityId);
        validateNameUnique(dto.getName(), commodityId);
        fillCommodity(commodity, dto);
        commodityMapper.update(commodity);
        return getCommodityDetail(commodityId);
    }

    @Transactional
    public void updateCommodityStatus(Long commodityId, String status) {
        adminGuard.requireAdmin();
        requireExistingCommodity(commodityId);
        commodityMapper.updateStatus(commodityId, status);
    }

    @Transactional
    public void updateStock(Long commodityId, Integer stock) {
        adminGuard.requireAdmin();
        requireExistingCommodity(commodityId);
        commodityMapper.updateStock(commodityId, stock);
    }

    private Commodity requireExistingCommodity(Long commodityId) {
        Commodity commodity = commodityMapper.findById(commodityId);
        if (commodity == null) {
            throw new BusinessException("commodity does not exist");
        }
        return commodity;
    }

    private void validateNameUnique(String name, Long excludeId) {
        Commodity existing = commodityMapper.findByName(name);
        if (existing != null && (excludeId == null || !existing.getId().equals(excludeId))) {
            throw new BusinessException("commodity name already exists");
        }
    }

    private void fillCommodity(Commodity commodity, AdminCommoditySaveDTO dto) {
        commodity.setName(dto.getName());
        commodity.setCategory(dto.getCategory());
        commodity.setPrice(dto.getPrice());
        commodity.setStock(dto.getStock());
        commodity.setCoverImage(dto.getCoverImage());
        commodity.setDescription(dto.getDescription());
        commodity.setStatus(dto.getStatus());
    }

    private CommodityDetailVO toDetailVO(Commodity commodity) {
        CommodityDetailVO vo = new CommodityDetailVO();
        vo.setId(commodity.getId());
        vo.setName(commodity.getName());
        vo.setCategory(commodity.getCategory());
        vo.setPrice(commodity.getPrice());
        vo.setStock(commodity.getStock());
        vo.setCoverImage(commodity.getCoverImage());
        vo.setDescription(commodity.getDescription());
        vo.setStatus(commodity.getStatus());
        vo.setPurchasable("ON_SALE".equalsIgnoreCase(commodity.getStatus()) && commodity.getStock() > 0);
        return vo;
    }
}
