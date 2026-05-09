export const MEMBER_STATUS_ACTIVE = "ACTIVE";
export const MEMBER_STATUS_PENDING = "PENDING";
export const MEMBER_STATUS_DISABLED = "DISABLED";

export function isActiveMemberStatus(status) {
  return status === MEMBER_STATUS_ACTIVE;
}

export function isRestrictedMemberStatus(status) {
  return Boolean(status) && status !== MEMBER_STATUS_ACTIVE;
}

export function memberStatusLabel(status) {
  if (status === MEMBER_STATUS_ACTIVE) {
    return "正常";
  }
  if (status === MEMBER_STATUS_PENDING) {
    return "未启用";
  }
  if (status === MEMBER_STATUS_DISABLED) {
    return "停用";
  }
  return status || "--";
}
