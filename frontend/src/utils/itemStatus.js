export function getItemStatusMeta(status) {
  const map = {
    pending: {
      label: '待处理',
      className: 'pending',
      tagType: 'warning',
      icon: 'Clock',
    },
    matched: {
      label: '已匹配',
      className: 'matched',
      tagType: 'primary',
      icon: 'Connection',
    },
    closed: {
      label: '已完成',
      className: 'closed',
      tagType: 'success',
      icon: 'CircleCheck',
    },
  }

  return map[status] || {
    label: status || '未知状态',
    className: 'unknown',
    tagType: 'info',
    icon: null,
  }
}
