CREATE DATABASE IF NOT EXISTS gym_system
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE gym_system;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS ai_message;
DROP TABLE IF EXISTS ai_session;
DROP TABLE IF EXISTS commodity_order_item;
DROP TABLE IF EXISTS commodity_order;
DROP TABLE IF EXISTS cart_item;
DROP TABLE IF EXISTS commodity;
DROP TABLE IF EXISTS course_enrollment;
DROP TABLE IF EXISTS course;
DROP TABLE IF EXISTS gym_booking;
DROP TABLE IF EXISTS equipment;
DROP TABLE IF EXISTS gym_room;
DROP TABLE IF EXISTS employee;
DROP TABLE IF EXISTS admin;
DROP TABLE IF EXISTS member;

CREATE TABLE member (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '会员ID',
  username VARCHAR(64) NOT NULL COMMENT '登录账号',
  password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
  nickname VARCHAR(64) NOT NULL COMMENT '昵称',
  real_name VARCHAR(64) DEFAULT NULL COMMENT '真实姓名',
  gender VARCHAR(16) DEFAULT NULL COMMENT '性别',
  phone VARCHAR(20) NOT NULL COMMENT '手机号',
  email VARCHAR(128) DEFAULT NULL COMMENT '邮箱',
  birthday DATE DEFAULT NULL COMMENT '生日',
  height_cm DECIMAL(5,2) DEFAULT NULL COMMENT '身高(cm)',
  weight_kg DECIMAL(5,2) DEFAULT NULL COMMENT '体重(kg)',
  fitness_goal VARCHAR(255) DEFAULT NULL COMMENT '健身目标',
  preferred_training_time VARCHAR(64) DEFAULT NULL COMMENT '偏好训练时间',
  injury_notes VARCHAR(255) DEFAULT NULL COMMENT '伤病备注',
  membership_status VARCHAR(32) NOT NULL DEFAULT 'PENDING' COMMENT '会员状态',
  last_login_at DATETIME DEFAULT NULL COMMENT '最后登录时间',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  deleted TINYINT(1) NOT NULL DEFAULT 0 COMMENT '逻辑删除标记',
  PRIMARY KEY (id),
  UNIQUE KEY uk_member_username (username),
  UNIQUE KEY uk_member_phone (phone),
  KEY idx_member_status (membership_status),
  KEY idx_member_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会员表';

CREATE TABLE admin (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '管理员ID',
  username VARCHAR(64) NOT NULL COMMENT '登录账号',
  password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
  name VARCHAR(64) NOT NULL COMMENT '姓名',
  phone VARCHAR(20) DEFAULT NULL COMMENT '手机号',
  role VARCHAR(32) NOT NULL DEFAULT 'OPERATOR' COMMENT '角色',
  status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE' COMMENT '状态',
  last_login_at DATETIME DEFAULT NULL COMMENT '最后登录时间',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_admin_username (username),
  KEY idx_admin_role (role),
  KEY idx_admin_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='管理员表';

CREATE TABLE employee (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '员工ID',
  name VARCHAR(64) NOT NULL COMMENT '姓名',
  phone VARCHAR(20) DEFAULT NULL COMMENT '手机号',
  gender VARCHAR(16) DEFAULT NULL COMMENT '性别',
  position VARCHAR(32) NOT NULL COMMENT '岗位',
  specialty VARCHAR(255) DEFAULT NULL COMMENT '特长',
  hire_date DATE DEFAULT NULL COMMENT '入职日期',
  status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE' COMMENT '状态',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_employee_position (position),
  KEY idx_employee_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='员工表';

CREATE TABLE gym_room (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '健身室ID',
  name VARCHAR(128) NOT NULL COMMENT '健身室名称',
  location VARCHAR(255) DEFAULT NULL COMMENT '位置',
  capacity INT NOT NULL COMMENT '容纳人数',
  open_time TIME DEFAULT NULL COMMENT '开放时间',
  close_time TIME DEFAULT NULL COMMENT '关闭时间',
  status VARCHAR(32) NOT NULL DEFAULT 'OPEN' COMMENT '状态',
  description VARCHAR(500) DEFAULT NULL COMMENT '描述',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_gym_room_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='健身室表';

CREATE TABLE equipment (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '器械ID',
  gym_room_id BIGINT DEFAULT NULL COMMENT '所属健身室ID',
  name VARCHAR(128) NOT NULL COMMENT '器械名称',
  category VARCHAR(64) DEFAULT NULL COMMENT '器械分类',
  brand VARCHAR(64) DEFAULT NULL COMMENT '品牌',
  quantity INT NOT NULL DEFAULT 1 COMMENT '数量',
  status VARCHAR(32) NOT NULL DEFAULT 'AVAILABLE' COMMENT '状态',
  purchase_date DATE DEFAULT NULL COMMENT '采购日期',
  description VARCHAR(500) DEFAULT NULL COMMENT '描述',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_equipment_room (gym_room_id),
  KEY idx_equipment_status (status),
  CONSTRAINT fk_equipment_room FOREIGN KEY (gym_room_id) REFERENCES gym_room (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='器械表';

CREATE TABLE gym_booking (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '预约ID',
  booking_no VARCHAR(64) NOT NULL COMMENT '预约编号',
  member_id BIGINT NOT NULL COMMENT '会员ID',
  gym_room_id BIGINT NOT NULL COMMENT '健身室ID',
  booking_date DATE NOT NULL COMMENT '预约日期',
  start_time DATETIME NOT NULL COMMENT '开始时间',
  end_time DATETIME NOT NULL COMMENT '结束时间',
  duration_minutes INT NOT NULL COMMENT '预约时长(分钟)',
  head_count INT NOT NULL DEFAULT 1 COMMENT '预约人数',
  status VARCHAR(32) NOT NULL DEFAULT 'CONFIRMED' COMMENT '预约状态',
  remark VARCHAR(255) DEFAULT NULL COMMENT '备注',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_gym_booking_no (booking_no),
  KEY idx_gym_booking_member (member_id),
  KEY idx_gym_booking_room_time (gym_room_id, start_time, end_time),
  KEY idx_gym_booking_date (booking_date),
  KEY idx_gym_booking_status (status),
  CONSTRAINT fk_gym_booking_member FOREIGN KEY (member_id) REFERENCES member (id),
  CONSTRAINT fk_gym_booking_room FOREIGN KEY (gym_room_id) REFERENCES gym_room (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='健身室预约表';

CREATE TABLE course (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '课程ID',
  name VARCHAR(128) NOT NULL COMMENT '课程名称',
  coach_id BIGINT DEFAULT NULL COMMENT '教练ID',
  gym_room_id BIGINT DEFAULT NULL COMMENT '上课健身室ID',
  course_type VARCHAR(64) DEFAULT NULL COMMENT '课程类型',
  start_time DATETIME NOT NULL COMMENT '开课时间',
  end_time DATETIME NOT NULL COMMENT '结束时间',
  capacity INT NOT NULL DEFAULT 20 COMMENT '容量',
  price DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '课程价格',
  description VARCHAR(500) DEFAULT NULL COMMENT '课程描述',
  status VARCHAR(32) NOT NULL DEFAULT 'OPEN' COMMENT '课程状态',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_course_coach (coach_id),
  KEY idx_course_room (gym_room_id),
  KEY idx_course_time (start_time, end_time),
  KEY idx_course_status (status),
  CONSTRAINT fk_course_coach FOREIGN KEY (coach_id) REFERENCES employee (id),
  CONSTRAINT fk_course_room FOREIGN KEY (gym_room_id) REFERENCES gym_room (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课程表';

CREATE TABLE course_enrollment (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '报名ID',
  enrollment_no VARCHAR(64) NOT NULL COMMENT '报名编号',
  member_id BIGINT NOT NULL COMMENT '会员ID',
  course_id BIGINT NOT NULL COMMENT '课程ID',
  status VARCHAR(32) NOT NULL DEFAULT 'ENROLLED' COMMENT '报名状态',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_course_enrollment_no (enrollment_no),
  UNIQUE KEY uk_course_member (member_id, course_id),
  KEY idx_course_enrollment_course (course_id),
  KEY idx_course_enrollment_status (status),
  CONSTRAINT fk_course_enrollment_member FOREIGN KEY (member_id) REFERENCES member (id),
  CONSTRAINT fk_course_enrollment_course FOREIGN KEY (course_id) REFERENCES course (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课程报名表';

CREATE TABLE commodity (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '商品ID',
  name VARCHAR(128) NOT NULL COMMENT '商品名称',
  category VARCHAR(64) DEFAULT NULL COMMENT '商品分类',
  price DECIMAL(10,2) NOT NULL COMMENT '单价',
  stock INT NOT NULL DEFAULT 0 COMMENT '库存',
  cover_image VARCHAR(255) DEFAULT NULL COMMENT '封面图',
  description VARCHAR(500) DEFAULT NULL COMMENT '商品描述',
  status VARCHAR(32) NOT NULL DEFAULT 'ON_SALE' COMMENT '商品状态',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_commodity_category (category),
  KEY idx_commodity_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品表';

CREATE TABLE cart_item (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '购物车项ID',
  member_id BIGINT NOT NULL COMMENT '会员ID',
  commodity_id BIGINT NOT NULL COMMENT '商品ID',
  quantity INT NOT NULL DEFAULT 1 COMMENT '数量',
  selected TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否勾选',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_cart_member_commodity (member_id, commodity_id),
  KEY idx_cart_member (member_id),
  CONSTRAINT fk_cart_member FOREIGN KEY (member_id) REFERENCES member (id),
  CONSTRAINT fk_cart_commodity FOREIGN KEY (commodity_id) REFERENCES commodity (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='购物车项表';

CREATE TABLE commodity_order (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品订单表';

CREATE TABLE commodity_order_item (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品订单明细表';

CREATE TABLE ai_session (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT 'AI会话ID',
  member_id BIGINT DEFAULT NULL COMMENT '会员ID',
  session_key VARCHAR(128) NOT NULL COMMENT '会话标识',
  source VARCHAR(32) NOT NULL DEFAULT 'LANGCHAIN' COMMENT '来源',
  status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE' COMMENT '会话状态',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_ai_session_key (session_key),
  KEY idx_ai_session_member (member_id),
  CONSTRAINT fk_ai_session_member FOREIGN KEY (member_id) REFERENCES member (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI会话表';

CREATE TABLE ai_message (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT 'AI消息ID',
  session_id BIGINT NOT NULL COMMENT '会话ID',
  role VARCHAR(32) NOT NULL COMMENT '消息角色',
  content TEXT NOT NULL COMMENT '消息内容',
  token_usage INT DEFAULT NULL COMMENT 'token消耗',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_ai_message_session (session_id),
  KEY idx_ai_message_role (role),
  CONSTRAINT fk_ai_message_session FOREIGN KEY (session_id) REFERENCES ai_session (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI消息表';

INSERT INTO member (
  id, username, password_hash, nickname, real_name, gender, phone, email, birthday,
  height_cm, weight_kg, fitness_goal, preferred_training_time, injury_notes,
  membership_status, last_login_at, created_at, updated_at, deleted
) VALUES
  (1, 'member001', '123456', '小强', '张强', '男', '13800000001', 'member001@gym.local', '1996-03-12', 176.00, 72.50, '减脂塑形', '工作日晚上', '无', 'ACTIVE', '2026-04-16 20:15:00', '2026-03-01 09:00:00', '2026-04-16 20:15:00', 0),
  (2, 'member002', '123456', '阿敏', '李敏', '女', '13800000002', 'member002@gym.local', '1998-07-08', 165.00, 54.20, '提升心肺', '周末上午', '膝盖旧伤，避免高冲击', 'ACTIVE', '2026-04-15 19:30:00', '2026-03-02 10:10:00', '2026-04-15 19:30:00', 0),
  (3, 'member003', '123456', '老王', '王伟', '男', '13800000003', 'member003@gym.local', '1990-11-20', 180.00, 82.00, '增肌训练', '工作日午休', '腰椎不适', 'ACTIVE', '2026-04-14 12:20:00', '2026-03-04 14:20:00', '2026-04-14 12:20:00', 0),
  (4, 'member004', '123456', '小雨', '王雨', '女', '13800000004', 'member004@gym.local', '2000-05-18', 168.00, 56.00, '体态改善', '周末下午', '无', 'ACTIVE', '2026-04-13 16:40:00', '2026-03-06 16:30:00', '2026-04-13 16:40:00', 0),
  (5, 'member005', '123456', '大海', '刘海', '男', '13800000005', 'member005@gym.local', '1994-09-28', 173.50, 75.00, '力量提升', '周末下午', '无', 'DISABLED', '2026-03-28 20:15:00', '2026-03-16 10:10:00', '2026-04-09 11:30:00', 0),
  (6, 'member006', '123456', '晨晨', '陈晨', '女', '13800000006', 'member006@gym.local', '1999-01-03', 162.00, 50.80, '瑜伽拉伸', '工作日早晨', '肩颈紧张', 'PENDING', NULL, '2026-04-01 08:30:00', '2026-04-01 08:30:00', 0),
  (7, 'member007', '123456', '阿杰', '赵杰', '男', '13800000007', 'member007@gym.local', '1992-12-05', 178.00, 78.30, '体能恢复', '工作日晚上', '脚踝扭伤恢复期', 'ACTIVE', '2026-04-16 21:05:00', '2026-04-03 11:20:00', '2026-04-16 21:05:00', 0),
  (8, 'member008', '123456', '安安', '周安', '女', '13800000008', 'member008@gym.local', '1997-08-22', 170.00, 59.60, '马拉松备赛', '周末清晨', '无', 'ACTIVE', '2026-04-17 08:10:00', '2026-04-05 09:45:00', '2026-04-17 08:10:00', 0);

INSERT INTO admin (
  id, username, password_hash, name, phone, role, status, last_login_at, created_at, updated_at
) VALUES
  (1, 'admin001', '123456', '系统管理员', '13900000001', 'SUPER_ADMIN', 'ACTIVE', '2026-04-17 09:10:00', '2026-03-01 08:00:00', '2026-04-17 09:10:00'),
  (2, 'admin002', '123456', '运营管理员', '13900000002', 'OPERATOR', 'ACTIVE', '2026-04-16 18:20:00', '2026-03-05 09:30:00', '2026-04-16 18:20:00');

INSERT INTO employee (
  id, name, phone, gender, position, specialty, hire_date, status, created_at, updated_at
) VALUES
  (1, '陈教练', '13700000001', '男', 'COACH', '力量训练、体态纠正', '2024-05-01', 'ACTIVE', '2026-03-01 09:00:00', '2026-03-01 09:00:00'),
  (2, '林教练', '13700000002', '女', 'COACH', '普拉提、瑜伽', '2023-09-15', 'ACTIVE', '2026-03-01 09:05:00', '2026-03-01 09:05:00'),
  (3, '何教练', '13700000003', '男', 'COACH', '搏击燃脂、HIIT', '2024-01-10', 'ACTIVE', '2026-03-01 09:10:00', '2026-03-01 09:10:00'),
  (4, '周前台', '13700000004', '女', 'RECEPTION', '会员接待、课程安排', '2025-02-18', 'ACTIVE', '2026-03-01 09:15:00', '2026-03-01 09:15:00'),
  (5, '吴维护', '13700000005', '男', 'MAINTENANCE', '器械巡检、场地维护', '2022-11-20', 'ACTIVE', '2026-03-01 09:20:00', '2026-03-01 09:20:00'),
  (6, '郑教练', '13700000006', '女', 'COACH', '动感单车、耐力训练', '2025-06-12', 'INACTIVE', '2026-03-01 09:25:00', '2026-04-12 18:00:00');

INSERT INTO gym_room (
  id, name, location, capacity, open_time, close_time, status, description, created_at, updated_at
) VALUES
  (1, '功能训练区', 'B栋1层南侧', 16, '08:30:00', '22:30:00', 'OPEN', '适合核心、功能性和康复训练。', '2026-03-01 10:00:00', '2026-04-10 09:20:00'),
  (2, '动感单车室', 'B栋2层', 30, '07:00:00', '23:00:00', 'OPEN', '配备智能单车和节奏灯光。', '2026-03-01 10:05:00', '2026-04-10 09:20:00'),
  (3, '私教训练室', 'A栋1层西侧', 8, '09:00:00', '21:00:00', 'OPEN', '适合一对一私教课程。', '2026-03-01 10:10:00', '2026-04-10 09:20:00'),
  (4, '瑜伽普拉提室', 'A栋2层东侧', 20, '08:00:00', '22:00:00', 'OPEN', '安静明亮，配备瑜伽垫和普拉提圈。', '2026-03-01 10:15:00', '2026-04-10 09:20:00'),
  (5, '力量器械区', 'C栋1层', 24, '06:30:00', '23:30:00', 'OPEN', '深蹲架、卧推架和自由力量器械齐全。', '2026-03-01 10:20:00', '2026-04-10 09:20:00'),
  (6, '康复拉伸室', 'A栋3层北侧', 12, '10:00:00', '20:00:00', 'CLOSED', '设备维护中，暂不开放预约。', '2026-03-01 10:25:00', '2026-04-15 17:00:00');

INSERT INTO equipment (
  id, gym_room_id, name, category, brand, quantity, status, purchase_date, description, created_at, updated_at
) VALUES
  (1, 1, '壶铃套组', '力量训练', 'Rogue', 10, 'AVAILABLE', '2025-12-01', '4kg 到 24kg 套组。', '2026-03-02 09:00:00', '2026-03-02 09:00:00'),
  (2, 1, '战绳', '体能训练', 'JOINFIT', 4, 'AVAILABLE', '2025-12-05', '适合燃脂和爆发力训练。', '2026-03-02 09:05:00', '2026-03-02 09:05:00'),
  (3, 2, '智能动感单车', '有氧器械', 'Yesoul', 30, 'AVAILABLE', '2025-11-20', '支持阻力调节和课程联动。', '2026-03-02 09:10:00', '2026-03-02 09:10:00'),
  (4, 3, '可调节哑铃', '力量训练', 'Bowflex', 6, 'AVAILABLE', '2025-10-12', '私教训练常用器械。', '2026-03-02 09:15:00', '2026-03-02 09:15:00'),
  (5, 4, '瑜伽垫', '瑜伽用品', 'Lululemon', 24, 'AVAILABLE', '2025-09-08', '防滑加厚垫。', '2026-03-02 09:20:00', '2026-03-02 09:20:00'),
  (6, 4, '普拉提圈', '普拉提用品', 'Balanced Body', 18, 'AVAILABLE', '2025-09-15', '核心控制训练使用。', '2026-03-02 09:25:00', '2026-03-02 09:25:00'),
  (7, 5, '深蹲架', '力量器械', 'Life Fitness', 4, 'AVAILABLE', '2025-08-01', '含安全保护杆。', '2026-03-02 09:30:00', '2026-03-02 09:30:00'),
  (8, 5, '卧推架', '力量器械', 'Hammer Strength', 5, 'AVAILABLE', '2025-08-01', '可调节角度卧推架。', '2026-03-02 09:35:00', '2026-03-02 09:35:00'),
  (9, 5, '杠铃片', '力量器械', 'Eleiko', 80, 'AVAILABLE', '2025-08-05', '2.5kg 到 25kg。', '2026-03-02 09:40:00', '2026-03-02 09:40:00'),
  (10, 6, '泡沫轴', '康复用品', 'TriggerPoint', 12, 'MAINTENANCE', '2025-07-12', '部分需要更换。', '2026-03-02 09:45:00', '2026-04-15 17:00:00'),
  (11, NULL, '备用心率带', '智能设备', 'Polar', 10, 'AVAILABLE', '2026-01-10', '跨房间备用设备。', '2026-03-02 09:50:00', '2026-03-02 09:50:00'),
  (12, 2, '音响系统', '场地设备', 'JBL', 1, 'AVAILABLE', '2025-11-25', '单车室课程音响。', '2026-03-02 09:55:00', '2026-03-02 09:55:00');

INSERT INTO gym_booking (
  id, booking_no, member_id, gym_room_id, booking_date, start_time, end_time, duration_minutes,
  head_count, status, remark, created_at, updated_at
) VALUES
  (1, 'bk202604170001', 1, 1, '2026-04-17', '2026-04-17 09:00:00', '2026-04-17 10:00:00', 60, 2, 'CONFIRMED', '核心训练', '2026-04-16 18:00:00', '2026-04-16 18:00:00'),
  (2, 'bk202604170002', 2, 4, '2026-04-17', '2026-04-17 10:00:00', '2026-04-17 11:30:00', 90, 1, 'CONFIRMED', '瑜伽拉伸', '2026-04-16 18:10:00', '2026-04-16 18:10:00'),
  (3, 'bk202604170003', 3, 5, '2026-04-17', '2026-04-17 19:00:00', '2026-04-17 20:30:00', 90, 2, 'CONFIRMED', '力量训练', '2026-04-16 18:20:00', '2026-04-16 18:20:00'),
  (4, 'bk202604180001', 4, 2, '2026-04-18', '2026-04-18 08:00:00', '2026-04-18 09:00:00', 60, 1, 'CONFIRMED', '单车课程前热身', '2026-04-16 18:30:00', '2026-04-16 18:30:00'),
  (5, 'bk202604180002', 7, 3, '2026-04-18', '2026-04-18 14:00:00', '2026-04-18 15:00:00', 60, 1, 'CONFIRMED', '私教训练', '2026-04-16 18:40:00', '2026-04-16 18:40:00'),
  (6, 'bk202604180003', 8, 1, '2026-04-18', '2026-04-18 16:00:00', '2026-04-18 17:00:00', 60, 3, 'CONFIRMED', '小组体能', '2026-04-16 18:50:00', '2026-04-16 18:50:00'),
  (7, 'bk202604160001', 1, 5, '2026-04-16', '2026-04-16 18:00:00', '2026-04-16 19:00:00', 60, 1, 'CANCELED', '临时取消', '2026-04-15 12:00:00', '2026-04-16 12:30:00'),
  (8, 'bk202604150001', 5, 3, '2026-04-15', '2026-04-15 20:00:00', '2026-04-15 21:00:00', 60, 1, 'CANCELED', '会员停用后取消', '2026-04-14 10:00:00', '2026-04-15 09:00:00'),
  (9, 'bk202604190001', 2, 1, '2026-04-19', '2026-04-19 09:30:00', '2026-04-19 10:30:00', 60, 2, 'CONFIRMED', '周末训练', '2026-04-17 08:00:00', '2026-04-17 08:00:00'),
  (10, 'bk202604190002', 3, 4, '2026-04-19', '2026-04-19 15:00:00', '2026-04-19 16:30:00', 90, 1, 'CONFIRMED', '拉伸恢复', '2026-04-17 08:15:00', '2026-04-17 08:15:00');

INSERT INTO course (
  id, name, coach_id, gym_room_id, course_type, start_time, end_time, capacity, price,
  description, status, created_at, updated_at
) VALUES
  (1, '私教拉伸课', 2, 3, '私教', '2026-04-09 15:00:00', '2026-04-09 16:00:00', 6, 199.00, '小班私教拉伸，适合恢复和体态改善。', 'OPEN', '2026-03-20 09:00:00', '2026-04-09 16:30:00'),
  (2, '燃脂单车营', 6, 2, '团课', '2026-04-18 09:30:00', '2026-04-18 10:30:00', 25, 89.00, '高燃脂动感单车课程。', 'OPEN', '2026-03-20 09:05:00', '2026-03-20 09:05:00'),
  (3, '力量基础课', 1, 5, '团课', '2026-04-18 19:00:00', '2026-04-18 20:30:00', 12, 129.00, '学习深蹲、硬拉和卧推基础动作。', 'OPEN', '2026-03-20 09:10:00', '2026-03-20 09:10:00'),
  (4, '瑜伽舒展课', 2, 4, '团课', '2026-04-19 10:00:00', '2026-04-19 11:00:00', 20, 79.00, '舒缓拉伸和呼吸练习。', 'OPEN', '2026-03-20 09:15:00', '2026-03-20 09:15:00'),
  (5, '搏击燃脂课', 3, 1, '团课', '2026-04-20 18:30:00', '2026-04-20 19:30:00', 16, 99.00, '结合拳击动作和体能循环。', 'OPEN', '2026-03-20 09:20:00', '2026-03-20 09:20:00'),
  (6, '体态纠正私教', 1, 3, '私教', '2026-04-21 14:00:00', '2026-04-21 15:00:00', 4, 239.00, '评估并改善圆肩、骨盆前倾等问题。', 'OPEN', '2026-03-20 09:25:00', '2026-03-20 09:25:00'),
  (7, '马拉松体能课', 3, 1, '专项训练', '2026-04-22 07:30:00', '2026-04-22 08:30:00', 10, 119.00, '跑者专项核心和下肢稳定训练。', 'OPEN', '2026-03-20 09:30:00', '2026-03-20 09:30:00'),
  (8, '康复拉伸体验课', 2, 6, '体验课', '2026-04-16 16:00:00', '2026-04-16 17:00:00', 8, 59.00, '已结束的康复拉伸体验课程。', 'CLOSED', '2026-03-20 09:35:00', '2026-04-16 17:30:00');

INSERT INTO course_enrollment (
  id, enrollment_no, member_id, course_id, status, created_at, updated_at
) VALUES
  (1, 'ce202604090001', 1, 1, 'ENROLLED', '2026-04-01 10:00:00', '2026-04-01 10:00:00'),
  (2, 'ce202604090002', 5, 1, 'ENROLLED', '2026-04-01 10:05:00', '2026-04-01 10:05:00'),
  (3, 'ce202604180001', 1, 2, 'ENROLLED', '2026-04-10 11:00:00', '2026-04-10 11:00:00'),
  (4, 'ce202604180002', 2, 2, 'ENROLLED', '2026-04-10 11:05:00', '2026-04-10 11:05:00'),
  (5, 'ce202604180003', 3, 3, 'ENROLLED', '2026-04-10 11:10:00', '2026-04-10 11:10:00'),
  (6, 'ce202604190001', 4, 4, 'ENROLLED', '2026-04-11 13:00:00', '2026-04-11 13:00:00'),
  (7, 'ce202604200001', 7, 5, 'ENROLLED', '2026-04-12 14:00:00', '2026-04-12 14:00:00'),
  (8, 'ce202604210001', 8, 6, 'ENROLLED', '2026-04-13 09:00:00', '2026-04-13 09:00:00'),
  (9, 'ce202604220001', 8, 7, 'ENROLLED', '2026-04-13 09:10:00', '2026-04-13 09:10:00'),
  (10, 'ce202604160001', 2, 8, 'CANCELED', '2026-04-08 10:00:00', '2026-04-10 12:00:00'),
  (11, 'ce202604200002', 3, 5, 'ENROLLED', '2026-04-13 15:00:00', '2026-04-13 15:00:00'),
  (12, 'ce202604210002', 4, 6, 'ENROLLED', '2026-04-14 10:30:00', '2026-04-14 10:30:00');

INSERT INTO commodity (
  id, name, category, price, stock, cover_image, description, status, created_at, updated_at
) VALUES
  (1, '拉力绳', '训练装备', 129.90, 5, '/images/shop/resistance-band.png', '多阻力组合拉力绳，适合家庭训练。', 'ON_SALE', '2026-03-10 09:00:00', '2026-04-16 10:00:00'),
  (2, '蛋白礼盒', '营养补剂', 299.00, 18, '/images/shop/protein-box.png', '乳清蛋白组合装，含巧克力和香草口味。', 'ON_SALE', '2026-03-10 09:05:00', '2026-04-16 10:00:00'),
  (3, '瑜伽垫', '瑜伽用品', 159.00, 22, '/images/shop/yoga-mat.png', '防滑加厚瑜伽垫。', 'ON_SALE', '2026-03-10 09:10:00', '2026-04-16 10:00:00'),
  (4, '泡沫轴', '康复放松', 89.00, 4, '/images/shop/foam-roller.png', '肌筋膜放松泡沫轴。', 'ON_SALE', '2026-03-10 09:15:00', '2026-04-16 10:00:00'),
  (5, '弹力带套装', '训练装备', 69.00, 4, '/images/shop/mini-band.png', '臀腿激活弹力带套装。', 'ON_SALE', '2026-03-10 09:20:00', '2026-04-16 10:00:00'),
  (6, '速干毛巾', '运动配件', 39.90, 45, '/images/shop/towel.png', '轻薄速干训练毛巾。', 'ON_SALE', '2026-03-10 09:25:00', '2026-04-16 10:00:00'),
  (7, '运动水杯', '运动配件', 59.90, 32, '/images/shop/bottle.png', '大容量防漏运动水杯。', 'ON_SALE', '2026-03-10 09:30:00', '2026-04-16 10:00:00'),
  (8, '训练手套', '运动配件', 79.90, 12, '/images/shop/gloves.png', '防滑耐磨力量训练手套。', 'ON_SALE', '2026-03-10 09:35:00', '2026-04-16 10:00:00'),
  (9, '跳绳', '有氧装备', 49.90, 3, '/images/shop/jump-rope.png', '可调节钢丝跳绳。', 'ON_SALE', '2026-03-10 09:40:00', '2026-04-16 10:00:00'),
  (10, '护腕', '运动护具', 45.00, 2, '/images/shop/wrist-wrap.png', '力量训练护腕。', 'ON_SALE', '2026-03-10 09:45:00', '2026-04-16 10:00:00'),
  (11, '旧款运动包', '运动配件', 199.00, 0, '/images/shop/gym-bag.png', '旧款运动包，暂时下架。', 'OFF_SALE', '2026-03-10 09:50:00', '2026-04-16 10:00:00'),
  (12, '筋膜球', '康复放松', 35.00, 6, '/images/shop/massage-ball.png', '足底和肩颈放松筋膜球。', 'ON_SALE', '2026-03-10 09:55:00', '2026-04-16 10:00:00');

INSERT INTO cart_item (
  id, member_id, commodity_id, quantity, selected, created_at, updated_at
) VALUES
  (1, 1, 1, 1, 1, '2026-04-16 20:00:00', '2026-04-16 20:00:00'),
  (2, 1, 6, 2, 1, '2026-04-16 20:05:00', '2026-04-16 20:05:00'),
  (3, 2, 3, 1, 1, '2026-04-16 20:10:00', '2026-04-16 20:10:00'),
  (4, 2, 4, 1, 0, '2026-04-16 20:15:00', '2026-04-16 20:15:00'),
  (5, 3, 8, 1, 1, '2026-04-16 20:20:00', '2026-04-16 20:20:00'),
  (6, 4, 7, 1, 1, '2026-04-16 20:25:00', '2026-04-16 20:25:00'),
  (7, 4, 12, 2, 1, '2026-04-16 20:30:00', '2026-04-16 20:30:00'),
  (8, 7, 2, 1, 1, '2026-04-16 20:35:00', '2026-04-16 20:35:00'),
  (9, 8, 9, 1, 1, '2026-04-16 20:40:00', '2026-04-16 20:40:00'),
  (10, 8, 10, 1, 0, '2026-04-16 20:45:00', '2026-04-16 20:45:00');

INSERT INTO commodity_order (
  id, order_no, member_id, total_amount, pay_amount, status, payment_status, payment_time,
  receiver_name, receiver_phone, receiver_address, created_at, updated_at
) VALUES
  (1, 'od20260416184110af9db7de', 1, 338.00, 0.00, 'CANCELED', 'CANCELED', NULL, '朱生', '13800000001', '广东省广州市天河区体育中心1号', '2026-04-16 18:41:10', '2026-04-16 19:00:00'),
  (2, 'od202604161358417e54e929', 1, 129.90, 0.00, 'CANCELED', 'CANCELED', NULL, '张强', '13800000001', '广东省广州市天河区珠江新城1号', '2026-04-16 13:58:41', '2026-04-16 14:10:00'),
  (3, 'od202604151030001a2b3c4d', 2, 198.90, 198.90, 'PAID', 'PAID', '2026-04-15 10:35:00', '李敏', '13800000002', '广东省深圳市南山区科技园2号', '2026-04-15 10:30:00', '2026-04-15 10:35:00'),
  (4, 'od20260415153000d4c3b2a1', 3, 119.80, 119.80, 'PAID', 'PAID', '2026-04-15 15:35:00', '王伟', '13800000003', '广东省广州市越秀区中山路3号', '2026-04-15 15:30:00', '2026-04-15 15:35:00'),
  (5, 'od2026041609000066aa2211', 4, 129.80, 129.80, 'PAID', 'PAID', '2026-04-16 09:10:00', '王雨', '13800000004', '广东省佛山市禅城区同济路4号', '2026-04-16 09:00:00', '2026-04-16 09:10:00'),
  (6, 'od2026041611000055bb3322', 7, 334.00, 334.00, 'PAID', 'PAID', '2026-04-16 11:05:00', '赵杰', '13800000007', '广东省东莞市南城街道5号', '2026-04-16 11:00:00', '2026-04-16 11:05:00'),
  (7, 'od2026041614300044cc7788', 8, 94.90, 94.90, 'PAID', 'PAID', '2026-04-16 14:36:00', '周安', '13800000008', '广东省珠海市香洲区情侣路6号', '2026-04-16 14:30:00', '2026-04-16 14:36:00'),
  (8, 'od2026041708300033dd9900', 2, 128.90, 0.00, 'CREATED', 'UNPAID', NULL, '李敏', '13800000002', '广东省深圳市南山区科技园2号', '2026-04-17 23:30:00', '2026-04-17 23:30:00'),
  (9, 'od2026041708450022ee8800', 3, 59.90, 0.00, 'CREATED', 'UNPAID', NULL, '王伟', '13800000003', '广东省广州市越秀区中山路3号', '2026-04-17 23:35:00', '2026-04-17 23:35:00'),
  (10, 'od2026041709000011ff7700', 1, 209.80, 0.00, 'CREATED', 'UNPAID', NULL, '张强', '13800000001', '广东省广州市天河区珠江新城1号', '2026-04-17 23:40:00', '2026-04-17 23:40:00');

INSERT INTO commodity_order_item (
  id, order_id, commodity_id, commodity_name_snapshot, unit_price, quantity, subtotal_amount, created_at
) VALUES
  (1, 1, 2, '蛋白礼盒', 299.00, 1, 299.00, '2026-04-16 18:41:10'),
  (2, 1, 6, '速干毛巾', 39.00, 1, 39.00, '2026-04-16 18:41:10'),
  (3, 2, 1, '拉力绳', 129.90, 1, 129.90, '2026-04-16 13:58:41'),
  (4, 3, 3, '瑜伽垫', 159.00, 1, 159.00, '2026-04-15 10:30:00'),
  (5, 4, 8, '训练手套', 79.90, 1, 79.90, '2026-04-15 15:30:00'),
  (6, 5, 7, '运动水杯', 59.90, 1, 59.90, '2026-04-16 09:00:00'),
  (7, 5, 12, '筋膜球', 35.00, 2, 70.00, '2026-04-16 09:00:00'),
  (8, 6, 2, '蛋白礼盒', 299.00, 1, 299.00, '2026-04-16 11:00:00'),
  (9, 7, 9, '跳绳', 49.90, 1, 49.90, '2026-04-16 14:30:00'),
  (10, 7, 10, '护腕', 45.00, 1, 45.00, '2026-04-16 14:30:00'),
  (11, 8, 4, '泡沫轴', 89.00, 1, 89.00, '2026-04-17 23:30:00'),
  (12, 9, 7, '运动水杯', 59.90, 1, 59.90, '2026-04-17 23:35:00'),
  (13, 10, 1, '拉力绳', 129.90, 1, 129.90, '2026-04-17 23:40:00'),
  (14, 10, 8, '训练手套', 79.90, 1, 79.90, '2026-04-17 23:40:00'),
  (15, 3, 6, '速干毛巾', 39.90, 1, 39.90, '2026-04-15 10:30:00'),
  (16, 4, 6, '速干毛巾', 39.90, 1, 39.90, '2026-04-15 15:30:00'),
  (17, 6, 12, '筋膜球', 35.00, 1, 35.00, '2026-04-16 11:00:00'),
  (18, 8, 6, '速干毛巾', 39.90, 1, 39.90, '2026-04-17 23:30:00');

INSERT INTO ai_session (
  id, member_id, session_key, source, status, created_at, updated_at
) VALUES
  (1, 1, 'session-member001-20260416', 'LANGCHAIN', 'ACTIVE', '2026-04-16 19:00:00', '2026-04-16 19:10:00'),
  (2, 2, 'session-member002-20260416', 'LANGCHAIN', 'ACTIVE', '2026-04-16 20:00:00', '2026-04-16 20:08:00'),
  (3, 8, 'session-member008-20260417', 'LANGCHAIN', 'ACTIVE', '2026-04-17 08:00:00', '2026-04-17 08:12:00'),
  (4, NULL, 'session-guest-demo-20260417', 'LANGCHAIN', 'CLOSED', '2026-04-17 09:00:00', '2026-04-17 09:05:00');

INSERT INTO ai_message (
  id, session_id, role, content, token_usage, created_at
) VALUES
  (1, 1, 'user', '帮我查一下明天有哪些课程可以报名', 18, '2026-04-16 19:00:10'),
  (2, 1, 'assistant', '明天有燃脂单车营和力量基础课，可以根据训练目标选择。', 42, '2026-04-16 19:00:20'),
  (3, 1, 'user', '帮我报名燃脂单车营', 14, '2026-04-16 19:01:00'),
  (4, 1, 'assistant', '我已经准备好帮你报名燃脂单车营，请确认后执行。', 36, '2026-04-16 19:01:08'),
  (5, 2, 'user', '查询我的预约', 10, '2026-04-16 20:00:10'),
  (6, 2, 'assistant', '你当前有 2 条预约，最近一条是 2026-04-17 的瑜伽普拉提室。', 40, '2026-04-16 20:00:20'),
  (7, 2, 'user', '取消编号 bk202604170002 的预约', 18, '2026-04-16 20:03:00'),
  (8, 2, 'assistant', '我已经准备好帮你取消这条预约，请确认后执行。', 34, '2026-04-16 20:03:08'),
  (9, 3, 'user', '推荐适合马拉松备赛的课程', 16, '2026-04-17 08:00:10'),
  (10, 3, 'assistant', '可以考虑马拉松体能课，重点训练核心稳定和下肢力量。', 38, '2026-04-17 08:00:18'),
  (11, 4, 'user', '健身房几点开门', 12, '2026-04-17 09:00:05'),
  (12, 4, 'assistant', '不同健身室开放时间不同，力量器械区最早 06:30 开放。', 35, '2026-04-17 09:00:12');

SET FOREIGN_KEY_CHECKS = 1;
