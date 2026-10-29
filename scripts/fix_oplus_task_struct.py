"""补回 oplus_task_struct 中被公开源码删掉的风驰 scx 字段，使布局与原厂一致。

原厂内核（CONFIG_HMBIRD_SCHED）在 lkinfo 之后嵌有 struct scx_entity scx（176 字节），
公开源码删除了它，后续字段整体前移，原厂厂商模块按原偏移读写导致开机崩溃。
这里只占位、不实现风驰；结构定义按原厂内核 BTF 逐字段核对。

用法: fix_oplus_task_struct.py <sa_common_struct.h>
"""
import os
import sys

DEFS = """struct scx_task_stats {
	u64	mark_start;
	u64	window_start;
	u32	sum;
	u32	sum_history[5];
	int	cidx;
	u32	demand;
	u16	demand_scaled;
	void	*sdsq;
};

struct scx_dispatch_q;
struct scx_entity {
	struct scx_dispatch_q	*dsq;
	struct {
		struct list_head	fifo;
		struct rb_node		priq;
	} dsq_node;
	u32			flags;
	u32			dsq_flags;
	s32			sticky_cpu;
	unsigned long		runnable_at;
	u64			slice;
	u64			dsq_vtime;
	int			gdsq_idx;
	int			ext_flags;
	int			prio_backup;
	unsigned long		sched_prop;
	struct scx_task_stats	sts;
};

"""
ANCHOR_STRUCT = "struct oplus_task_struct {\n"
ANCHOR_FIELD = "\tstruct locking_info lkinfo;\n/*#endif*/\n"
FIELD = "\tstruct scx_entity scx;\n"

path = sys.argv[1]
real = os.path.realpath(path)
if not os.path.exists(real):
    sys.exit(f"❌ 找不到 {path}（-> {real}）")
src = open(real, encoding="utf-8", newline="").read()
if "struct scx_entity" in src:
    print(f"源码已有 struct scx_entity，跳过: {real}")
    sys.exit(0)
for anchor in (ANCHOR_STRUCT, ANCHOR_FIELD):
    if src.count(anchor) != 1:
        sys.exit(f"❌ 锚点出现 {src.count(anchor)} 次，源码结构已变，需重新核对布局: {anchor!r}")
src = src.replace(ANCHOR_STRUCT, DEFS + ANCHOR_STRUCT).replace(ANCHOR_FIELD, ANCHOR_FIELD + FIELD)
open(real, "w", encoding="utf-8", newline="").write(src)
print(f"已在 oplus_task_struct 的 lkinfo 后补回 struct scx_entity scx: {real}")
