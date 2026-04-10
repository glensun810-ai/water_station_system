/**
 * 企业服务管理平台 - 配置文件
 * 
 * 用于管理所有文案、服务类型、单位等配置项
 * 实现从"水站管理"到"综合服务管理"的平滑扩展
 */

const APP_CONFIG = {
  // ==================== 应用基础配置 ====================
  appName: '企业服务管理平台',
  appShortName: '服务平台',
  appVersion: '2.0.0',
  
  // ==================== 核心概念文案配置 ====================
  concepts: {
    // 产品/服务
    product: {
      singular: '服务',
      plural: '服务',
      management: '服务管理',
      category: '服务分类',
      add: '添加服务',
      edit: '编辑服务',
      delete: '删除服务',
      stock: '资源量',
      unit: '服务单位'
    },
    
    // 领水记录/服务记录
    pickup: {
      singular: '服务记录',
      plural: '服务记录',
      register: '服务登记',
      list: '服务记录列表',
      person: '服务使用人',
      time: '服务时间'
    },
    
    // 库存/资源
    inventory: {
      label: '资源量',
      alert: '资源预警',
      warning: '资源紧张',
      empty: '资源耗尽',
      replenish: '补充资源'
    },
    
    // 交易/结算
    transaction: {
      singular: '服务订单',
      plural: '服务订单',
      settle: '服务结算',
      settlement: '结算管理'
    },
    
    // 办公室
    office: {
      label: '办公室',
      management: '办公室管理'
    },
    
    // 用户
    user: {
      label: '用户',
      management: '用户管理'
    }
  },
  
  // ==================== 服务类型配置 ====================
  serviceTypes: [
    { 
      value: 'water', 
      label: '饮用水', 
      icon: '💧',
      color: 'blue',
      category: 'physical',
      units: ['桶', '瓶', '件', '提'],
      bookingRequired: false,
      defaultUnit: '桶',
      description: '桶装水、瓶装水等饮用水服务'
    },
    { 
      value: 'meeting_room', 
      label: '会议室', 
      icon: '🏛️',
      color: 'purple',
      category: 'space',
      units: ['小时', '半天', '天'],
      bookingRequired: true,
      defaultUnit: '小时',
      description: '各类会议室、洽谈室预订',
      config: {
        timeSlots: ['09:00-12:00', '14:00-18:00', '19:00-21:00'],
        minDuration: 1,
        maxDuration: 8,
        advanceDays: 7
      }
    },
    { 
      value: 'reception_room',
      label: '接待室', 
      icon: '🛋️',
      color: 'indigo',
      category: 'space',
      units: ['小时', '半天', '天'],
      bookingRequired: true,
      defaultUnit: '小时',
      description: '商务接待室预订'
    },
    { 
      value: 'auditorium',
      label: '会场', 
      icon: '🎤',
      color: 'red',
      category: 'space',
      units: ['半天', '天'],
      bookingRequired: true,
      defaultUnit: '天',
      description: '大型会场、报告厅预订'
    },
    { 
      value: 'vip_dining',
      label: 'VIP 餐厅', 
      icon: '🍽️',
      color: 'orange',
      category: 'space',
      units: ['次', '人均', '包间'],
      bookingRequired: true,
      defaultUnit: '包间',
      description: 'VIP 包间、商务餐饮服务'
    },
    { 
      value: 'large_screen',
      label: '前台大屏', 
      icon: '📺',
      color: 'pink',
      category: 'space',
      units: ['小时', '天'],
      bookingRequired: true,
      defaultUnit: '小时',
      description: '前台 LED 大屏展示服务'
    },
    { 
      value: 'exhibition_booth',
      label: '接待区展位', 
      icon: '🎪',
      color: 'yellow',
      category: 'space',
      units: ['天', '周', '展位'],
      bookingRequired: true,
      defaultUnit: '天',
      description: '接待区展示展位'
    },
    { 
      value: 'cleaning',
      label: '保洁服务', 
      icon: '🧹',
      color: 'green',
      category: 'human',
      units: ['次', '小时', '平方米'],
      bookingRequired: false,
      defaultUnit: '次',
      description: '环境保洁、清洁服务'
    },
    { 
      value: 'tea_break',
      label: '茶歇服务', 
      icon: '☕',
      color: 'amber',
      category: 'supporting',
      units: ['套', '人次'],
      bookingRequired: true,
      defaultUnit: '套',
      description: '会议茶歇、咖啡服务'
    },
    { 
      value: 'shuttle',
      label: '接送服务', 
      icon: '🚗',
      color: 'cyan',
      category: 'human',
      units: ['次', '公里'],
      bookingRequired: true,
      defaultUnit: '次',
      description: '商务接送、用车服务'
    }
  ],
  
  // ==================== 服务分类 ====================
  serviceCategories: [
    { value: 'physical', label: '实物类', icon: '📦', color: 'blue' },
    { value: 'space', label: '空间类', icon: '🏢', color: 'purple' },
    { value: 'human', label: '人力类', icon: '👥', color: 'green' },
    { value: 'supporting', label: '配套类', icon: '🎁', color: 'amber' }
  ],
  
  // ==================== 单位配置 ====================
  defaultUnits: [
    // 实物类单位
    { value: '桶', label: '桶', category: 'physical', group: 'water' },
    { value: '瓶', label: '瓶', category: 'physical', group: 'water' },
    { value: '件', label: '件', category: 'physical', group: 'water' },
    { value: '提', label: '提', category: 'physical', group: 'water' },
    { value: '箱', label: '箱', category: 'physical', group: 'water' },
    { value: '套', label: '套', category: 'physical', group: 'package' },
    
    // 时间类单位
    { value: '小时', label: '小时', category: 'time', group: 'duration' },
    { value: '半天', label: '半天', category: 'time', group: 'duration' },
    { value: '天', label: '天', category: 'time', group: 'duration' },
    { value: '周', label: '周', category: 'time', group: 'duration' },
    { value: '月', label: '月', category: 'time', group: 'duration' },
    
    // 空间类单位
    { value: '间', label: '间', category: 'space', group: 'room' },
    { value: '平方米', label: '平方米', category: 'space', group: 'area' },
    { value: '展位', label: '展位', category: 'space', group: 'booth' },
    
    // 人力类单位
    { value: '次', label: '次', category: 'count', group: 'service' },
    { value: '人次', label: '人次', category: 'human', group: 'people' },
    { value: '人', label: '人', category: 'human', group: 'people' },
    { value: '人均', label: '人均', category: 'human', group: 'people' },
    
    // 项目类单位
    { value: '项', label: '项', category: 'project', group: 'project' },
    { value: '个', label: '个', category: 'count', group: 'general' },
    { value: '公里', label: '公里', category: 'distance', group: 'distance' },
    
    // 餐饮类单位
    { value: '包间', label: '包间', category: 'dining', group: 'room' }
  ],
  
  // ==================== 状态配置 ====================
  statusConfig: {
    // 订单/记录状态
    order: {
      pending: { label: '待结算', color: 'amber' },
      applied: { label: '已申请', color: 'blue' },
      settled: { label: '已结算', color: 'green' },
      cancelled: { label: '已取消', color: 'red' }
    },
    
    // 服务状态
    service: {
      available: { label: '可用', color: 'green' },
      booked: { label: '已预订', color: 'blue' },
      occupied: { label: '使用中', color: 'orange' },
      unavailable: { label: '不可用', color: 'red' }
    },
    
    // 资源状态
    resource: {
      normal: { label: '充足', color: 'green' },
      warning: { label: '紧张', color: 'amber' },
      low: { label: '不足', color: 'orange' },
      empty: { label: '耗尽', color: 'red' }
    }
  },
  
  // ==================== 时间配置 ====================
  timeConfig: {
    timeSlots: [
      { start: '09:00', end: '12:00', label: '上午' },
      { start: '14:00', end: '18:00', label: '下午' },
      { start: '19:00', end: '21:00', label: '晚上' }
    ],
    
    bookingRules: {
      minDuration: 1,  // 最少预约 1 小时
      maxDuration: 8,  // 最多预约 8 小时
      advanceDays: 7,  // 可提前 7 天
      cancelHours: 2   // 可提前 2 小时取消
    }
  },
  
  // ==================== 促销配置 ====================
  promoConfig: {
    // 买 N 赠 M 配置
    buyGift: {
      enabled: true,
      default: { threshold: 10, gift: 1 }
    },
    
    // 套餐优惠
    combo: {
      enabled: true,
      default: { discount: 0.8 }  // 8 折
    }
  },
  
  // ==================== 通知配置 ====================
  notificationConfig: {
    enabled: true,
    types: {
      booking_confirm: { label: '预约确认', icon: '✅' },
      booking_reminder: { label: '预约提醒', icon: '⏰' },
      settlement_reminder: { label: '结算提醒', icon: '💰' },
      resource_alert: { label: '资源预警', icon: '⚠️' }
    }
  }
};

// 导出配置（兼容不同模块系统）
if (typeof module !== 'undefined' && module.exports) {
  module.exports = APP_CONFIG;
}

// 全局注册（浏览器环境）
if (typeof window !== 'undefined') {
  window.APP_CONFIG = APP_CONFIG;
}

console.log('✅ APP_CONFIG loaded:', APP_CONFIG.appName);
