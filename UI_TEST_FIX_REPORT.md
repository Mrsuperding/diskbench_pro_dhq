# UI自动化测试修复报告

**项目**：DiskBench Pro  
**日期**：2026-05-07  
**文件路径**：`test/frontend/ui/page_objects/tasks/tasks_list_page.py`

---

## 问题描述

任务列表页面的UI自动化测试用例执行失败，主要涉及以下测试：

- `test_tasks_page_elements_visible` - 状态筛选元素可见性检查
- `test_status_filter_works` - 状态筛选功能测试
- `test_reset_button_clears_filters` - 重置筛选功能测试

---

## 问题分析

### 1. 文件编码问题（核心问题）

**现象**：测试日志显示选择器被解析为乱码

```
waiting for locator(".el-select[placeholder="״̬ɸѡ"]")
```

**根因**：`tasks_list_page.py` 文件保存为 UTF-8 编码，但运行时 Python 解释器的默认编码（Windows GBK/CP1252）导致中文字符串被错误解码。

**验证**：
```python
# 文件实际内容
STATUS_FILTER = '.el-select[placeholder="状态筛选"]'  # UTF-8

# 运行时被错误解码为
'.el-select[placeholder="״̬ɸѡ"]'  # GBK解码结果
```

### 2. Element Plus 下拉选项属性问题

**现象**：修复编码问题后，仍无法点击下拉选项

**分析**：
- `el-option` 元素的 `value` 属性实际为 `None`
- 使用 `value` 选择器 `.el-option[value="pending"]` 无法匹配

**验证**：
```python
# 查询结果
items = page.query_selector_all('.el-select-dropdown__item')
# text="待执行" value=None data-value=None
```

---

## 解决方案

### 修改1：替换状态筛选选择器

**文件**：`tasks_list_page.py` 第34行

```python
# 修改前（有编码问题）
STATUS_FILTER = '.el-select[placeholder="状态筛选"]'

# 修改后（使用类选择器）
STATUS_FILTER = '.w-32.el-select'
```

### 修改2：重写下拉选项点击逻辑

**文件**：`tasks_list_page.py` 第129-157行

```python
def filter_by_status(self, status: str):
    """按状态筛选"""
    self.click(self.selectors.STATUS_FILTER)
    self.wait.for_visible('.el-select-dropdown', timeout=5000)

    if status == "":
        self._click_dropdown_item_by_index(0)  # 全部
    elif status == "pending":
        self._click_dropdown_item_by_index(1)  # 待执行
    elif status == "running":
        self._click_dropdown_item_by_index(2)  # 运行中
    elif status == "completed":
        self._click_dropdown_item_by_index(3)  # 已完成
    elif status == "failed":
        self._click_dropdown_item_by_index(4)  # 失败

def _click_dropdown_item_by_index(self, index: int):
    """通过索引点击下拉选项"""
    items = self.page.query_selector_all('.el-select-dropdown__item')
    if len(items) > index:
        items[index].click()
```

### 修改3：移除无用的选择器常量

**文件**：`tasks_list_page.py` 第87-91行

```python
# 这些选择器不再使用（因为 value 属性为 None）
STATUS_OPTION_ALL = 'el-option[value=""]'
STATUS_OPTION_PENDING = 'el-option[value="pending"]'
STATUS_OPTION_RUNNING = 'el-option[value="running"]'
STATUS_OPTION_COMPLETED = 'el-option[value="completed"]'
STATUS_OPTION_FAILED = 'el-option[value="failed"]'
```

---

## 测试结果

修复后运行全部16个测试用例：

```bash
pytest test/frontend/ui/tests/test_tasks_pom.py -v
```

**结果**：16 passed

---

## 经验总结

### 1. 文件编码注意事项

- Python 项目中避免在字符串选择器中使用非ASCII字符
- 如需使用中文/日文等字符，务必确保：
  - 文件保存为 UTF-8 BOM 格式
  - 或使用 Unicode 转义（\u5b57\u7b26）
  - 或使用不依赖文字的替代选择器

### 2. 前端组件属性问题

- Element Plus 的 `el-option` 的 `value` 属性需要显式绑定
- 如果 Vue 模板中未正确绑定 `value`，则 `el-option` 的 `value` 为 `None`
- 测试时需要先检查实际 DOM 结构，而不仅仅依赖文档

### 3. 下拉选项点击策略

- 优先使用稳定的属性选择器（id、data-* 属性）
- 其次使用 CSS 类选择器
- 最后考虑使用索引（最不稳健，但有时是唯一选择）

---

## 相关文件

| 文件 | 修改内容 |
|------|---------|
| `test/frontend/ui/page_objects/tasks/tasks_list_page.py` | 修改选择器和点击逻辑 |

---

## 参考信息

- Element Plus Select 组件文档
- Playwright 选择器最佳实践
- Python 字符串编码处理
