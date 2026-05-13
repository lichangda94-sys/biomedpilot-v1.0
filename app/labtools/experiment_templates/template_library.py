from __future__ import annotations

from app.labtools.experiment_templates.template_models import ExperimentRecordDraft, ExperimentTemplate, ExperimentTemplateError


def default_experiment_templates() -> tuple[ExperimentTemplate, ...]:
    return (
        ExperimentTemplate(
            template_id="qpcr_plan_draft",
            name="qPCR 实验计划模板",
            category="qPCR",
            description="用于整理 qPCR 实验目的、样本分组、试剂、关键体系参数和输出文件。",
            purpose_prompt="例如：验证目标基因在处理组与对照组中的表达差异。",
            sample_group_fields=("样本编号", "处理组/对照组", "生物学重复", "内参基因"),
            reagent_fields=("qPCR master mix", "forward/reverse primer", "template/cDNA", "nuclease-free water"),
            key_parameter_fields=("单孔体系体积", "技术重复数", "退火温度", "阴性/阳性对照", "Ct 判读规则"),
            output_file_fields=("plate layout", "raw Ct table", "QC notes", "analysis summary draft"),
            note_fields=("引物批号", "template 稀释倍数", "异常孔备注"),
            safety_notes=("不自动设计 primer，不生成诊断结论；所有 Ct 解释需人工复核。",),
        ),
        ExperimentTemplate(
            template_id="western_blot_plan_draft",
            name="Western blot 实验计划模板",
            category="Western blot",
            description="用于整理 WB 样本、抗体、上样量、转膜和输出文件草稿。",
            purpose_prompt="例如：比较处理组与对照组中目标蛋白表达。",
            sample_group_fields=("样本编号", "处理条件", "蛋白浓度", "目标上样量", "内参/总蛋白策略"),
            reagent_fields=("primary antibody", "secondary antibody", "loading buffer", "running/transfer buffer"),
            key_parameter_fields=("凝胶浓度", "上样体积", "转膜条件", "封闭条件", "曝光设置"),
            output_file_fields=("原始膜图", "曝光记录", "样本上样表", "人工复核备注"),
            note_fields=("抗体批号", "膜号", "异常条带说明"),
            safety_notes=("不做 WB/凝胶灰度或条带自动分析；图像解释需人工复核。",),
        ),
        ExperimentTemplate(
            template_id="cell_seeding_plan_draft",
            name="细胞实验接种计划模板",
            category="细胞实验",
            description="用于整理接种密度、孔板、处理组、培养基和输出文件草稿。",
            purpose_prompt="例如：为处理实验准备 24 孔板细胞接种计划。",
            sample_group_fields=("细胞系/批次", "处理组", "孔板位置", "目标每孔细胞数", "重复数"),
            reagent_fields=("细胞悬液", "培养基", "处理试剂", "PBS/消化液"),
            key_parameter_fields=("孔板类型", "每孔体积", "接种密度", "overage", "培养时间"),
            output_file_fields=("plate map", "cell count note", "seeding calculation draft", "观察记录"),
            note_fields=("细胞活率", "传代数", "混匀/计数误差备注"),
            safety_notes=("不替代细胞培养 SOP；接种前需复核细胞活率、污染风险和实验设计。",),
        ),
        ExperimentTemplate(
            template_id="scratch_assay_record_draft",
            name="Scratch assay 记录模板",
            category="图像记录",
            description="用于整理划痕实验分组、拍摄时间点、ROI/threshold 记录和输出文件草稿。",
            purpose_prompt="例如：记录处理组对细胞迁移辅助测量的影响。",
            sample_group_fields=("样本/孔位", "处理组", "时间点", "重复数"),
            reagent_fields=("培养基", "处理试剂", "染色/固定试剂（如适用）"),
            key_parameter_fields=("拍摄倍率", "时间点", "ROI 规则", "threshold 模式", "图像命名规则"),
            output_file_fields=("原图路径摘要", "ROI export package", "CSV summary", "manual review notes"),
            note_fields=("划痕宽度一致性", "细胞状态", "排除孔说明"),
            safety_notes=("仅作为 manual ROI / threshold 半定量记录草稿，不自动判断迁移效果。",),
        ),
        ExperimentTemplate(
            template_id="immunofluorescence_image_record_draft",
            name="免疫荧光图像记录模板",
            category="图像记录",
            description="用于整理 IF 染色、成像、manual ROI 复核和输出文件草稿。",
            purpose_prompt="例如：记录目标蛋白荧光信号的手动 ROI 辅助分析。",
            sample_group_fields=("样本编号", "处理组", "视野编号", "通道", "重复数"),
            reagent_fields=("primary antibody", "secondary antibody", "mounting medium", "染核试剂"),
            key_parameter_fields=("曝光时间", "通道设置", "ROI 规则", "background ROI 规则", "显微镜设置"),
            output_file_fields=("原始图片", "ROI overlay", "CSV summary", "manual review notes"),
            note_fields=("曝光饱和检查", "背景区域选择", "批次差异备注"),
            safety_notes=("仅记录 manual ROI grayscale 辅助分析；不做自动细胞识别或自动荧光结论。",),
        ),
    )


class ExperimentTemplateLibrary:
    def __init__(self, templates: tuple[ExperimentTemplate, ...] | None = None) -> None:
        self._templates = tuple(templates or default_experiment_templates())
        self._by_id = {template.template_id: template for template in self._templates}

    def list_templates(self) -> tuple[ExperimentTemplate, ...]:
        return self._templates

    def get_template(self, template_id: str) -> ExperimentTemplate | None:
        return self._by_id.get(template_id)


def create_record_draft(
    template: ExperimentTemplate,
    *,
    purpose: str,
    sample_groups: tuple[str, ...],
    reagents: tuple[str, ...],
    key_parameters: tuple[str, ...],
    output_files: tuple[str, ...],
    notes: tuple[str, ...] = (),
) -> ExperimentRecordDraft:
    purpose = purpose.strip()
    if not purpose:
        raise ExperimentTemplateError("请填写实验目的。")
    cleaned_groups = _clean_lines(sample_groups)
    cleaned_reagents = _clean_lines(reagents)
    cleaned_parameters = _clean_lines(key_parameters)
    cleaned_outputs = _clean_lines(output_files)
    if not cleaned_groups:
        raise ExperimentTemplateError("请至少填写 1 条样本分组。")
    if not cleaned_reagents:
        raise ExperimentTemplateError("请至少填写 1 条试剂或材料。")
    if not cleaned_parameters:
        raise ExperimentTemplateError("请至少填写 1 条关键参数。")
    if not cleaned_outputs:
        raise ExperimentTemplateError("请至少填写 1 条输出文件或记录。")
    return ExperimentRecordDraft(
        template_id=template.template_id,
        template_name=template.name,
        purpose=purpose,
        sample_groups=cleaned_groups,
        reagents=cleaned_reagents,
        key_parameters=cleaned_parameters,
        output_files=cleaned_outputs,
        notes=_clean_lines(notes),
    )


def draft_markdown_preview(draft: ExperimentRecordDraft) -> str:
    lines = [
        "## LabTools 实验记录结构化草稿",
        "",
        f"- 模板：{draft.template_name}",
        f"- 状态：{draft.status}",
        f"- 创建时间：{draft.created_at}",
        "",
        "### 实验目的",
        draft.purpose,
        "",
        "### 样本分组",
        *[f"- {item}" for item in draft.sample_groups],
        "",
        "### 试剂/材料",
        *[f"- {item}" for item in draft.reagents],
        "",
        "### 关键参数",
        *[f"- {item}" for item in draft.key_parameters],
        "",
        "### 输出文件/记录",
        *[f"- {item}" for item in draft.output_files],
    ]
    if draft.notes:
        lines.extend(["", "### 备注", *[f"- {item}" for item in draft.notes]])
    lines.extend(["", "### 人工复核提示", draft.review_notice])
    return "\n".join(lines)


def _clean_lines(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(value.strip() for value in values if value.strip())
