# Bioinformatics B5.15 - UI Single Recognition Entry Cleanup

日期：2026-05-15

## 目标

清理 Bioinformatics 数据导入与检索相关页面中的重复“进入数据识别”入口，让每个页面只保留底部全局下一步按钮作为进入数据识别的唯一主入口。

## 修改内容

### 数据导入与检索主页面

- 移除了“待处理数据集”区块右下角的批量操作按钮“进入数据识别”。
- 保留区块内局部操作：
  - 下载所选
  - 删除所选
  - 查看详情
- 保留页面底部全局按钮“下一步：数据识别”，作为唯一进入数据识别入口。
- 底部状态继续显示：
  - 已保存数据来源数量
  - 下载列表 / 待处理数量
  - 可进入数据识别数量
  - 下一步提示

### 中文研究主题检索子页面

- 移除了已选数据源区块中“下一步”列里的“进入数据识别”文案，改为状态型文案“可识别”。
- 移除了已选 GEO 数据集区块中复用的批量“进入数据识别”按钮。
- 保留区块内局部操作：
  - 下载所选 / 下载补充文件
  - 删除所选
  - 查看详情
  - 保存 / 加入下载列表 / 生成中文简介
  - 返回数据来源页
- 保留页面底部全局按钮“下一步：进入数据识别”，作为唯一进入数据识别入口。
- 底部状态继续显示：
  - 已选 GEO / TCGA / GTEx 数量
  - 可进入识别数量
  - 当前状态或下一步建议

## 业务逻辑边界

本阶段只修改 Bioinformatics UI 入口展示和 UI 测试。

未修改：

- 数据导入业务逻辑
- GSE 检索业务逻辑
- 中文研究问题检索业务逻辑
- 下载业务逻辑
- acquisition 记录逻辑
- recognition 逻辑
- standardization 逻辑
- Meta / LabTools / UIShell / Integration / ReleaseBuild / MainLine

未执行：

- 打包
- 覆盖桌面入口
- 远程 push

## 测试覆盖

新增或更新的 UI 断言覆盖：

- 数据导入与检索主页面只存在一个包含“数据识别”的主按钮：`下一步：数据识别`。
- 点击底部 `下一步：数据识别` 仍能发出进入 recognition 的信号。
- 待处理数据集区块仍保留 `下载所选` / `删除所选`。
- 中文研究主题检索子页面只存在一个包含“进入数据识别”的主按钮：`下一步：进入数据识别`。
- 点击底部 `下一步：进入数据识别` 仍能进入 recognition 页面。
- GEO 下载候选、补充文件下载、pending dataset 展示相关测试继续保留并通过。

## 验证命令

- `python3 -m pytest tests/bioinformatics -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
- `python3 -m app.main --smoke-test`
- `git diff --check`
- `git diff --cached --check`

## 结果

- `python3 -m pytest tests/bioinformatics -q`：251 passed。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：155 passed。
- `python3 -m app.main --smoke-test`：通过，source launch smoke 输出正常。
- `git diff --check`：通过。
- `git diff --cached --check`：通过。

本阶段不包含业务逻辑迁移或打包验证。
