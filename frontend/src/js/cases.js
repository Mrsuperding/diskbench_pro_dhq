let cases = [];
let currentEditingCase = null;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    loadCases();
    setupEventListeners();
});

// 设置事件监听器
function setupEventListeners() {
    // 搜索和筛选
    document.getElementById('searchInput').addEventListener('input', filterCases);
    document.getElementById('rwModeFilter').addEventListener('change', filterCases);
    document.getElementById('templateFilter').addEventListener('change', filterCases);
    document.getElementById('refreshBtn').addEventListener('click', loadCases);
    
    // 用户菜单
    document.getElementById('userMenuBtn').addEventListener('click', toggleUserMenu);
    
    // 表单字段变化时更新FIO预览
    const formInputs = document.querySelectorAll('#caseForm input, #caseForm select, #caseForm textarea');
    formInputs.forEach(input => {
        input.addEventListener('input', debounce(updateFioPreview, 500));
        input.addEventListener('change', debounce(updateFioPreview, 500));
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

// 加载用例列表
async function loadCases() {
    try {
        const response = await apiRequest('/api/cases/');
        
        if (response.ok) {
            cases = await response.json();
            renderCases();
        } else {
            showMessage('加载用例失败', 'error');
        }
    } catch (error) {
        console.error('Load cases error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    }
}

// 渲染用例列表
function renderCases() {
    const container = document.getElementById('casesList');
    const emptyState = document.getElementById('emptyState');
    
    if (cases.length === 0) {
        container.innerHTML = '';
        emptyState.classList.remove('hidden');
        return;
    }
    
    emptyState.classList.add('hidden');
    
    const filteredCases = getFilteredCases();
    
    container.innerHTML = filteredCases.map(testCase => `
        <div class="case-card bg-white rounded-lg shadow-sm p-6">
            <div class="flex items-start justify-between mb-4">
                <div class="flex-1">
                    <div class="flex items-center mb-2">
                        <h3 class="text-lg font-semibold text-gray-900 mr-2">${testCase.case_name}</h3>
                        ${testCase.is_template ? '<span class="template-badge">模板</span>' : ''}
                        ${testCase.is_public ? '<span class="public-badge ml-1">公开</span>' : ''}
                    </div>
                    <p class="text-sm text-gray-600 mb-3">${testCase.description || '暂无描述'}</p>
                </div>
                <div class="flex items-center space-x-2">
                    <button onclick="previewCommand(${testCase.id})" class="p-2 text-gray-400 hover:text-blue-600 transition-colors" title="预览命令">
                        <i class="fas fa-terminal"></i>
                    </button>
                    <button onclick="cloneCase(${testCase.id})" class="p-2 text-gray-400 hover:text-green-600 transition-colors" title="克隆">
                        <i class="fas fa-copy"></i>
                    </button>
                    <button onclick="editCase(${testCase.id})" class="p-2 text-gray-400 hover:text-yellow-600 transition-colors" title="编辑">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button onclick="deleteCase(${testCase.id})" class="p-2 text-gray-400 hover:text-red-600 transition-colors" title="删除">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            
            <div class="grid grid-cols-2 gap-4 mb-4">
                <div class="text-sm">
                    <span class="text-gray-500">读写模式:</span>
                    <span class="font-medium">${getRwModeDisplay(testCase.rw_mode)}</span>
                </div>
                <div class="text-sm">
                    <span class="text-gray-500">IO大小:</span>
                    <span class="font-medium">${testCase.io_size}</span>
                </div>
                <div class="text-sm">
                    <span class="text-gray-500">运行时间:</span>
                    <span class="font-medium">${testCase.runtime}秒</span>
                </div>
                <div class="text-sm">
                    <span class="text-gray-500">块大小:</span>
                    <span class="font-medium">${testCase.block_size}</span>
                </div>
            </div>
            
            <div class="flex items-center justify-between pt-4 border-t border-gray-200">
                <div class="text-xs text-gray-400">
                    创建时间: ${formatDate(testCase.created_at)}
                </div>
                <div class="flex items-center space-x-2">
                    <span class="text-xs text-gray-500">队列深度: ${testCase.queue_depth}</span>
                    ${testCase.rw_mode.includes('rw') ? `<span class="text-xs text-gray-500">读/写: ${testCase.rw_ratio}</span>` : ''}
                </div>
            </div>
        </div>
    `).join('');
    
    // 添加动画效果
    anime({
        targets: '.case-card',
        translateY: [20, 0],
        opacity: [0, 1],
        duration: 600,
        easing: 'easeOutQuart',
        delay: anime.stagger(100)
    });
}

// 获取筛选后的用例
function getFilteredCases() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const rwModeFilter = document.getElementById('rwModeFilter').value;
    const templateFilter = document.getElementById('templateFilter').value;
    
    return cases.filter(testCase => {
        const matchesSearch = !searchTerm || 
            testCase.case_name.toLowerCase().includes(searchTerm) ||
            (testCase.description && testCase.description.toLowerCase().includes(searchTerm));
        
        const matchesRwMode = !rwModeFilter || testCase.rw_mode === rwModeFilter;
        
        const matchesTemplate = !templateFilter || 
            (templateFilter === 'template' && testCase.is_template) ||
            (templateFilter === 'custom' && !testCase.is_template);
        
        return matchesSearch && matchesRwMode && matchesTemplate;
    });
}

// 筛选用例
function filterCases() {
    renderCases();
}

// 打开创建用例模态框
function openAddCaseModal() {
    currentEditingCase = null;
    document.getElementById('modalTitle').textContent = '创建用例';
    document.getElementById('caseForm').reset();
    document.getElementById('caseModal').classList.remove('hidden');
    
    // 设置默认值
    document.getElementById('ioEngine').value = 'libaio';
    document.getElementById('blockSize').value = '4k';
    document.getElementById('queueDepth').value = '32';
    document.getElementById('ioSize').value = '1G';
    document.getElementById('runtime').value = '60';
    document.getElementById('rwMode').value = 'read';
    document.getElementById('rwRatio').value = '50/50';
    document.getElementById('compressionRatio').value = '0';
    document.getElementById('numjobs').value = '1';
    document.getElementById('directIO').checked = true;
    document.getElementById('timeBased').checked = true;
    document.getElementById('groupReporting').checked = true;
    
    updateRwRatioVisibility();
    updateFioPreview();
    
    // 动画效果
    anime({
        targets: '.modal-content',
        scale: [0.8, 1],
        opacity: [0, 1],
        duration: 300,
        easing: 'easeOutQuart'
    });
}

// 编辑用例
function editCase(caseId) {
    const testCase = cases.find(c => c.id === caseId);
    if (!testCase) return;
    
    currentEditingCase = testCase;
    document.getElementById('modalTitle').textContent = '编辑用例';
    
    // 填充表单
    document.getElementById('caseName').value = testCase.case_name;
    document.getElementById('description').value = testCase.description || '';
    document.getElementById('ioEngine').value = testCase.io_engine;
    document.getElementById('blockSize').value = testCase.block_size;
    document.getElementById('queueDepth').value = testCase.queue_depth;
    document.getElementById('ioSize').value = testCase.io_size;
    document.getElementById('runtime').value = testCase.runtime;
    document.getElementById('rwMode').value = testCase.rw_mode;
    document.getElementById('rwRatio').value = testCase.rw_ratio;
    document.getElementById('compressionRatio').value = testCase.compression_ratio;
    document.getElementById('numjobs').value = testCase.numjobs;
    document.getElementById('directIO').checked = testCase.direct_io;
    document.getElementById('timeBased').checked = testCase.time_based;
    document.getElementById('verify').value = testCase.verify || '';
    document.getElementById('verifyFatal').checked = testCase.verify_fatal;
    document.getElementById('groupReporting').checked = testCase.group_reporting;
    document.getElementById('isPublic').checked = testCase.is_public;
    document.getElementById('isTemplate').checked = testCase.is_template;
    
    updateRwRatioVisibility();
    updateFioPreview();
    
    document.getElementById('caseModal').classList.remove('hidden');
    
    // 动画效果
    anime({
        targets: '.modal-content',
        scale: [0.8, 1],
        opacity: [0, 1],
        duration: 300,
        easing: 'easeOutQuart'
    });
}

// 更新读写比例字段可见性
function updateRwRatioVisibility() {
    const rwMode = document.getElementById('rwMode').value;
    const rwRatioField = document.getElementById('rwRatioField');
    
    if (rwMode.includes('rw')) {
        rwRatioField.style.display = 'block';
    } else {
        rwRatioField.style.display = 'none';
    }
}

// 更新FIO命令预览
function updateFioPreview() {
    const formData = new FormData(document.getElementById('caseForm'));
    const data = Object.fromEntries(formData.entries());
    
    // 转换为正确的数据类型
    const caseData = {
        case_name: data.case_name || 'test_case',
        io_engine: data.io_engine || 'libaio',
        block_size: data.block_size || '4k',
        queue_depth: parseInt(data.queue_depth) || 32,
        io_size: data.io_size || '1G',
        runtime: parseInt(data.runtime) || 60,
        rw_mode: data.rw_mode || 'read',
        rw_ratio: data.rw_ratio || '50/50',
        compression_ratio: parseFloat(data.compression_ratio) || 0,
        direct_io: data.direct_io === 'on',
        numjobs: parseInt(data.numjobs) || 1,
        time_based: data.time_based === 'on',
        verify: data.verify || '',
        verify_fatal: data.verify_fatal === 'on',
        group_reporting: data.group_reporting === 'on'
    };
    
    const command = generateFioCommand(caseData);
    document.getElementById('fioPreview').textContent = command;
}

// 生成FIO命令
function generateFioCommand(caseData) {
    const cmdParts = ['fio'];
    
    // 基本参数
    cmdParts.push(`--name=${caseData.case_name}`);
    cmdParts.push('--filename=testfile');
    cmdParts.push(`--ioengine=${caseData.io_engine}`);
    cmdParts.push(`--bs=${caseData.block_size}`);
    cmdParts.push(`--iodepth=${caseData.queue_depth}`);
    cmdParts.push(`--size=${caseData.io_size}`);
    cmdParts.push(`--runtime=${caseData.runtime}`);
    cmdParts.push(`--rw=${caseData.rw_mode}`);
    
    // 读写比例
    if (caseData.rw_mode.includes('rw')) {
        cmdParts.push(`--rwmixread=${caseData.rw_ratio.split('/')[0]}`);
    }
    
    // 压缩比
    if (caseData.compression_ratio > 0) {
        cmdParts.push(`--buffer_compress_percentage=${Math.round(caseData.compression_ratio * 100)}`);
    }
    
    // 直接IO
    if (caseData.direct_io) {
        cmdParts.push('--direct=1');
    }
    
    // 作业数
    cmdParts.push(`--numjobs=${caseData.numjobs}`);
    
    // 基于时间的测试
    if (caseData.time_based) {
        cmdParts.push('--time_based');
    }
    
    // 验证
    if (caseData.verify) {
        cmdParts.push(`--verify=${caseData.verify}`);
        if (caseData.verify_fatal) {
            cmdParts.push('--verify_fatal=1');
        }
    }
    
    // 组报告
    if (caseData.group_reporting) {
        cmdParts.push('--group_reporting');
    }
    
    // 输出格式
    cmdParts.push('--output-format=json');
    
    return cmdParts.join(' ');
}

// 预览FIO命令
async function previewCommand(caseId) {
    try {
        const response = await apiRequest(`/api/cases/${caseId}/fio-command`);
        
        if (response.ok) {
            const result = await response.json();
            
            // 创建模态框显示命令
            const modal = document.createElement('div');
            modal.className = 'fixed inset-0 z-50 overflow-y-auto';
            modal.innerHTML = `
                <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
                    <div class="modal fixed inset-0 transition-opacity" onclick="this.parentElement.parentElement.remove()"></div>
                    <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
                        <div class="modal-content">
                            <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                                <div class="flex items-center justify-between mb-4">
                                    <h3 class="text-lg font-medium text-gray-900">FIO命令预览 - ${result.case_name}</h3>
                                    <button onclick="this.closest('.fixed').remove()" class="text-gray-400 hover:text-gray-500">
                                        <i class="fas fa-times text-xl"></i>
                                    </button>
                                </div>
                                <div class="fio-preview mb-4">${result.command}</div>
                                <div class="text-sm text-gray-600">
                                    <p><strong>说明：</strong></p>
                                    <ul class="list-disc list-inside mt-2 space-y-1">
                                        <li>此命令使用默认文件名 'testfile'</li>
                                        <li>输出格式为JSON，便于程序解析</li>
                                        <li>在实际使用时，请根据需要调整文件名路径</li>
                                    </ul>
                                </div>
                            </div>
                            <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                                <button onclick="copyToClipboard('${result.command.replace(/'/g, "\\'")}')" class="btn-primary inline-flex justify-center rounded-md border border-transparent px-4 py-2 text-base font-medium text-white sm:text-sm">
                                    <i class="fas fa-copy mr-2"></i>复制命令
                                </button>
                                <button onclick="this.closest('.fixed').remove()" class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 px-4 py-2 text-base font-medium text-gray-700 hover:bg-gray-50 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm">
                                    关闭
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // 动画效果
            anime({
                targets: modal.querySelector('.modal-content'),
                scale: [0.8, 1],
                opacity: [0, 1],
                duration: 300,
                easing: 'easeOutQuart'
            });
            
        } else {
            const error = await response.json();
            showMessage(error.detail || '获取命令失败', 'error');
        }
        
    } catch (error) {
        console.error('Preview command error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    }
}

// 复制到剪贴板
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showMessage('命令已复制到剪贴板', 'success');
    }).catch(() => {
        showMessage('复制失败，请手动复制', 'error');
    });
}

// 克隆用例
async function cloneCase(caseId) {
    const testCase = cases.find(c => c.id === caseId);
    if (!testCase) return;
    
    const newName = prompt('请输入新的用例名称:', testCase.case_name + '_副本');
    if (!newName || newName.trim() === '') {
        return;
    }
    
    try {
        const response = await apiRequest(`/api/cases/${caseId}/clone`, {
            method: 'POST',
            body: JSON.stringify({ new_name: newName.trim() })
        });
        
        if (response.ok) {
            showMessage('用例克隆成功', 'success');
            loadCases();
        } else {
            const error = await response.json();
            showMessage(error.detail || '克隆失败', 'error');
        }
        
    } catch (error) {
        console.error('Clone case error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    }
}

// 关闭用例模态框
function closeCaseModal() {
    document.getElementById('caseModal').classList.add('hidden');
    currentEditingCase = null;
}

// 保存用例
async function saveCase() {
    const formData = new FormData(document.getElementById('caseForm'));
    const data = Object.fromEntries(formData.entries());
    
    // 验证必填字段
    if (!data.case_name) {
        showMessage('请填写用例名称', 'error');
        return;
    }
    
    // 数据类型转换
    const caseData = {
        ...data,
        queue_depth: parseInt(data.queue_depth),
        runtime: parseInt(data.runtime),
        numjobs: parseInt(data.numjobs),
        compression_ratio: parseFloat(data.compression_ratio),
        direct_io: data.direct_io === 'on',
        time_based: data.time_based === 'on',
        verify_fatal: data.verify_fatal === 'on',
        group_reporting: data.group_reporting === 'on',
        is_public: data.is_public === 'on',
        is_template: data.is_template === 'on'
    };
    
    const saveBtnText = document.getElementById('saveBtnText');
    const saveBtnLoading = document.getElementById('saveBtnLoading');
    
    saveBtnText.classList.add('hidden');
    saveBtnLoading.classList.remove('hidden');
    
    try {
        const url = currentEditingCase ? `/api/cases/${currentEditingCase.id}` : '/api/cases/';
        const method = currentEditingCase ? 'PUT' : 'POST';
        
        const response = await apiRequest(url, {
            method: method,
            body: JSON.stringify(caseData)
        });
        
        if (response.ok) {
            showMessage(currentEditingCase ? '用例更新成功' : '用例创建成功', 'success');
            closeCaseModal();
            loadCases();
        } else {
            const error = await response.json();
            showMessage(error.detail || '操作失败', 'error');
        }
        
    } catch (error) {
        console.error('Save case error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    } finally {
        saveBtnText.classList.remove('hidden');
        saveBtnLoading.classList.add('hidden');
    }
}

// 删除用例
async function deleteCase(caseId) {
    const testCase = cases.find(c => c.id === caseId);
    if (!testCase) return;
    
    if (!confirm(`确定要删除用例 "${testCase.case_name}" 吗？此操作不可撤销。`)) {
        return;
    }
    
    try {
        const response = await apiRequest(`/api/cases/${caseId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showMessage('用例删除成功', 'success');
            loadCases();
        } else {
            const error = await response.json();
            showMessage(error.detail || '删除失败', 'error');
        }
        
    } catch (error) {
        console.error('Delete case error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    }
}

// 获取读写模式显示名称
function getRwModeDisplay(mode) {
    const modeMap = {
        'read': '顺序读',
        'write': '顺序写',
        'randread': '随机读',
        'randwrite': '随机写',
        'rw': '顺序读写',
        'randrw': '随机读写'
    };
    return modeMap[mode] || mode;
}

// 工具函数
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN');
}

function showMessage(message, type = 'info') {
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