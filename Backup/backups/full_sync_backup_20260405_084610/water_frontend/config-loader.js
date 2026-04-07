/**
 * 配置加载工具
 * 用于从后端 API 加载配置并与本地配置合并
 */

const ConfigLoader = {
  // 配置缓存
  _config: null,
  _apiConfig: null,
  
  /**
   * 初始化配置
   * @param {boolean} useApi - 是否从 API 加载配置
   * @returns {Promise<Object>} 配置对象
   */
  async init(useApi = true) {
    // 优先使用本地配置
    if (typeof window.APP_CONFIG !== 'undefined') {
      this._config = window.APP_CONFIG;
    } else if (typeof APP_CONFIG !== 'undefined') {
      this._config = APP_CONFIG;
    } else {
      console.warn('⚠️ 本地配置未找到，使用默认配置');
      this._config = this._getDefaultConfig();
    }
    
    // 可选：从 API 加载配置并合并
    if (useApi) {
      try {
        this._apiConfig = await this._loadFromApi();
        this._config = this._mergeConfig(this._config, this._apiConfig);
        console.log('✅ 配置已从 API 更新');
      } catch (error) {
        console.warn('⚠️ API 配置加载失败，使用本地配置:', error.message);
      }
    }
    
    return this._config;
  },
  
  /**
   * 获取当前配置
   * @returns {Object} 配置对象
   */
  getConfig() {
    if (!this._config) {
      console.warn('⚠️ 配置未初始化，请先调用 init()');
      return this._getDefaultConfig();
    }
    return this._config;
  },
  
  /**
   * 获取服务类型配置
   * @param {string} type - 服务类型
   * @returns {Object|null} 服务类型配置
   */
  getServiceType(type) {
    const config = this.getConfig();
    return config.serviceTypes?.find(s => s.value === type) || null;
  },
  
  /**
   * 获取所有服务类型
   * @returns {Array} 服务类型列表
   */
  getAllServiceTypes() {
    const config = this.getConfig();
    return config.serviceTypes || [];
  },
  
  /**
   * 获取概念文案
   * @param {string} concept - 概念名称
   * @param {string} key - 文案键
   * @returns {string} 文案
   */
  getText(concept, key) {
    const config = this.getConfig();
    return config.concepts?.[concept]?.[key] || key;
  },
  
  /**
   * 获取单位列表
   * @param {string} category - 单位分类
   * @returns {Array} 单位列表
   */
  getUnits(category = null) {
    const config = this.getConfig();
    let units = config.defaultUnits || [];
    
    if (category) {
      units = units.filter(u => u.category === category);
    }
    
    return units;
  },
  
  /**
   * 获取状态配置
   * @param {string} type - 状态类型
   * @param {string} status - 状态值
   * @returns {Object} 状态配置
   */
  getStatus(type, status) {
    const config = this.getConfig();
    return config.statusConfig?.[type]?.[status] || { label: status, color: 'gray' };
  },
  
  /**
   * 从 API 加载配置
   * @returns {Promise<Object>} API 配置
   */
  async _loadFromApi() {
    const API_BASE = localStorage.getItem('API_BASE') || 
      (window.location.hostname === 'localhost' ? 'http://localhost:8000/api' : 'https://jhw-ai.com/api');
    
    const response = await fetch(`${API_BASE}/services/config`);
    
    if (!response.ok) {
      throw new Error(`API 请求失败: ${response.status}`);
    }
    
    const data = await response.json();
    
    // 转换 API 格式为本地格式
    return {
      serviceTypes: data.serviceTypes?.map(st => ({
        value: st.value,
        label: st.label,
        icon: st.icon,
        color: st.color,
        category: st.category,
        units: st.units,
        bookingRequired: st.bookingRequired,
        defaultUnit: st.defaultUnit,
        description: st.description,
        config: st.config
      })),
      defaultUnits: data.units
    };
  },
  
  /**
   * 合并配置
   * @param {Object} local - 本地配置
   * @param {Object} api - API 配置
   * @returns {Object} 合并后的配置
   */
  _mergeConfig(local, api) {
    if (!api) return local;
    
    return {
      ...local,
      // API 配置覆盖本地配置
      serviceTypes: api.serviceTypes || local.serviceTypes,
      defaultUnits: api.defaultUnits || local.defaultUnits
    };
  },
  
  /**
   * 默认配置
   * @returns {Object} 默认配置
   */
  _getDefaultConfig() {
    return {
      appName: '服务管理平台',
      appVersion: '1.0.0',
      serviceTypes: [
        {
          value: 'water',
          label: '饮用水',
          icon: '💧',
          color: 'blue',
          category: 'physical',
          units: ['桶'],
          bookingRequired: false,
          defaultUnit: '桶'
        }
      ],
      defaultUnits: [
        { value: '桶', label: '桶', category: 'physical' }
      ],
      concepts: {
        product: { singular: '服务', plural: '服务' }
      }
    };
  }
};

// 导出（兼容不同模块系统）
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ConfigLoader;
}

// 全局注册
if (typeof window !== 'undefined') {
  window.ConfigLoader = ConfigLoader;
}