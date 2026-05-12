#!/usr/bin/env node

const fs = require('fs')
const path = require('path')

console.log('🔍 IO性能测试平台前端项目检查')
console.log('=' .repeat(50))

// 项目统计
let totalFiles = 0
let totalLines = 0
let vueFiles = 0
let jsFiles = 0
let cssFiles = 0

// 检查文件是否存在
function fileExists(filePath) {
  return fs.existsSync(path.join(__dirname, filePath))
}

// 统计文件信息
function analyzeFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8')
    const lines = content.split('\n').length
    totalLines += lines
    totalFiles++
    
    const ext = path.extname(filePath)
    if (ext === '.vue') vueFiles++
    else if (ext === '.js') jsFiles++
    else if (ext === '.css') cssFiles++
    
    return { lines, size: content.length }
  } catch (error) {
    return null
  }
}

// 递归遍历目录
function walkDir(dir, callback) {
  const files = fs.readdirSync(dir)
  files.forEach(file => {
    const filePath = path.join(dir, file)
    const stat = fs.statSync(filePath)
    
    if (stat.isDirectory() && !file.startsWith('.') && file !== 'node_modules' && file !== 'dist') {
      walkDir(filePath, callback)
    } else if (stat.isFile()) {
      callback(filePath)
    }
  })
}

// 检查必需文件
function checkRequiredFiles() {
  console.log('📋 检查必需文件...')
  
  const requiredFiles = [
    'package.json',
    'vite.config.js',
    'index.html',
    'src/main.js',
    'src/App.vue',
    'src/router/index.js',
    'src/stores/auth.js',
    'src/stores/index.js'
  ]
  
  let missingFiles = []
  requiredFiles.forEach(file => {
    if (!fileExists(file)) {
      missingFiles.push(file)
    }
  })
  
  if (missingFiles.length > 0) {
    console.log('❌ 缺失文件:')
    missingFiles.forEach(file => console.log(`  - ${file}`))
  } else {
    console.log('✅ 所有必需文件都存在')
  }
  
  return missingFiles.length === 0
}

// 检查项目结构
function checkProjectStructure() {
  console.log('\n🏗️  检查项目结构...')
  
  const requiredDirs = [
    'src',
    'src/api',
    'src/assets',
    'src/components',
    'src/composables',
    'src/router',
    'src/stores',
    'src/utils',
    'src/views',
    'src/views/auth',
    'src/views/dashboard',
    'src/views/nodes',
    'src/views/testcases',
    'src/views/tasks',
    'src/views/monitoring'
  ]
  
  let missingDirs = []
  requiredDirs.forEach(dir => {
    if (!fileExists(dir)) {
      missingDirs.push(dir)
    }
  })
  
  if (missingDirs.length > 0) {
    console.log('❌ 缺失目录:')
    missingDirs.forEach(dir => console.log(`  - ${dir}`))
  } else {
    console.log('✅ 项目结构完整')
  }
  
  return missingDirs.length === 0
}

// 检查依赖
function checkDependencies() {
  console.log('\n📦 检查依赖配置...')
  
  try {
    const packageJson = require('./package.json')
    const requiredDeps = [
      'vue',
      'vue-router',
      'pinia',
      'axios',
      'element-plus',
      'echarts'
    ]
    
    let missingDeps = []
    requiredDeps.forEach(dep => {
      if (!packageJson.dependencies[dep]) {
        missingDeps.push(dep)
      }
    })
    
    if (missingDeps.length > 0) {
      console.log('❌ 缺失依赖:')
      missingDeps.forEach(dep => console.log(`  - ${dep}`))
    } else {
      console.log('✅ 核心依赖已配置')
    }
    
    return missingDeps.length === 0
  } catch (error) {
    console.log('❌ 无法读取package.json')
    return false
  }
}

// 统计代码量
function countCode() {
  console.log('\n📊 统计代码信息...')
  
  walkDir('src', (filePath) => {
    if (filePath.endsWith('.vue') || filePath.endsWith('.js') || filePath.endsWith('.ts')) {
      analyzeFile(filePath)
    }
  })
  
  console.log(`📁 总文件数: ${totalFiles}`)
  console.log(`📝 总代码行数: ${totalLines.toLocaleString()}`)
  console.log(`🎯 Vue组件: ${vueFiles}个`)
  console.log(`⚡ JS文件: ${jsFiles}个`)
  console.log(`🎨 CSS文件: ${cssFiles}个`)
}

// 检查配置文件
function checkConfigs() {
  console.log('\n⚙️  检查配置文件...')
  
  const configs = [
    'vite.config.js',
    'tailwind.config.js',
    '.gitignore'
  ]
  
  configs.forEach(config => {
    if (fileExists(config)) {
      console.log(`✅ ${config}`)
    } else {
      console.log(`❌ ${config} (可选)`)
    }
  })
}

// 检查关键组件
function checkKeyComponents() {
  console.log('\n🧩 检查关键组件...')
  
  const components = [
    'src/views/auth/Login.vue',
    'src/views/auth/Register.vue',
    'src/views/dashboard/Dashboard.vue',
    'src/views/nodes/NodeList.vue',
    'src/views/testcases/TestcaseList.vue',
    'src/views/tasks/TaskList.vue',
    'src/views/monitoring/RealTimeMonitor.vue',
    'src/components/charts/PerformanceChart.vue',
    'src/components/layout/AppLayout.vue'
  ]
  
  components.forEach(component => {
    if (fileExists(component)) {
      console.log(`✅ ${path.basename(component)}`)
    } else {
      console.log(`❌ ${path.basename(component)}`)
    }
  })
}

// 生成项目报告
function generateReport() {
  console.log('\n📋 项目检查报告')
  console.log('=' .repeat(50))
  
  const checks = [
    checkRequiredFiles(),
    checkProjectStructure(),
    checkDependencies()
  ]
  
  countCode()
  checkConfigs()
  checkKeyComponents()
  
  const passedChecks = checks.filter(Boolean).length
  const totalChecks = checks.length
  
  console.log(`\n📈 检查通过率: ${passedChecks}/${totalChecks} (${Math.round(passedChecks/totalChecks*100)}%)`)
  
  if (passedChecks === totalChecks) {
    console.log('\n🎉 项目检查通过！项目已准备就绪。')
    console.log('💡 下一步: 运行 npm install 安装依赖')
  } else {
    console.log('\n⚠️  项目检查未通过，请修复上述问题。')
    console.log('💡 建议: 检查缺失的文件和目录')
  }
}

// 执行检查
generateReport()