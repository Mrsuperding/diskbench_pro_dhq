let nodes = [];
let currentEditingNode = null;
let currentNodeId = null;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    loadNodes();
    setupEventListeners();
});

// 设置事件监听器
function setupEventListeners() {
    // 搜索和筛选
    document.getElementById('searchInput').addEventListener('input', filterNodes);
    document.getElementById('statusFilter').addEventListener('change', filterNodes);
    document.getElementById('refreshBtn').addEventListener('click', loadNodes);
    
    // 用户菜单
    document.getElementById('userMenuBtn').addEventListener('click', toggleUserMenu);
    
    // 表单提交
    document.getElementById('nodeForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveNode();
    });
    
    // 点击外部关闭菜单
    document.addEventListener('click', function(e) {
        const userMenu = document.getElementById('userMenu');
        const userMenuBtn = document.getElementById('userMenuBtn');
        
        if (!userMenu.contains(e.target) && !userMenuBtn.contains(e.target)) {
            userMenu.classList.add('hidden');
        }
    });
}

// 加载节点列表
async function loadNodes() {
    try {
        const response = await apiRequest('/api/nodes/');
        
        if (response.ok) {
            nodes = await response.json();
            renderNodes();
        } else {
            showMessage('加载节点失败', 'error');
        }
    } catch (error) {
        console.error('Load nodes error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    }
}

// 渲染节点列表
function renderNodes() {
    const container = document.getElementById('nodesList');
    const emptyState = document.getElementById('emptyState');
    
    if (nodes.length === 0) {
        container.innerHTML = '';
        emptyState.classList.remove('hidden');
        return;
    }
    
    emptyState.classList.add('hidden');
    
    const filteredNodes = getFilteredNodes();
    
    container.innerHTML = filteredNodes.map(node => `
        <div class="node-card bg-white rounded-lg shadow-sm p-6">
            <div class="flex items-start justify-between mb-4">
                <div class="flex items-center">
                    <span class="status-indicator status-${node.status}"></span>
                    <h3 class="text-lg font-semibold text-gray-900">${node.node_name}</h3>
                </div>
                <div class="flex items-center space-x-2">
                    <button onclick="testNodeConnection(${node.id})" class="p-2 text-gray-400 hover:text-blue-600 transition-colors" title="测试连接">
                        <i class="fas fa-plug"></i>
                    </button>
                    <button onclick="managePartitions(${node.id})" class="p-2 text-gray-400 hover:text-green-600 transition-colors" title="管理分区">
                        <i class="fas fa-hdd"></i>
                    </button>
                    <button onclick="editNode(${node.id})" class="p-2 text-gray-400 hover:text-yellow-600 transition-colors" title="编辑">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button onclick="deleteNode(${node.id})" class="p-2 text-gray-400 hover:text-red-600 transition-colors" title="删除">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            
            <div class="space-y-2 mb-4">
                <div class="flex items-center text-sm text-gray-600">
                    <i class="fas fa-server mr-2 w-4"></i>
                    <span>${node.host}:${node.port}</span>
                </div>
                <div class="flex items-center text-sm text-gray-600">
                    <i class="fas fa-user mr-2 w-4"></i>
                    <span>${node.username}</span>
                </div>
                <div class="flex items-center text-sm text-gray-600">
                    <i class="fas fa-key mr-2 w-4"></i>
                    <span>${node.login_type === 'password' ? '密码登录' : '密钥登录'}</span>
                </div>
                ${node.os_type ? `
                <div class="flex items-center text-sm text-gray-600">
                    <i class="fas fa-desktop mr-2 w-4"></i>
                    <span>${node.os_type}</span>
                </div>
                ` : ''}
            </div>
            
            <div class="flex items-center justify-between pt-4 border-t border-gray-200">
                <div class="flex items-center text-sm text-gray-500">
                    <i class="fas fa-hdd mr-1"></i>
                    <span>${node.partition_count || 0} 个分区</span>
                </div>
                <div class="flex items-center text-sm text-gray-500">
                    ${node.is_public ? '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">公开</span>' : '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">私有</span>'}
                </div>
            </div>
            
            <div class="mt-3 text-xs text-gray-400">
                创建时间: ${formatDate(node.created_at)}
            </div>
        </div>
    `).join('');
    
    // 添加动画效果
    anime({
        targets: '.node-card',
        translateY: [20, 0],
        opacity: [0, 1],
        duration: 600,
        easing: 'easeOutQuart',
        delay: anime.stagger(100)
    });
}

// 获取筛选后的节点
function getFilteredNodes() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;
    
    return nodes.filter(node => {
        const matchesSearch = !searchTerm || 
            node.node_name.toLowerCase().includes(searchTerm) ||
            node.host.toLowerCase().includes(searchTerm);
        
        const matchesStatus = !statusFilter || node.status === statusFilter;
        
        return matchesSearch && matchesStatus;
    });
}

// 筛选节点
function filterNodes() {
    renderNodes();
}

// 打开添加节点模态框
function openAddNodeModal() {
    currentEditingNode = null;
    document.getElementById('modalTitle').textContent = '添加节点';
    document.getElementById('nodeForm').reset();
    document.getElementById('nodeModal').classList.remove('hidden');
    
    // 动画效果
    anime({
        targets: '.modal-content',
        scale: [0.8, 1],
        opacity: [0, 1],
        duration: 300,
        easing: 'easeOutQuart'
    });
}

// 编辑节点
function editNode(nodeId) {
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return;
    
    currentEditingNode = node;
    document.getElementById('modalTitle').textContent = '编辑节点';
    
    // 填充表单
    document.getElementById('nodeName').value = node.node_name;
    document.getElementById('host').value = node.host;
    document.getElementById('port').value = node.port;
    document.getElementById('username').value = node.username;
    document.getElementById('osType').value = node.os_type || '';
    document.getElementById('loginType').value = node.login_type;
    document.getElementById('isPublic').checked = node.is_public;
    
    // 根据登录类型显示相应字段
    toggleLoginFields();
    
    document.getElementById('nodeModal').classList.remove('hidden');
    
    // 动画效果
    anime({
        targets: '.modal-content',
        scale: [0.8, 1],
        opacity: [0, 1],
        duration: 300,
        easing: 'easeOutQuart'
    });
}

// 切换登录字段显示
function toggleLoginFields() {
    const loginType = document.getElementById('loginType').value;
    const passwordField = document.getElementById('passwordField');
    const privateKeyField = document.getElementById('privateKeyField');
    
    if (loginType === 'password') {
        passwordField.classList.remove('hidden');
        privateKeyField.classList.add('hidden');
        document.getElementById('password').required = true;
        document.getElementById('privateKey').required = false;
    } else {
        passwordField.classList.add('hidden');
        privateKeyField.classList.remove('hidden');
        document.getElementById('password').required = false;
        document.getElementById('privateKey').required = true;
    }
}

// 关闭节点模态框
function closeNodeModal() {
    document.getElementById('nodeModal').classList.add('hidden');
    currentEditingNode = null;
}

// 测试连接
async function testConnection() {
    const formData = new FormData(document.getElementById('nodeForm'));
    const data = Object.fromEntries(formData.entries());
    
    // 验证必填字段
    if (!data.host || !data.username || !data.port) {
        showMessage('请填写主机地址、用户名和端口', 'error');
        return;
    }
    
    if (data.login_type === 'password' && !data.password) {
        showMessage('密码登录方式需要填写密码', 'error');
        return;
    }
    
    if (data.login_type === 'key' && !data.private_key) {
        showMessage('密钥登录方式需要填写私钥', 'error');
        return;
    }
    
    try {
        const response = await apiRequest('/api/nodes/test-connection', {
            method: 'POST',
            body: JSON.stringify({
                host: data.host,
                port: parseInt(data.port),
                username: data.username,
                password: data.password || undefined,
                private_key: data.private_key || undefined,
                login_type: data.login_type
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showMessage('连接成功！', 'success');
            console.log('System info:', result.system_info);
        } else {
            const error = await response.json();
            showMessage(`连接失败: ${error.detail}`, 'error');
        }
    } catch (error) {
        console.error('Test connection error:', error);
        showMessage('测试连接失败，请检查网络设置', 'error');
    }
}

// 保存节点
async function saveNode() {
    const formData = new FormData(document.getElementById('nodeForm'));
    const data = Object.fromEntries(formData.entries());
    
    // 验证必填字段
    if (!data.node_name || !data.host || !data.username || !data.port) {
        showMessage('请填写所有必填字段', 'error');
        return;
    }
    
    if (data.login_type === 'password' && !data.password && !currentEditingNode) {
        showMessage('密码登录方式需要填写密码', 'error');
        return;
    }
    
    if (data.login_type === 'key' && !data.private_key && !currentEditingNode) {
        showMessage('密钥登录方式需要填写私钥', 'error');
        return;
    }
    
    const saveBtnText = document.getElementById('saveBtnText');
    const saveBtnLoading = document.getElementById('saveBtnLoading');
    
    saveBtnText.classList.add('hidden');
    saveBtnLoading.classList.remove('hidden');
    
    try {
        const url = currentEditingNode ? `/api/nodes/${currentEditingNode.id}` : '/api/nodes/';
        const method = currentEditingNode ? 'PUT' : 'POST';
        
        const requestData = {
            ...data,
            port: parseInt(data.port),
            is_public: data.is_public === 'on'
        };
        
        // 如果是编辑模式且没有修改密码/私钥，则不包含这些字段
        if (currentEditingNode) {
            if (!requestData.password) {
                delete requestData.password;
            }
            if (!requestData.private_key) {
                delete requestData.private_key;
            }
        }
        
        const response = await apiRequest(url, {
            method: method,
            body: JSON.stringify(requestData)
        });
        
        if (response.ok) {
            showMessage(currentEditingNode ? '节点更新成功' : '节点创建成功', 'success');
            closeNodeModal();
            loadNodes();
        } else {
            const error = await response.json();
            showMessage(error.detail || '操作失败', 'error');
        }
        
    } catch (error) {
        console.error('Save node error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    } finally {
        saveBtnText.classList.remove('hidden');
        saveBtnLoading.classList.add('hidden');
    }
}

// 删除节点
async function deleteNode(nodeId) {
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return;
    
    if (!confirm(`确定要删除节点 "${node.node_name}" 吗？此操作不可撤销。`)) {
        return;
    }
    
    try {
        const response = await apiRequest(`/api/nodes/${nodeId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showMessage('节点删除成功', 'success');
            loadNodes();
        } else {
            const error = await response.json();
            showMessage(error.detail || '删除失败', 'error');
        }
        
    } catch (error) {
        console.error('Delete node error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    }
}

// 测试节点连接
async function testNodeConnection(nodeId) {
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return;
    
    try {
        const response = await apiRequest(`/api/nodes/${nodeId}/test-connection`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const result = await response.json();
            showMessage('连接成功！', 'success');
            
            // 更新节点状态
            node.status = 'online';
            renderNodes();
        } else {
            const error = await response.json();
            showMessage(`连接失败: ${error.detail}`, 'error');
            
            // 更新节点状态
            node.status = 'offline';
            renderNodes();
        }
        
    } catch (error) {
        console.error('Test node connection error:', error);
        showMessage('网络错误，请稍后重试', 'error');
        
        // 更新节点状态
        node.status = 'offline';
        renderNodes();
    }
}

// 管理分区
async function managePartitions(nodeId) {
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return;
    
    currentNodeId = nodeId;
    document.getElementById('partitionNodeName').textContent = node.node_name;
    document.getElementById('partitionsModal').classList.remove('hidden');
    
    await loadPartitions(nodeId);
}

// 加载分区列表
async function loadPartitions(nodeId) {
    try {
        const response = await apiRequest(`/api/nodes/${nodeId}/partitions`);
        
        if (response.ok) {
            const partitions = await response.json();
            renderPartitions(partitions);
        } else {
            showMessage('加载分区失败', 'error');
        }
    } catch (error) {
        console.error('Load partitions error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    }
}

// 渲染分区列表
function renderPartitions(partitions) {
    const container = document.getElementById('partitionsList');
    
    if (partitions.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8">
                <i class="fas fa-hdd text-4xl text-gray-300 mb-4"></i>
                <p class="text-gray-500">暂无分区信息</p>
                <p class="text-sm text-gray-400 mt-2">点击"同步分区信息"获取最新数据</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = `
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">分区名称</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">挂载点</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">文件系统</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">总大小</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">可用空间</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">使用率</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                ${partitions.map(partition => `
                    <tr>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${partition.partition_name}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${partition.mount_point}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${partition.filesystem || '-'}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${formatSize(partition.total_size * 1024 * 1024)}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${formatSize(partition.available_size * 1024 * 1024)}</td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <div class="flex items-center">
                                <div class="w-16 bg-gray-200 rounded-full h-2 mr-2">
                                    <div class="bg-blue-600 h-2 rounded-full" style="width: ${partition.used_percentage}%"></div>
                                </div>
                                <span class="text-sm text-gray-500">${partition.used_percentage}%</span>
                            </div>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

// 同步分区信息
async function syncPartitions() {
    if (!currentNodeId) return;
    
    try {
        const response = await apiRequest(`/api/nodes/${currentNodeId}/sync-partitions`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const result = await response.json();
            showMessage(`同步成功，共发现 ${result.partitions_count} 个分区`, 'success');
            await loadPartitions(currentNodeId);
        } else {
            const error = await response.json();
            showMessage(`同步失败: ${error.detail}`, 'error');
        }
        
    } catch (error) {
        console.error('Sync partitions error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    }
}

// 关闭分区管理模态框
function closePartitionsModal() {
    document.getElementById('partitionsModal').classList.add('hidden');
    currentNodeId = null;
}

// 工具函数
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN');
}

function formatSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showMessage(message, type = 'info') {
    // 简单的消息显示实现
    const messageDiv = document.createElement('div');
    messageDiv.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
        type === 'success' ? 'bg-green-500 text-white' :
        type === 'error' ? 'bg-red-500 text-white' :
        'bg-blue-500 text-white'
    }`;
    messageDiv.textContent = message;
    
    document.body.appendChild(messageDiv);
    
    // 动画显示
    anime({
        targets: messageDiv,
        translateX: [300, 0],
        opacity: [0, 1],
        duration: 300,
        easing: 'easeOutQuart'
    });
    
    // 3秒后自动消失
    setTimeout(() => {
        anime({
            targets: messageDiv,
            translateX: [0, 300],
            opacity: [1, 0],
            duration: 300,
            easing: 'easeInQuart',
            complete: () => {
                document.body.removeChild(messageDiv);
            }
        });
    }, 3000);
}

// 切换用户菜单
function toggleUserMenu() {
    const menu = document.getElementById('userMenu');
    menu.classList.toggle('hidden');
}

// 退出登录
function logout() {
    localStorage.clear();
    window.location.href = 'login.html';
}