let dashboardData = {
    nodes: [],
    cases: [],
    tasks: [],
    performanceData: []
};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    loadDashboardData();
    setupEventListeners();
    initializeCharts();
});

// 设置事件监听器
function setupEventListeners() {
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

// 加载仪表板数据
async function loadDashboardData() {
    try {
        // 并行加载所有数据
        const [nodesResponse, casesResponse, tasksResponse] = await Promise.all([
            apiRequest('/api/nodes/'),
            apiRequest('/api/cases/'),
            apiRequest('/api/tasks/')
        ]);
        
        if (nodesResponse.ok) {
            dashboardData.nodes = await nodesResponse.json();
        }
        
        if (casesResponse.ok) {
            dashboardData.cases = await casesResponse.json();
        }
        
        if (tasksResponse.ok) {
            dashboardData.tasks = await tasksResponse.json();
        }
        
        updateDashboardDisplay();
        updateRecentActivity();
        
    } catch (error) {
        console.error('Load dashboard data error:', error);
        showMessage('加载数据失败', 'error');
    }
}

// 更新仪表板显示
function updateDashboardDisplay() {
    // 更新节点统计
    const totalNodes = dashboardData.nodes.length;
    const onlineNodes = dashboardData.nodes.filter(node => node.status === 'online').length;
    
    document.getElementById('totalNodes').textContent = totalNodes;
    document.getElementById('onlineNodes').textContent = onlineNodes;
    
    // 更新用例统计
    const totalCases = dashboardData.cases.length;
    const publicCases = dashboardData.cases.filter(testCase => testCase.is_public).length;
    
    document.getElementById('totalCases').textContent = totalCases;
    document.getElementById('publicCases').textContent = publicCases;
    
    // 更新任务统计
    const totalTasks = dashboardData.tasks.length;
    const runningTasks = dashboardData.tasks.filter(task => task.status === 'running').length;
    const completedTasks = dashboardData.tasks.filter(task => task.status === 'completed').length;
    const failedTasks = dashboardData.tasks.filter(task => task.status === 'failed').length;
    
    document.getElementById('totalTasks').textContent = totalTasks;
    document.getElementById('runningTasks').textContent = runningTasks;
    
    // 更新性能数据记录（模拟数据）
    document.getElementById('performanceRecords').textContent = Math.floor(Math.random() * 1000) + 500;
    
    // 添加动画效果
    anime({
        targets: '.stat-card .text-3xl',
        scale: [0, 1],
        opacity: [0, 1],
        duration: 800,
        easing: 'easeOutQuart',
        delay: anime.stagger(200)
    });
}

// 更新最近活动
function updateRecentActivity() {
    updateRecentTasks();
    updateNodeStatusList();
}

// 更新最近任务
function updateRecentTasks() {
    const container = document.getElementById('recentTasks');
    const recentTasks = dashboardData.tasks
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .slice(0, 5);
    
    if (recentTasks.length === 0) {
        container.innerHTML = `
            <div class="px-6 py-8 text-center text-gray-500">
                <i class="fas fa-tasks text-4xl mb-2"></i>
                <p>暂无任务数据</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = recentTasks.map(task => `
        <div class="recent-item">
            <div class="flex items-center justify-between">
                <div class="flex items-center">
                    <span class="status-dot status-${task.status}"></span>
                    <div>
                        <div class="font-medium text-gray-900">${task.task_name}</div>
                        <div class="text-sm text-gray-500">
                            ${task.test_case_name || 'Unknown'} • ${getStatusDisplay(task.status)}
                        </div>
                    </div>
                </div>
                <div class="text-right">
                    <div class="text-sm text-gray-900">${task.duration || 0}s</div>
                    <div class="text-xs text-gray-500">${formatDate(task.created_at)}</div>
                </div>
            </div>
        </div>
    `).join('');
}

// 更新节点状态列表
function updateNodeStatusList() {
    const container = document.getElementById('nodeStatusList');
    const nodes = dashboardData.nodes.slice(0, 5);
    
    if (nodes.length === 0) {
        container.innerHTML = `
            <div class="px-6 py-8 text-center text-gray-500">
                <i class="fas fa-server text-4xl mb-2"></i>
                <p>暂无节点数据</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = nodes.map(node => `
        <div class="recent-item">
            <div class="flex items-center justify-between">
                <div class="flex items-center">
                    <span class="status-dot status-${node.status}"></span>
                    <div>
                        <div class="font-medium text-gray-900">${node.node_name}</div>
                        <div class="text-sm text-gray-500">
                            ${node.host}:${node.port} • ${node.partition_count || 0} 个分区
                        </div>
                    </div>
                </div>
                <div class="text-right">
                    <div class="text-sm text-gray-900">${getStatusDisplay(node.status)}</div>
                    <div class="text-xs text-gray-500">${node.os_type || 'Unknown OS'}</div>
                </div>
            </div>
        </div>
    `).join('');
}

// 初始化图表
function initializeCharts() {
    initPerformanceTrendChart();
    initNodeStatusChart();
}

// 初始化性能趋势图表
function initPerformanceTrendChart() {
    const chartDom = document.getElementById('performanceTrendChart');
    const chart = echarts.init(chartDom);
    
    // 生成模拟数据
    const hours = [];
    const iopsData = [];
    const bandwidthData = [];
    const latencyData = [];
    
    const now = new Date();
    for (let i = 23; i >= 0; i--) {
        const time = new Date(now.getTime() - i * 60 * 60 * 1000);
        hours.push(time.getHours() + ':00');
        iopsData.push(Math.floor(Math.random() * 50000) + 10000);
        bandwidthData.push(Math.floor(Math.random() * 2000) + 500);
        latencyData.push(Math.floor(Math.random() * 50) + 10);
    }
    
    const option = {
        title: {
            text: '24小时性能趋势',
            left: 'center',
            textStyle: {
                fontSize: 14,
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
            type: 'category',
            data: hours,
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
                data: iopsData,
                smooth: true,
                itemStyle: {
                    color: '#3b82f6'
                },
                areaStyle: {
                    opacity: 0.1
                }
            },
            {
                name: '带宽(MB/s)',
                type: 'line',
                data: bandwidthData,
                smooth: true,
                itemStyle: {
                    color: '#10b981'
                },
                areaStyle: {
                    opacity: 0.1
                }
            },
            {
                name: '延迟(ms)',
                type: 'line',
                yAxisIndex: 1,
                data: latencyData,
                smooth: true,
                itemStyle: {
                    color: '#f59e0b'
                },
                areaStyle: {
                    opacity: 0.1
                }
            }
        ]
    };
    
    chart.setOption(option);
    
    // 响应式处理
    window.addEventListener('resize', () => {
        chart.resize();
    });
}

// 初始化节点状态图表
function initNodeStatusChart() {
    const chartDom = document.getElementById('nodeStatusChart');
    const chart = echarts.init(chartDom);
    
    // 统计节点状态
    const statusCount = {
        online: 0,
        offline: 0,
        testing: 0
    };
    
    dashboardData.nodes.forEach(node => {
        if (statusCount.hasOwnProperty(node.status)) {
            statusCount[node.status]++;
        } else {
            statusCount.offline++;
        }
    });
    
    const option = {
        title: {
            text: '节点状态分布',
            left: 'center',
            textStyle: {
                fontSize: 14,
                fontWeight: 'normal'
            }
        },
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'horizontal',
            bottom: 10,
            data: ['在线', '离线', '测试中']
        },
        series: [
            {
                name: '节点状态',
                type: 'pie',
                radius: ['40%', '70%'],
                center: ['50%', '45%'],
                avoidLabelOverlap: false,
                itemStyle: {
                    borderRadius: 4,
                    borderColor: '#fff',
                    borderWidth: 2
                },
                label: {
                    show: false,
                    position: 'center'
                },
                emphasis: {
                    label: {
                        show: true,
                        fontSize: 16,
                        fontWeight: 'bold'
                    }
                },
                labelLine: {
                    show: false
                },
                data: [
                    {
                        value: statusCount.online,
                        name: '在线',
                        itemStyle: { color: '#10b981' }
                    },
                    {
                        value: statusCount.offline,
                        name: '离线',
                        itemStyle: { color: '#ef4444' }
                    },
                    {
                        value: statusCount.testing,
                        name: '测试中',
                        itemStyle: { color: '#f59e0b' }
                    }
                ]
            }
        ]
    };
    
    chart.setOption(option);
    
    // 响应式处理
    window.addEventListener('resize', () => {
        chart.resize();
    });
}

// 工具函数
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN');
}

function getStatusDisplay(status) {
    const statusMap = {
        'online': '在线',
        'offline': '离线',
        'testing': '测试中',
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
    window.location.href = 'login.html';
}

// 定期刷新数据
setInterval(() => {
    loadDashboardData();
}, 30000); // 每30秒刷新一次