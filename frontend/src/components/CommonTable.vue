<template>
  <div class="bg-white rounded-lg shadow">
    <div class="p-4 border-b border-gray-200">
      <div class="flex justify-between items-center">
        <h3 class="text-lg font-medium text-gray-900">{{ title }}</h3>
        <div class="flex space-x-2">
          <el-input
            v-if="searchable"
            v-model="searchQuery"
            placeholder="搜索..."
            class="w-64"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><search /></el-icon>
            </template>
          </el-input>
          <el-button
            v-if="$slots.actions"
            type="primary"
            @click="handleCreate"
          >
            <el-icon><plus /></el-icon>
            新增
          </el-button>
        </div>
      </div>
    </div>

    <el-table
      :data="tableData"
      v-loading="loading"
      style="width: 100%"
      @selection-change="handleSelectionChange"
    >
      <el-table-column
        v-if="selectable"
        type="selection"
        width="55"
      />

      <el-table-column
        v-for="column in columns"
        :key="column.prop"
        :prop="column.prop"
        :label="column.label"
        :width="column.width"
        :sortable="column.sortable"
        :formatter="column.formatter"
      >
        <template #default="{ row }" v-if="column.slot">
          <slot :name="column.prop" :row="row"></slot>
        </template>
      </el-table-column>

      <el-table-column
        v-if="showActions"
        label="操作"
        :width="actionWidth"
        fixed="right"
      >
        <template #default="{ row }">
          <slot name="actions" :row="row">
            <el-button
              type="primary"
              link
              size="small"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              link
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </slot>
        </template>
      </el-table-column>
    </el-table>

    <div class="p-4 flex justify-between items-center">
      <div class="text-sm text-gray-600">
        共 {{ total }} 条记录
      </div>
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Search, Plus } from '@element-plus/icons-vue'

const props = defineProps({
  title: {
    type: String,
    default: '数据列表'
  },
  data: {
    type: Array,
    default: () => []
  },
  columns: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  total: {
    type: Number,
    default: 0
  },
  searchable: {
    type: Boolean,
    default: true
  },
  selectable: {
    type: Boolean,
    default: false
  },
  showActions: {
    type: Boolean,
    default: true
  },
  actionWidth: {
    type: [String, Number],
    default: 150
  }
})

const emit = defineEmits([
  'create',
  'edit',
  'delete',
  'search',
  'page-change',
  'size-change',
  'selection-change'
])

const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(10)

const tableData = computed(() => {
  if (props.data.length > pageSize.value) {
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return props.data.slice(start, end)
  }
  return props.data
})

const handleSearch = () => {
  emit('search', searchQuery.value)
}

const handleCreate = () => {
  emit('create')
}

const handleEdit = (row) => {
  emit('edit', row)
}

const handleDelete = (row) => {
  emit('delete', row)
}

const handleSizeChange = (size) => {
  pageSize.value = size
  emit('size-change', size)
}

const handleCurrentChange = (page) => {
  currentPage.value = page
  emit('page-change', page)
}

const handleSelectionChange = (selection) => {
  emit('selection-change', selection)
}
</script>