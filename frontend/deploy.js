#!/usr/bin/env node

const { execSync } = require('child_process')
const fs = require('fs')
const path = require('path')

console.log('🚀 IO性能测试平台前端部署脚本')
console.log('=' .repeat(50))

// 检查Node.js版本
function checkNodeVersion() {
  const nodeVersion = process.version
  const majorVersion = parseInt(nodeVersion.substring(1).split('.')[0])
  
  if (majorVersion < 16) {
    console.error('❌ 错误: Node.js版本必须 >= 16.0.0')
    console.log(`当前版本: ${nodeVersion}`)
    process.exit(1)
  }
  
  console.log(`✅ Node.js版本检查通过: ${nodeVersion}`)
}

// 检查必需文件
function checkRequiredFiles() {
  const requiredFiles = [
    'package.json',
    'vite.config.js',
    'src/main.js',
    'src/App.vue',
    'index.html'
  ]
  
  const missingFiles = requiredFiles.filter(file => {
    return !fs.existsSync(path.join(__dirname, file))
  })
  
  if (missingFiles.length > 0) {
    console.error('❌ 错误: 缺少必需文件')
    console.log('缺失文件:', missingFiles.join(', '))
    process.exit(1)
  }
  
  console.log('✅ 必需文件检查通过')
}

// 安装依赖
function installDependencies() {
  console.log('📦 安装项目依赖...')
  try {
    execSync('npm install', { stdio: 'inherit' })
    console.log('✅ 依赖安装完成')
  } catch (error) {
    console.error('❌ 依赖安装失败:', error.message)
    process.exit(1)
  }
}

// 构建项目
function buildProject() {
  console.log('🔨 构建项目...')
  try {
    execSync('npm run build', { stdio: 'inherit' })
    console.log('✅ 项目构建完成')
  } catch (error) {
    console.error('❌ 项目构建失败:', error.message)
    process.exit(1)
  }
}

// 检查构建结果
function checkBuildResult() {
  const distPath = path.join(__dirname, 'dist')
  
  if (!fs.existsSync(distPath)) {
    console.error('❌ 错误: 构建目录不存在')
    process.exit(1)
  }
  
  const requiredFiles = ['index.html', 'assets']
  const missingFiles = requiredFiles.filter(file => {
    return !fs.existsSync(path.join(distPath, file))
  })
  
  if (missingFiles.length > 0) {
    console.error('❌ 错误: 构建结果不完整')
    console.log('缺失文件:', missingFiles.join(', '))
    process.exit(1)
  }
  
  console.log('✅ 构建结果检查通过')
}

// 创建部署包
function createDeployPackage() {
  console.log('📦 创建部署包...')
  
  const packageInfo = {
    name: 'io-performance-platform-frontend',
    version: require('./package.json').version,
    buildTime: new Date().toISOString(),
    files: []
  }
  
  // 递归获取所有文件
  function getFiles(dir, basePath = '') {
    const files = fs.readdirSync(dir)
    files.forEach(file => {
      const filePath = path.join(dir, file)
      const relativePath = path.join(basePath, file)
      
      if (fs.statSync(filePath).isDirectory()) {
        getFiles(filePath, relativePath)
      } else {
        packageInfo.files.push(relativePath)
      }
    })
  }
  
  getFiles(path.join(__dirname, 'dist'))
  
  fs.writeFileSync(
    path.join(__dirname, 'dist', 'package-info.json'),
    JSON.stringify(packageInfo, null, 2)
  )
  
  console.log('✅ 部署包创建完成')
  console.log(`📊 包含文件数量: ${packageInfo.files.length}`)
}

// 显示部署信息
function showDeployInfo() {
  console.log('\n🎉 部署准备完成！')
  console.log('=' .repeat(50))
  console.log('📁 构建目录: ./dist')
  console.log('🌐 入口文件: ./dist/index.html')
  console.log('📄 部署信息: ./dist/package-info.json')
  
  console.log('\n🔧 部署选项:')
  console.log('1. 静态文件服务器: 将dist目录部署到Nginx/Apache')
  console.log('2. CDN部署: 上传到云存储CDN')
  console.log('3. Docker容器: 使用Docker部署')
  console.log('4. 云服务: 部署到Vercel/Netlify等平台')
  
  console.log('\n📖 使用说明:')
  console.log('- 确保API后端服务已启动')
  console.log('- 配置环境变量(.env文件)')
  console.log('- 设置反向代理(如需)')
  console.log('- 配置HTTPS证书(生产环境)')
  
  console.log('\n✨ 项目已准备就绪！')
}

// 主执行流程
async function main() {
  try {
    checkNodeVersion()
    checkRequiredFiles()
    installDependencies()
    buildProject()
    checkBuildResult()
    createDeployPackage()
    showDeployInfo()
  } catch (error) {
    console.error('❌ 部署过程出错:', error.message)
    process.exit(1)
  }
}

// 执行主程序
main()