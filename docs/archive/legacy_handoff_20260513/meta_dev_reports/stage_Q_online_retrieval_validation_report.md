# Stage Q Online Retrieval Validation Report

## 本阶段目标

在用户授权后，执行只读 PubMed 外部检索验证，确认联网成功、失败回退、检索历史和导入到现有 `literature_records` 的路径可用。Stage Q 不接入 Embase、WOS、CNKI，也不保存 API key。

## 实际完成内容

- 新增 `OnlineRetrievalValidationService`。
- 支持 PubMed E-utilities `esearch` + `efetch` 最小只读验证。
- 输出 PubMed 记录到 `project_dir/literature/pubmed_retrieval_<timestamp>_records.json`。
- 保存检索历史到 `project_dir/retrieval/pubmed_retrieval_history.json`。
- 成功时登记 Data Center：`module=meta_analysis`，`data_type=literature_records`。
- 复用 Task Center 现有 `literature_import` task type，避免修改 shared 枚举。
- 失败时返回用户可读 message，写入 history，不阻塞本地流程。

## 安全边界

- 只读检索。
- 不上传用户隐私数据。
- 不保存 API key。
- 不把 API key 写入 URL 或 history。
- 网络失败只记录 warning 和 details，不影响本地 Meta Analysis 主链。

## 新增/修改文件

- `app/meta_analysis/services/online_retrieval_validation_service.py`
- `tests/meta_analysis/test_stage_q_online_retrieval_validation.py`
- `docs/meta_dev_reports/stage_Q_online_retrieval_validation_report.md`

## 输出路径

- Literature records: `project_dir/literature/pubmed_retrieval_<timestamp>_records.json`
- Retrieval history: `project_dir/retrieval/pubmed_retrieval_history.json`

## Data Center / Task Center

- Data Center：`literature_records`
- Task Center：复用 `literature_import`

## Live PubMed Validation

已执行一次授权后的只读 PubMed 小查询：

- Query: `statin mortality randomized trial`
- Retmax: `2`
- Result: success
- Fetched records: `2`
- PMIDs: `41952094`, `41935556`
- Output existed in temporary project: yes
- Retrieval history existed in temporary project: yes
- Data Center data type: `literature_records`
- Task status: `completed`
- API key saved: false
- Private data uploaded: false

首次 live run 遇到本机 SSL certificate verify failure；服务按预期返回 warning、写入 history、不影响本地流程。随后默认 fetcher 改为在本地已有 `certifi` 时使用 CA bundle，保持证书校验开启，第二次 live run 成功。

## 测试结果

- Stage Q focused tests: `2 passed`
- Live PubMed validation: success, 2 records fetched
- Full test results recorded in final handoff.

## 当前限制

- 当前只支持 PubMed 最小验证，不是完整检索策略管理系统。
- 未实现 PMID/DOI 元数据批量补全 UI。
- 未实现 rate-limit/backoff 策略，只保留失败不崩溃行为。
- 未实现 Embase、WOS、CNKI 等需账号或授权的数据源。
