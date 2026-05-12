let tasks = [];
let currentTaskId = null;
let socket = null;
let performanceChart = null;
let performanceData = {};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    loadTasks();
    loadTaskStatistics();
    setupEventListeners();
    initializeWebSocket();
});

// 设置事件监听器
function setupEventListeners() {
    // 搜索和筛选
    document.getElementById('searchInput').addEventListener('input', filterTasks);
    document.getElementById('statusFilter').addEventListener('change', filterTasks);
    document.getElementById('refreshBtn').addEventListener('click', () => {
        loadTasks();
        loadTaskStatistics();
    });
    
    // 用户菜单
    document.getElementById('userMenuBtn').addEventListener('click', toggleUserMenu);
    
    // 点击外部关闭菜单
    document.addEventListener('click', function(e) {
        const userMenu = document.getElementById('userMenu');
        const userMenuBtn = document.getElementById('userMenuBtn');
        
        if (!userMenu.contains(e.target) && !userMenuBtn.contains(e.target)) {
            userMenu.classList.add('hidden');
        }
    });
}

// 加载任务列表
async function loadTasks() {
    try {
        const response = await apiRequest('/api/tasks/');
        
        if (response.ok) {
            tasks = await response.json();
            renderTasks();
        } else {
            showMessage('加载任务失败', 'error');
        }
    } catch (error) {
        console.error('Load tasks error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    }
}

// 加载任务统计
async function loadTaskStatistics() {
    try {
        const response = await apiRequest('/api/tasks/statistics/');
        
        if (response.ok) {
            const stats = await response.json();
            updateStatisticsDisplay(stats);
        }
    } catch (error) {
        console.error('Load task statistics error:', error);
    }
}

// 更新统计显示
function updateStatisticsDisplay(stats) {
    document.getElementById('totalTasks').textContent = stats.total_tasks;
    document.getElementById('runningTasks').textContent = stats.running_tasks;
    document.getElementById('completedTasks').textContent = stats.completed_tasks;
    document.getElementById('failedTasks').textContent = stats.failed_tasks;
    
    // 添加动画效果
    anime({
        targets: '.performance-value',
        scale: [1.2, 1],
        duration: 300,
        easing: 'easeOutQuart'
    });
}

// 渲染任务列表
function renderTasks() {
    const container = document.getElementById('tasksList');
    const emptyState = document.getElementById('emptyState');
    
    if (tasks.length === 0) {
        container.innerHTML = '';
        emptyState.classList.remove('hidden');
        return;
    }
    
    emptyState.classList.add('hidden');
    
    const filteredTasks = getFilteredTasks();
    
    container.innerHTML = filteredTasks.map(task => `
        <div class="task-card bg-white rounded-lg shadow-sm p-6">
            <div class="flex items-start justify-between mb-4">
                <div class="flex-1">
                    <div class="flex items-center mb-2">
                        <span class="status-indicator status-${task.status}"></span>
                        <h3 class="text-lg font-semibold text-gray-900">${task.task_name}</h3>
                        ${task.is_public ? '<span class="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">公开</span>' : ''}
                    </div>
                    <p class="text-sm text-gray-600 mb-2">${task.description || '暂无描述'}</p>
                    <p class="text-xs text-gray-500">测试用例: ${task.test_case_name || 'Unknown'}</p>
                </div>
                <div class="flex items-center space-x-2">
                    <button onclick="viewTaskDetails(${task.id})" class="p-2 text-gray-400 hover:text-blue-600 transition-colors" title="查看详情">
                        <i class="fas fa-eye"></i>
                    </button>
                    ${task.status === 'pending' ? `
                        <button onclick="startTaskFromList(${task.id})" class="p-2 text-gray-400 hover:text-green-600 transition-colors" title="开始任务">
                            <i class="fas fa-play"></i>
                        </button>
                    ` : ''}
                    ${task.status === 'running' ? `
                        <button onclick="stopTaskFromList(${task.id})" class="p-2 text-gray-400 hover:text-red-600 transition-colors" title="停止任务">
                            <i class="fas fa-stop"></i>
                        </button>
                    ` : ''}
                    <button onclick="cloneTaskFromList(${task.id})" class="p-2 text-gray-400 hover:text-green-600 transition-colors" title="克隆任务">
                        <i class="fas fa-copy"></i>
                    </button>
                    <button onclick="deleteTask(${task.id})" class="p-2 text-gray-400 hover:text-red-600 transition-colors" title="删除任务">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div class="text-center">
                    <div class="text-lg font-semibold text-gray-900">${task.node_count || 0}</div>
                    <div class="text-xs text-gray-500">节点数</div>
                </div>
                <div class="text-center">
                    <div class="text-lg font-semibold text-gray-900">${task.duration || 0}s</div>
                    <div class="text-xs text-gray-500">运行时间</div>
                </div>
                <div class="text-center">
                    <div class="text-lg font-semibold text-blue-600">${Math.round(task.avg_iops || 0)}</div>
                    <div class="text-xs text-gray-500">平均IOPS</div>
                </div>
                <div class="text-center">
                    <div class="text-lg font-semibold text-green-600">${Math.round(task.avg_bw || 0)}</div>
                    <div class="text-xs text-gray-500">平均带宽</div>
                </div>
            </div>
            
            <div class="flex items-center justify-between pt-4 border-t border-gray-200">
                <div class="text-xs text-gray-400">
                    创建时间: ${formatDate(task.created_at)}
                </div>
                <div class="flex items-center space-x-2">
                    <span class="text-xs text-gray-500">状态: ${getStatusDisplay(task.status)}</span>
                    ${task.status === 'running' ? '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">运行中</span>' : ''}
                </div>
            </div>
        </div>
    `).join('');
    
    // 添加动画效果
    anime({
        targets: '.task-card',
        translateY: [20, 0],
        opacity: [0, 1],
        duration: 600,
        easing: 'easeOutQuart',
        delay: anime.stagger(100)
    });
}

// 获取筛选后的任务
function getFilteredTasks() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;
    
    return tasks.filter(task => {
        const matchesSearch = !searchTerm || 
            task.task_name.toLowerCase().includes(searchTerm) ||
            (task.description && task.description.toLowerCase().includes(searchTerm));
        
        const matchesStatus = !statusFilter || task.status === statusFilter;
        
        return matchesSearch && matchesStatus;
    });
}

// 筛选任务
function filterTasks() {
    renderTasks();
}

// 打开创建任务模态框
function openCreateTaskModal() {
    document.getElementById('createTaskModal').classList.remove('hidden');
    loadTestCasesForSelection();
    loadNodesForSelection();
    
    // 动画效果
    anime({
        targets: '#createTaskModal .modal-content',
        scale: [0.8, 1],
        opacity: [0, 1],
        duration: 300,
        easing: 'easeOutQuart'
    });
}

// 关闭创建任务模态框
function closeCreateTaskModal() {
    document.getElementById('createTaskModal').classList.add('hidden');
    document.getElementById('createTaskForm').reset();
}

// 加载测试用例选择列表
async function loadTestCasesForSelection() {
    try {
        const response = await apiRequest('/api/cases/');
        
        if (response.ok) {
            const cases = await response.json();
            const select = document.getElementById('testCaseSelect');
            
            select.innerHTML = '<option value="">请选择测试用例</option>';
            cases.forEach(testCase => {
                const option = document.createElement('option');
                option.value = testCase.id;
                option.textContent = testCase.case_name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Load test cases error:', error);
    }
}

// 加载节点选择列表
async function loadNodesForSelection() {
    try {
        const response = await apiRequest('/api/nodes/');
        
        if (response.ok) {
            const nodes = await response.json();
            const container = document.getElementById('nodeSelection');
            
            container.innerHTML = '';
            nodes.forEach(node => {
                const nodeDiv = document.createElement('div');
                nodeDiv.className = 'flex items-center p-2 hover:bg-gray-50 rounded';
                nodeDiv.innerHTML = `
                    <input type="checkbox" id="node_${node.id}" name="nodes" value="${node.id}" class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mr-3">
                    <label for="node_${node.id}" class="flex-1 text-sm text-gray-700 cursor-pointer">
                        <div class="font-medium">${node.node_name}</div>
                        <div class="text-xs text-gray-500">${node.host}:${node.port} - ${getStatusDisplay(node.status)}</div>
                    </label>
                `;
                container.appendChild(nodeDiv);
            });
        }
    } catch (error) {
        console.error('Load nodes error:', error);
    }
}

// 创建任务
async function createTask() {
    const formData = new FormData(document.getElementById('createTaskForm'));
    const data = Object.fromEntries(formData.entries());
    
    // 验证必填字段
    if (!data.task_name || !data.test_case_id) {
        showMessage('请填写任务名称和选择测试用例', 'error');
        return;
    }
    
    // 获取选中的节点
    const selectedNodes = Array.from(document.querySelectorAll('input[name="nodes"]:checked')).map(cb => parseInt(cb.value));
    
    if (selectedNodes.length === 0) {
        showMessage('请至少选择一个节点', 'error');
        return;
    }
    
    const createBtnText = document.getElementById('createTaskBtnText');
    const createBtnLoading = document.getElementById('createBtnLoading');
    
    createBtnText.classList.add('hidden');
    createBtnLoading.classList.remove('hidden');
    
    try {
        // 获取节点的分区信息（简化处理，使用第一个可用分区）
        const partitionMappings = {};
        for (const nodeId of selectedNodes) {
            const response = await apiRequest(`/api/nodes/${nodeId}/partitions`);
            if (response.ok) {
                const partitions = await response.json();
                if (partitions.length > 0) {
                    partitionMappings[nodeId] = partitions[0].id;
                }
            }
        }
        
        if (Object.keys(partitionMappings).length === 0) {
            showMessage('所选节点没有可用的分区', 'error');
            return;
        }
        
        const response = await apiRequest('/api/tasks/', {
            method: 'POST',
            body: JSON.stringify({
                task_name: data.task_name,
                description: data.description,
                test_case_id: parseInt(data.test_case_id),
                node_ids: selectedNodes,
                partition_mappings: partitionMappings,
                is_public: data.is_public === 'on'
            })
        });
        
        if (response.ok) {
            showMessage('任务创建成功', 'success');
            closeCreateTaskModal();
            loadTasks();
            loadTaskStatistics();
        } else {
            const error = await response.json();
            showMessage(error.detail || '创建失败', 'error');
        }
        
    } catch (error) {
        console.error('Create task error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    } finally {
        createBtnText.classList.remove('hidden');
        createBtnLoading.classList.add('hidden');
    }
}

// 查看任务详情
async function viewTaskDetails(taskId) {
    currentTaskId = taskId;
    
    try {
        const response = await apiRequest(`/api/tasks/${taskId}`);
        
        if (response.ok) {
            const task = await response.json();
            showTaskDetailModal(task);
        } else {
            showMessage('获取任务详情失败', 'error');
        }
    } catch (error) {
        console.error('View task details error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    }
}

// 显示任务详情模态框
function showTaskDetailModal(task) {
    // 更新基本信息
    document.getElementById('taskDetailTitle').textContent = `任务详情 - ${task.task_name}`;
    document.getElementById('detailStatus').textContent = getStatusDisplay(task.status);
    document.getElementById('detailDuration').textContent = `${task.duration || 0}s`;
    document.getElementById('detailIOPS').textContent = Math.round(task.avg_iops || 0);
    document.getElementById('detailBandwidth').textContent = `${Math.round(task.avg_bw || 0)} MB/s`;
    
    // 更新节点状态
    renderNodeStatusGrid(task.task_nodes || []);
    
    // 初始化性能图表
    initPerformanceChart();
    
    // 加载日志
    loadTaskLogs(task.id);
    
    // 更新按钮状态
    updateTaskActionButtons(task.status);
    
    // 显示模态框
    document.getElementById('taskDetailModal').classList.remove('hidden');
    
    // 动画效果
    anime({
        targets: '#taskDetailModal .modal-content',
        scale: [0.8, 1],
        opacity: [0, 1],
        duration: 300,
        easing: 'easeOutQuart'
    });
    
    // 加入WebSocket房间
    if (socket) {
        socket.emit('join_task_monitor', { task_id: task.id });
    }
}

// 渲染节点状态网格
function renderNodeStatusGrid(taskNodes) {
    const container = document.getElementById('nodeStatusGrid');
    
    if (taskNodes.length === 0) {
        container.innerHTML = '<div class="col-span-full text-center text-gray-500 py-8">暂无节点数据</div>';
        return;
    }
    
    container.innerHTML = taskNodes.map(taskNode => `
        <div class="node-status-card">
            <div class="flex items-center justify-between mb-2">
                <h5 class="font-medium text-gray-900">${taskNode.node ? taskNode.node.node_name : 'Unknown'}</h5>
                <span class="status-indicator status-${taskNode.status}"></span>
            </div>
            <div class="text-sm text-gray-600 mb-2">
                ${taskNode.partition ? taskNode.partition.partition_name : 'Unknown'} - ${taskNode.partition ? taskNode.partition.mount_point : ''}
            </div>
            <div class="grid grid-cols-2 gap-2 text-xs mb-2">
                <div>IOPS: <span class="font-medium">${Math.round(taskNode.iops || 0)}</span></div>
                <div>带宽: <span class="font-medium">${Math.round(taskNode.bandwidth || 0)} MB/s</span></div>
                <div>延迟: <span class="font-medium">${Math.round(taskNode.latency || 0)} ms</span></div>
                <div>IO操作: <span class="font-medium">${taskNode.io_ops || 0}</span></div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${getNodeProgress(taskNode)}"></div>
            </div>
            <div class="text-xs text-gray-500 mt-1">
                ${getStatusDisplay(taskNode.status)} - ${taskNode.duration || 0}s
            </div>
        </div>
    `).join('');
}

// 获取节点进度
function getNodeProgress(taskNode) {
    switch (taskNode.status) {
        case 'pending': return '0%';
        case 'running': return '50%';
        case 'completed': return '100%';
        case 'failed': return '100%';
        case 'cancelled': return '100%';
        default: return '0%';
    }
}

// 初始化性能图表
function initPerformanceChart() {
    const chartDom = document.getElementById('performanceChart');
    
    if (performanceChart) {
        performanceChart.dispose();
    }
    
    performanceChart = echarts.init(chartDom);
    
    const option = {
        title: {
            text: '实时性能监控',
            left: 'center',
            textStyle: {
                fontSize: 16,
                fontWeight: 'normal'
            }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            }
        },
        legend: {
            data: ['IOPS', '带宽(MB/s)', '延迟(ms)'],
            bottom: 10
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '15%',
            containLabel: true
        },
        xAxis: {
            type: 'time',
            boundaryGap: false
        },
        yAxis: [
            {
                type: 'value',
                name: 'IOPS / 带宽',
                position: 'left'
            },
            {
                type: 'value',
                name: '延迟(ms)',
                position: 'right'
            }
        ],
        series: [
            {
                name: 'IOPS',
                type: 'line',
                data: [],
                smooth: true,
                itemStyle: {
                    color: '#3b82f6'
                }
            },
            {
                name: '带宽(MB/s)',
                type: 'line',
                data: [],
                smooth: true,
                itemStyle: {
                    color: '#10b981'
                }
            },
            {
                name: '延迟(ms)',
                type: 'line',
                yAxisIndex: 1,
                data: [],
                smooth: true,
                itemStyle: {
                    color: '#f59e0b'
                }
            }
        ]
    };
    
    performanceChart.setOption(option);
    
    // 初始化性能数据
    performanceData[currentTaskId] = {
        iops: [],
        bandwidth: [],
        latency: [],
        timestamps: []
    };
}

// 更新性能图表
function updatePerformanceChart(data) {
    if (!performanceChart || !performanceData[currentTaskId]) return;
    
    const chartData = performanceData[currentTaskId];
    const timestamp = new Date(data.timestamp || Date.now());
    
    // 限制数据点数量
    const maxPoints = 100;
    if (chartData.timestamps.length >= maxPoints) {
        chartData.timestamps.shift();
        chartData.iops.shift();
        chartData.bandwidth.shift();
        chartData.latency.shift();
    }
    
    chartData.timestamps.push(timestamp);
    chartData.iops.push(data.iops || 0);
    chartData.bandwidth.push(data.bandwidth || 0);
    chartData.latency.push(data.latency || 0);
    
    const option = {
        series: [
            {
                data: chartData.timestamps.map((time, index) => [time, chartData.iops[index]])
            },
            {
                data: chartData.timestamps.map((time, index) => [time, chartData.bandwidth[index]])
            },
            {
                data: chartData.timestamps.map((time, index) => [time, chartData.latency[index]])
            }
        ]
    };
    
    performanceChart.setOption(option);
}

// 加载任务日志
async function loadTaskLogs(taskId) {
    try {
        const response = await apiRequest(`/api/tasks/${taskId}/logs`);
        
        if (response.ok) {
            const logs = await response.json();
            renderTaskLogs(logs);
        }
    } catch (error) {
        console.error('Load task logs error:', error);
    }
}

// 渲染任务日志
function renderTaskLogs(logs) {
    const container = document.getElementById('taskLogs');
    
    if (logs.length === 0) {
        container.innerHTML = `
            <div class="text-center text-gray-400 py-8">
                <i class="fas fa-file-alt text-4xl mb-2"></i>
                <p>暂无日志数据</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = logs.map(log => `
        <div class="log-entry log-${log.log_level}">
            <span class="text-gray-400">[${formatTime(log.created_at)}]</span>
            <span class="text-gray-400">[${log.source || 'system'}]</span>
            ${log.message}
        </div>
    `).join('');
    
    // 滚动到底部
    container.scrollTop = container.scrollHeight;
}

// 更新任务操作按钮
function updateTaskActionButtons(status) {
    const startBtn = document.getElementById('startTaskBtn');
    const stopBtn = document.getElementById('stopTaskBtn');
    const cloneBtn = document.getElementById('cloneTaskBtn');
    
    switch (status) {
        case 'pending':
            startBtn.style.display = 'inline-flex';
            stopBtn.style.display = 'none';
            cloneBtn.style.display = 'inline-flex';
            break;
        case 'running':
            startBtn.style.display = 'none';
            stopBtn.style.display = 'inline-flex';
            cloneBtn.style.display = 'none';
            break;
        case 'completed':
        case 'failed':
        case 'cancelled':
            startBtn.style.display = 'none';
            stopBtn.style.display = 'none';
            cloneBtn.style.display = 'inline-flex';
            break;
        default:
            startBtn.style.display = 'inline-flex';
            stopBtn.style.display = 'none';
            cloneBtn.style.display = 'inline-flex';
    }
}

// 初始化WebSocket连接
function initializeWebSocket() {
    const token = localStorage.getItem('access_token');
    
    socket = io({
        auth: {
            token: token
        }
    });
    
    // WebSocket事件处理
    socket.on('connect', () => {
        console.log('WebSocket connected');
    });
    
    socket.on('disconnect', () => {
        console.log('WebSocket disconnected');
    });
    
    socket.on('task_started', (data) => {
        handleTaskStatusUpdate(data);
    });
    
    socket.on('task_completed', (data) => {
        handleTaskStatusUpdate(data);
    });
    
    socket.on('task_stopped', (data) => {
        handleTaskStatusUpdate(data);
    });
    
    socket.on('performance_update', (data) => {
        if (data.task_id == currentTaskId) {
            updatePerformanceChart(data);
        }
    });
    
    socket.on('log_update', (data) => {
        if (data.task_id == currentTaskId) {
            addLogEntry(data);
        }
    });
    
    socket.on('node_status_update', (data) => {
        if (data.task_id == currentTaskId) {
            updateNodeStatus(data);
        }
    });
}

// 处理任务状态更新
function handleTaskStatusUpdate(data) {
    // 更新任务列表中的状态
    const taskIndex = tasks.findIndex(t => t.id === data.task_id);
    if (taskIndex !== -1) {
        tasks[taskIndex].status = data.status;
        if (data.end_time) {
            tasks[taskIndex].end_time = data.end_time;
        }
        if (data.duration !== undefined) {
            tasks[taskIndex].duration = data.duration;
        }
        if (data.avg_iops !== undefined) {
            tasks[taskIndex].avg_iops = data.avg_iops;
        }
        if (data.avg_bw !== undefined) {
            tasks[taskIndex].avg_bw = data.avg_bw;
        }
        
        renderTasks();
        loadTaskStatistics();
    }
}

// 添加日志条目
function addLogEntry(logData) {
    const container = document.getElementById('taskLogs');
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${logData.level}`;
    logEntry.innerHTML = `
        <span class="text-gray-400">[${formatTime(logData.timestamp)}]</span>
        <span class="text-gray-400">[${logData.source || 'system'}]</span>
        ${logData.message}
    `;
    
    container.appendChild(logEntry);
    container.scrollTop = container.scrollHeight;
}

// 更新节点状态
function updateNodeStatus(nodeData) {
    // 重新加载任务详情以获取最新节点状态
    if (currentTaskId) {
        loadTaskDetails(currentTaskId);
    }
}

// 开始任务
async function startTask() {
    if (!currentTaskId) return;
    
    try {
        const response = await apiRequest(`/api/tasks/${currentTaskId}/start`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showMessage('任务启动成功', 'success');
            // 更新按钮状态
            updateTaskActionButtons('running');
        } else {
            const error = await response.json();
            showMessage(error.detail || '启动失败', 'error');
        }
    } catch (error) {
        console.error('Start task error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    }
}

// 停止任务
async function stopTask() {
    if (!currentTaskId) return;
    
    if (!confirm('确定要停止当前任务吗？')) {
        return;
    }
    
    try {
        const response = await apiRequest(`/api/tasks/${currentTaskId}/stop`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showMessage('任务停止成功', 'success');
            // 更新按钮状态
            updateTaskActionButtons('cancelled');
        } else {
            const error = await response.json();
            showMessage(error.detail || '停止失败', 'error');
        }
    } catch (error) {
        console.error('Stop task error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    }
}

// 克隆任务
async function cloneTask() {
    if (!currentTaskId) return;
    
    const newName = prompt('请输入新的任务名称:', '');
    if (!newName || newName.trim() === '') {
        return;
    }
    
    try {
        const response = await apiRequest(`/api/tasks/${currentTaskId}/clone`, {
            method: 'POST',
            body: JSON.stringify({ new_name: newName.trim() })
        });
        
        if (response.ok) {
            showMessage('任务克隆成功', 'success');
            loadTasks();
            closeTaskDetailModal();
        } else {
            const error = await response.json();
            showMessage(error.detail || '克隆失败', 'error');
        }
    } catch (error) {
        console.error('Clone task error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    }
}

// 从列表开始任务
async function startTaskFromList(taskId) {
    try {
        const response = await apiRequest(`/api/tasks/${taskId}/start`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showMessage('任务启动成功', 'success');
            loadTasks();
            loadTaskStatistics();
        } else {
            const error = await response.json();
            showMessage(error.detail || '启动失败', 'error');
        }
    } catch (error) {
        console.error('Start task from list error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    }
}

// 从列表停止任务
async function stopTaskFromList(taskId) {
    if (!confirm('确定要停止当前任务吗？')) {
        return;
    }
    
    try {
        const response = await apiRequest(`/api/tasks/${taskId}/stop`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showMessage('任务停止成功', 'success');
            loadTasks();
            loadTaskStatistics();
        } else {
            const error = await response.json();
            showMessage(error.detail || '停止失败', 'error');
        }
    } catch (error) {
        console.error('Stop task from list error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    }
}

// 从列表克隆任务
async function cloneTaskFromList(taskId) {
    const newName = prompt('请输入新的任务名称:', '');
    if (!newName || newName.trim() === '') {
        return;
    }
    
    try {
        const response = await apiRequest(`/api/tasks/${taskId}/clone`, {
            method: 'POST',
            body: JSON.stringify({ new_name: newName.trim() })
        });
        
        if (response.ok) {
            showMessage('任务克隆成功', 'success');
            loadTasks();
        } else {
            const error = await response.json();
            showMessage(error.detail || '克隆失败', 'error');
        }
    } catch (error) {
        console.error('Clone task from list error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    }
}

// 删除任务
async function deleteTask(taskId) {
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;
    
    if (!confirm(`确定要删除任务 "${task.task_name}" 吗？此操作不可撤销。`)) {
        return;
    }
    
    try {
        const response = await apiRequest(`/api/tasks/${taskId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showMessage('任务删除成功', 'success');
            loadTasks();
            loadTaskStatistics();
        } else {
            const error = await response.json();
            showMessage(error.detail || '删除失败', 'error');
        }
        
    } catch (error) {
        console.error('Delete task error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    }
}

// 关闭任务详情模态框
function closeTaskDetailModal() {
    document.getElementById('taskDetailModal').classList.add('hidden');
    
    // 离开WebSocket房间
    if (socket && currentTaskId) {
        socket.emit('leave_task_monitor', { task_id: currentTaskId });
    }
    
    currentTaskId = null;
    
    // 清理图表
    if (performanceChart) {
        performanceChart.dispose();
        performanceChart = null;
    }
}

// 工具函数
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN');
}

function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('zh-CN');
}

function getStatusDisplay(status) {
    const statusMap = {
        'pending': '待执行',
        'running': '运行中',
        'completed': '已完成',
        'failed': '失败',
        'cancelled': '已取消'
    };
    return statusMap[status] || status;
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
    if (socket) {
        socket.disconnect();
    }
    window.location.href = 'login.html';
}