// 在浏览器Console中执行此脚本，快速验证管理中心功能

console.log('=== Portal管理中心功能验证 ===\n');

// 1. 检查localStorage中的用户信息
const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
console.log('1. 用户信息:');
console.log('   - ID:', userInfo.id);
console.log('   - 姓名:', userInfo.name);
console.log('   - 角色:', userInfo.role);
console.log('   - 是否管理员:', userInfo.is_admin);

if (!userInfo.is_admin) {
    console.error('\n❌ 问题: 用户不是管理员，管理中心不会显示！');
    console.log('\n解决方案:');
    console.log('1. 使用管理员账号登录（admin / admin123）');
    console.log('2. 或者修改localStorage:');
    console.log('   localStorage.setItem("userInfo", JSON.stringify({...JSON.parse(localStorage.getItem("userInfo")), is_admin: true}))');
    console.log('3. 刷新页面');
} else {
    console.log('\n✅ 用户是管理员，管理中心应该显示');
}

// 2. 检查token
const token = localStorage.getItem('token');
if (token) {
    console.log('\n2. Token: ✅ 已登录');
} else {
    console.log('\n2. Token: ❌ 未登录');
    console.log('   请先登录！');
}

// 3. 检查管理中心DOM
setTimeout(() => {
    const adminSection = document.querySelector('.admin-section');
    if (adminSection) {
        console.log('\n3. 管理中心section: ✅ 已找到');
        console.log('   管理中心已正确显示！');
    } else {
        console.log('\n3. 管理中心section: ❌ 未找到');
        if (userInfo.is_admin) {
            console.log('   错误: 用户是管理员但管理中心未显示');
            console.log('   请刷新页面（Ctrl+F5）');
        }
    }
}, 1000);

console.log('\n=== 验证完成 ===');