from __future__ import annotations

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QComboBox,
        QFileDialog,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from app.labtools.calculators.calculator_models import CalculationError
    from app.labtools.calculators.unit_conversion import format_number, supported_mass_units, supported_volume_units
    from app.labtools.recipes import default_recipe_library
    from app.labtools.recipes.recipe_models import RECIPE_REVIEW_NOTICE, Recipe, RecipeComponent, RecipeDraft, RecipeError
    from app.labtools.recipes.recipe_scaling import calculate_stock_dilution, scale_recipe
    from app.labtools.recipes.recipe_source_importer import RecipeSourceImporter
    from app.labtools.recipes.recipe_source_models import (
        NETWORK_DISABLED_MESSAGE,
        SOURCE_REVIEW_NOTICE,
        RecipeExtractionDraft,
        RecipeSourceCard,
    )
    from app.labtools.recipes.recipe_persistence import RECIPE_DRAFT_SAFETY_CATEGORY, load_user_recipe_store, save_user_recipe_store
    from app.labtools.recipes.user_recipe_store import UserRecipeStore
    from app.ui_style_tokens import COLORS, CONTROL_HEIGHT, FONT_SIZE, RADIUS, SPACING
except Exception:  # pragma: no cover
    QWidget = None  # type: ignore[assignment]


if QWidget is not None:
    SAFETY_CATEGORY_TEXT = " / ".join(RECIPE_DRAFT_SAFETY_CATEGORY.values())

    def _line_edit(placeholder: str, text: str = "") -> QLineEdit:
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setText(text)
        field.setMinimumHeight(CONTROL_HEIGHT["field"])
        return field


    def _combo(values: tuple[str, ...], current: str | None = None) -> QComboBox:
        combo = QComboBox()
        combo.addItems(values)
        if current in values:
            combo.setCurrentText(current)
        combo.setMinimumHeight(CONTROL_HEIGHT["field"])
        return combo


    class LabToolsRecipeWidget(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self.setObjectName("labToolsRecipeWorkspace")
            self.setStyleSheet(self._stylesheet())
            self._base_library = default_recipe_library()
            self._user_store = UserRecipeStore()
            self._source_importer = RecipeSourceImporter()
            self._recipes: tuple[Recipe, ...] = ()
            self._current_recipe: Recipe | None = None
            self._current_source_card: RecipeSourceCard | None = None
            self._current_extraction_draft: RecipeExtractionDraft | None = None
            self._source_recipe_draft: RecipeDraft | None = None
            self._build_ui()
            self._refresh_recipes()

        def user_recipe_store(self) -> UserRecipeStore:
            return self._user_store

        def recipe_count(self) -> int:
            return len(self._recipes)

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(SPACING["xl"], SPACING["lg"], SPACING["xl"], SPACING["xl"])
            root.setSpacing(SPACING["md"])

            title = QLabel("试剂与配方")
            title.setObjectName("labToolsSectionTitle")
            notice = QLabel(RECIPE_REVIEW_NOTICE)
            notice.setObjectName("recipeNotice")
            notice.setWordWrap(True)
            root.addWidget(title)
            root.addWidget(notice)

            self._tabs = QTabWidget()
            self._tabs.setObjectName("recipeWorkspaceTabs")
            self._tabs.addTab(self._build_library_tab(), "本地配方库")
            self._tabs.addTab(self._build_user_recipe_tab(), "用户配方")
            self._tabs.addTab(self._build_source_tab(), "外部来源草稿")
            root.addWidget(self._tabs, 1)

        def _build_library_tab(self) -> QWidget:
            tab = QWidget()
            body = QHBoxLayout(tab)
            body.setContentsMargins(0, SPACING["sm"], 0, 0)
            body.setSpacing(SPACING["md"])
            self._recipe_list = QListWidget()
            self._recipe_list.setObjectName("recipeList")
            self._recipe_list.setMinimumWidth(260)
            self._recipe_list.currentItemChanged.connect(self._handle_recipe_selected)
            body.addWidget(self._recipe_list, 1)

            right = QVBoxLayout()
            right.setSpacing(SPACING["md"])
            self._detail = QTextEdit()
            self._detail.setObjectName("recipeDetailPanel")
            self._detail.setReadOnly(True)
            self._detail.setMinimumHeight(180)
            right.addWidget(self._detail)
            right.addWidget(self._build_scale_card())
            right.addWidget(self._build_dilution_card())
            body.addLayout(right, 2)
            return tab

        def _build_user_recipe_tab(self) -> QWidget:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.setContentsMargins(0, SPACING["sm"], 0, 0)
            layout.setSpacing(SPACING["md"])
            layout.addWidget(self._build_user_recipe_card())
            layout.addWidget(self._build_user_recipe_persistence_card())
            self._user_recipe_summary = QTextEdit()
            self._user_recipe_summary.setObjectName("recipeResultPanel")
            self._user_recipe_summary.setReadOnly(True)
            self._user_recipe_summary.setText(
                "用户确认的配方仅保存在当前内存结构；只有点击保存并选择 JSON 路径后才写盘。"
                f"安全类别：{SAFETY_CATEGORY_TEXT}。"
            )
            layout.addWidget(self._user_recipe_summary, 1)
            return tab

        def _build_scale_card(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            heading = QLabel("按目标体积缩放")
            heading.setObjectName("recipeCardTitle")
            grid = QGridLayout()
            self._target_volume = _line_edit("例如 500", "500")
            self._target_volume_unit = _combo(supported_volume_units(), "mL")
            button = QPushButton("计算缩放")
            button.setObjectName("primaryButton")
            button.clicked.connect(self._handle_scale)
            grid.addWidget(QLabel("目标体积"), 0, 0)
            grid.addWidget(self._target_volume, 0, 1)
            grid.addWidget(self._target_volume_unit, 0, 2)
            grid.addWidget(button, 1, 0, 1, 3)
            self._scale_result = QTextEdit()
            self._scale_result.setObjectName("recipeResultPanel")
            self._scale_result.setReadOnly(True)
            self._scale_result.setText("选择配方并填写目标体积后计算。")
            layout.addWidget(heading)
            layout.addLayout(grid)
            layout.addWidget(self._scale_result)
            return frame

        def _build_dilution_card(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            heading = QLabel("stock-to-working 稀释")
            heading.setObjectName("recipeCardTitle")
            grid = QGridLayout()
            self._stock_x = _line_edit("例如 10×", "10×")
            self._target_x = _line_edit("例如 1×", "1×")
            self._dilution_volume = _line_edit("例如 100", "100")
            self._dilution_volume_unit = _combo(supported_volume_units(), "mL")
            self._dilution_output_unit = _combo(supported_volume_units(), "mL")
            button = QPushButton("计算稀释")
            button.setObjectName("primaryButton")
            button.clicked.connect(self._handle_dilution)
            grid.addWidget(QLabel("stock 浓度"), 0, 0)
            grid.addWidget(self._stock_x, 0, 1, 1, 2)
            grid.addWidget(QLabel("目标浓度"), 1, 0)
            grid.addWidget(self._target_x, 1, 1, 1, 2)
            grid.addWidget(QLabel("目标体积"), 2, 0)
            grid.addWidget(self._dilution_volume, 2, 1)
            grid.addWidget(self._dilution_volume_unit, 2, 2)
            grid.addWidget(QLabel("结果单位"), 3, 0)
            grid.addWidget(self._dilution_output_unit, 3, 1, 1, 2)
            grid.addWidget(button, 4, 0, 1, 3)
            self._dilution_result = QTextEdit()
            self._dilution_result.setObjectName("recipeResultPanel")
            self._dilution_result.setReadOnly(True)
            self._dilution_result.setText("填写 stock 和目标浓度后计算。")
            layout.addWidget(heading)
            layout.addLayout(grid)
            layout.addWidget(self._dilution_result)
            return frame

        def _build_user_recipe_card(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            heading = QLabel("用户自定义配方草稿")
            heading.setObjectName("recipeCardTitle")
            grid = QGridLayout()
            self._draft_name = _line_edit("配方名称")
            self._draft_category = _line_edit("分类", "用户自定义")
            self._draft_description = _line_edit("简短说明", "用户自定义配方")
            self._draft_volume = _line_edit("默认体积", "100")
            self._draft_volume_unit = _combo(supported_volume_units(), "mL")
            self._draft_component_name = _line_edit("组分名称")
            self._draft_component_amount = _line_edit("组分用量")
            self._draft_component_unit = _combo(supported_mass_units() + supported_volume_units(), "g")
            confirm = QPushButton("确认草稿")
            confirm.setObjectName("secondaryButton")
            confirm.clicked.connect(self._handle_confirm_draft)
            grid.addWidget(QLabel("名称"), 0, 0)
            grid.addWidget(self._draft_name, 0, 1, 1, 2)
            grid.addWidget(QLabel("分类"), 1, 0)
            grid.addWidget(self._draft_category, 1, 1, 1, 2)
            grid.addWidget(QLabel("说明"), 2, 0)
            grid.addWidget(self._draft_description, 2, 1, 1, 2)
            grid.addWidget(QLabel("默认体积"), 3, 0)
            grid.addWidget(self._draft_volume, 3, 1)
            grid.addWidget(self._draft_volume_unit, 3, 2)
            grid.addWidget(QLabel("组分"), 4, 0)
            grid.addWidget(self._draft_component_name, 4, 1, 1, 2)
            grid.addWidget(QLabel("用量"), 5, 0)
            grid.addWidget(self._draft_component_amount, 5, 1)
            grid.addWidget(self._draft_component_unit, 5, 2)
            grid.addWidget(confirm, 6, 0, 1, 3)
            self._draft_status = QLabel(
                "草稿确认后仅保存在当前内存结构，可导出为 JSON-compatible dict；不会自动写盘。"
                "使用前需按实验室 SOP、SDS 和试剂说明书人工核对浓度、pH、储存条件、有效期和危险性。"
            )
            self._draft_status.setObjectName("recipeSupportLine")
            self._draft_status.setWordWrap(True)
            layout.addWidget(heading)
            layout.addLayout(grid)
            layout.addWidget(self._draft_status)
            return frame

        def _build_user_recipe_persistence_card(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            heading = QLabel("本地配方草稿持久化")
            heading.setObjectName("recipeCardTitle")
            support = QLabel(
                "仅保存用户确认配方到本地 JSON；不自动保存、不联网、不调用 AI。"
                f"安全类别：{SAFETY_CATEGORY_TEXT}；"
                "载入后仍需人工核对 SOP、SDS、试剂说明书、浓度、pH、储存条件、有效期和危险性；"
                "不构成安全操作规范，不自动适配所有实验。"
            )
            support.setObjectName("recipeSupportLine")
            support.setWordWrap(True)
            row = QHBoxLayout()
            save_button = QPushButton("保存用户配方 JSON")
            save_button.setObjectName("secondaryButton")
            save_button.clicked.connect(self._handle_save_user_recipes)
            load_button = QPushButton("载入用户配方 JSON")
            load_button.setObjectName("secondaryButton")
            load_button.clicked.connect(self._handle_load_user_recipes)
            row.addWidget(save_button)
            row.addWidget(load_button)
            layout.addWidget(heading)
            layout.addWidget(support)
            layout.addLayout(row)
            return frame

        def _build_source_tab(self) -> QWidget:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.setContentsMargins(0, SPACING["sm"], 0, 0)
            layout.setSpacing(SPACING["md"])
            intro = QLabel(SOURCE_REVIEW_NOTICE)
            intro.setObjectName("recipeSupportLine")
            intro.setWordWrap(True)
            layout.addWidget(intro)
            layout.addWidget(self._build_source_request_card())
            layout.addWidget(self._build_manual_source_card())
            layout.addWidget(self._build_source_extract_card())
            self._source_status = QTextEdit()
            self._source_status.setObjectName("recipeResultPanel")
            self._source_status.setReadOnly(True)
            self._source_status.setText("网络检索当前未启用。可手动录入来源，并在人工核对后转为用户配方草稿。")
            layout.addWidget(self._source_status, 1)
            return tab

        def _build_source_request_card(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            heading = QLabel("检索需求")
            heading.setObjectName("recipeCardTitle")
            grid = QGridLayout()
            self._source_query = _line_edit("例如 PBS 配方来源")
            self._source_goal = _line_edit("用途说明，可选")
            search = QPushButton("网络检索")
            search.setObjectName("secondaryButton")
            search.clicked.connect(self._handle_disabled_network_search)
            grid.addWidget(QLabel("需求"), 0, 0)
            grid.addWidget(self._source_query, 0, 1)
            grid.addWidget(QLabel("目标"), 1, 0)
            grid.addWidget(self._source_goal, 1, 1)
            grid.addWidget(search, 2, 0, 1, 2)
            layout.addWidget(heading)
            layout.addLayout(grid)
            return frame

        def _build_manual_source_card(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            heading = QLabel("手动添加来源")
            heading.setObjectName("recipeCardTitle")
            grid = QGridLayout()
            self._manual_source_url = _line_edit("https://example.org/protocol")
            self._manual_source_title = _line_edit("来源标题")
            self._manual_source_label = _line_edit("来源标签", "用户手动录入来源")
            self._manual_source_snippet = QTextEdit()
            self._manual_source_snippet.setObjectName("recipeResultPanel")
            self._manual_source_snippet.setPlaceholderText("填写摘要或摘录内容。")
            self._manual_source_snippet.setMinimumHeight(88)
            add_source = QPushButton("生成来源卡片")
            add_source.setObjectName("secondaryButton")
            add_source.clicked.connect(self._handle_manual_source)
            grid.addWidget(QLabel("URL"), 0, 0)
            grid.addWidget(self._manual_source_url, 0, 1)
            grid.addWidget(QLabel("标题"), 1, 0)
            grid.addWidget(self._manual_source_title, 1, 1)
            grid.addWidget(QLabel("标签"), 2, 0)
            grid.addWidget(self._manual_source_label, 2, 1)
            grid.addWidget(QLabel("摘要"), 3, 0)
            grid.addWidget(self._manual_source_snippet, 3, 1)
            grid.addWidget(add_source, 4, 0, 1, 2)
            layout.addWidget(heading)
            layout.addLayout(grid)
            return frame

        def _build_source_extract_card(self) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            heading = QLabel("摘录草稿")
            heading.setObjectName("recipeCardTitle")
            grid = QGridLayout()
            self._extract_recipe_name = _line_edit("配方名称")
            self._extract_default_volume = _line_edit("默认体积", "100")
            self._extract_default_volume_unit = _combo(supported_volume_units(), "mL")
            self._extract_stock = _line_edit("浓度，例如 1×", "1×")
            self._extract_component_name = _line_edit("组分名称")
            self._extract_component_amount = _line_edit("组分用量")
            self._extract_component_unit = _combo(supported_mass_units() + supported_volume_units(), "g")
            self._extract_notes = QTextEdit()
            self._extract_notes.setObjectName("recipeResultPanel")
            self._extract_notes.setPlaceholderText("人工摘录说明、适用范围或注意事项。")
            self._extract_notes.setMinimumHeight(72)
            to_draft = QPushButton("转为用户配方草稿")
            to_draft.setObjectName("secondaryButton")
            to_draft.clicked.connect(self._handle_source_to_draft)
            confirm = QPushButton("确认保存")
            confirm.setObjectName("primaryButton")
            confirm.clicked.connect(self._handle_confirm_source_draft)
            grid.addWidget(QLabel("配方"), 0, 0)
            grid.addWidget(self._extract_recipe_name, 0, 1, 1, 2)
            grid.addWidget(QLabel("默认体积"), 1, 0)
            grid.addWidget(self._extract_default_volume, 1, 1)
            grid.addWidget(self._extract_default_volume_unit, 1, 2)
            grid.addWidget(QLabel("浓度"), 2, 0)
            grid.addWidget(self._extract_stock, 2, 1, 1, 2)
            grid.addWidget(QLabel("组分"), 3, 0)
            grid.addWidget(self._extract_component_name, 3, 1, 1, 2)
            grid.addWidget(QLabel("用量"), 4, 0)
            grid.addWidget(self._extract_component_amount, 4, 1)
            grid.addWidget(self._extract_component_unit, 4, 2)
            grid.addWidget(QLabel("摘录"), 5, 0)
            grid.addWidget(self._extract_notes, 5, 1, 1, 2)
            grid.addWidget(to_draft, 6, 0, 1, 3)
            grid.addWidget(confirm, 7, 0, 1, 3)
            layout.addWidget(heading)
            layout.addLayout(grid)
            return frame

        def _refresh_recipes(self) -> None:
            current_id = self._current_recipe.recipe_id if self._current_recipe else ""
            self._recipes = self._base_library.with_user_recipes(self._user_store.list_recipes()).list_recipes()
            self._recipe_list.clear()
            selected_row = 0
            for index, recipe in enumerate(self._recipes):
                item = QListWidgetItem(f"{recipe.name}\n{recipe.category} · {recipe.version}")
                item.setData(Qt.UserRole, recipe.recipe_id)
                self._recipe_list.addItem(item)
                if recipe.recipe_id == current_id:
                    selected_row = index
            if self._recipes:
                self._recipe_list.setCurrentRow(selected_row)
            self._render_user_recipe_summary()

        def _render_user_recipe_summary(self) -> None:
            if not hasattr(self, "_user_recipe_summary"):
                return
            recipes = self._user_store.list_recipes()
            if not recipes:
                self._user_recipe_summary.setText(
                    "尚未确认用户配方。用户草稿和来源摘录草稿均不会自动写盘。"
                    f"\n安全类别：{SAFETY_CATEGORY_TEXT}。"
                    "\n使用前需按实验室 SOP、SDS 和试剂说明书人工核对浓度、pH、储存条件、有效期和危险性。"
                )
                return
            lines = ["已确认用户配方"]
            for recipe in recipes:
                source = recipe.source_title or recipe.source_label
                lines.append(f"- {recipe.name}；版本：{recipe.version}；来源：{source}")
            lines.extend(
                [
                    "",
                    "本地持久化",
                    "点击“保存用户配方 JSON”并选择路径后才写盘；保存时会进行基础安全范围检查并避免覆盖同名文件。",
                    "",
                    "安全类别",
                    SAFETY_CATEGORY_TEXT,
                    "使用前需确认浓度、pH、储存条件、有效期和危险性；不构成安全操作规范，不自动适配所有实验。",
                ]
            )
            lines.extend(["", "复核提示", RECIPE_REVIEW_NOTICE])
            self._user_recipe_summary.setText("\n".join(lines))

        def _handle_recipe_selected(self, current: QListWidgetItem | None) -> None:
            if current is None:
                return
            recipe_id = str(current.data(Qt.UserRole) or "")
            self._current_recipe = next((recipe for recipe in self._recipes if recipe.recipe_id == recipe_id), None)
            self._render_detail()

        def _render_detail(self) -> None:
            recipe = self._current_recipe
            if recipe is None:
                self._detail.setText("请选择配方。")
                return
            lines = [
                recipe.name,
                f"分类：{recipe.category}",
                f"说明：{recipe.description}",
                f"浓度：{recipe.stock_concentration}",
                f"默认体积：{format_number(recipe.default_volume)} {recipe.default_volume_unit}",
                f"来源：{recipe.source_label}",
                f"版本：{recipe.version}",
                f"适用范围：{recipe.description}",
                "",
                "组分",
            ]
            for component in recipe.components:
                optional = "（可选）" if component.optional else ""
                lines.append(f"- {component.name}{optional}：{format_number(component.amount)} {component.unit}；{component.role}")
            lines.extend(["", "注意事项", *[f"- {note}" for note in recipe.preparation_notes]])
            lines.extend(["", "安全提示", *[f"- {note}" for note in recipe.safety_notes]])
            lines.extend(
                [
                    "",
                    "安全类别",
                    SAFETY_CATEGORY_TEXT,
                    "使用前需确认浓度、pH、储存条件、有效期和危险性；不构成安全操作规范，不自动适配所有实验。",
                ]
            )
            lines.extend(["", "复核提示", recipe.review_notice])
            self._detail.setText("\n".join(lines))
            self._target_volume.setText(format_number(recipe.default_volume))
            self._target_volume_unit.setCurrentText(recipe.default_volume_unit)
            if recipe.stock_concentration.endswith("×"):
                self._stock_x.setText(recipe.stock_concentration)

        def _handle_scale(self) -> None:
            if self._current_recipe is None:
                self._scale_result.setText("请先选择配方。")
                return
            try:
                result = scale_recipe(self._current_recipe, self._target_volume.text(), self._target_volume_unit.currentText())
            except (CalculationError, RecipeError) as exc:
                self._scale_result.setText(f"输入需要调整\n{exc}")
                return
            self._scale_result.setText(result.as_text(format_number))

        def _handle_dilution(self) -> None:
            try:
                result = calculate_stock_dilution(
                    self._stock_x.text(),
                    self._target_x.text(),
                    self._dilution_volume.text(),
                    self._dilution_volume_unit.currentText(),
                    output_volume_unit=self._dilution_output_unit.currentText(),
                )
            except CalculationError as exc:
                self._dilution_result.setText(f"输入需要调整\n{exc}")
                return
            self._dilution_result.setText(result.as_text())

        def _handle_confirm_draft(self) -> None:
            try:
                component = RecipeComponent(
                    name=self._draft_component_name.text().strip(),
                    amount=float(self._draft_component_amount.text().strip()),
                    unit=self._draft_component_unit.currentText(),
                    role="用户输入组分",
                )
                draft = RecipeDraft(
                    name=self._draft_name.text().strip(),
                    category=self._draft_category.text().strip(),
                    description=self._draft_description.text().strip(),
                    stock_concentration="1×",
                    default_volume=float(self._draft_volume.text().strip()),
                    default_volume_unit=self._draft_volume_unit.currentText(),
                    components=(component,),
                    preparation_notes=("用户草稿已确认；请按实验室 SOP 复核。",),
                    safety_notes=("用户备注仅在 LabTools 内显示，不传递到其他模块。",),
                )
                recipe = self._user_store.confirm_draft(draft)
            except ValueError:
                self._draft_status.setText("输入需要调整\n用量和体积必须是有效数字。")
                return
            except RecipeError as exc:
                self._draft_status.setText(f"输入需要调整\n{exc}")
                return
            self._draft_status.setText(f"已确认用户配方：{recipe.name}。当前仅保存在内存结构；如需持久化，请手动保存为本地 JSON。")
            self._current_recipe = recipe
            self._refresh_recipes()

        def _handle_disabled_network_search(self) -> None:
            query = self._source_query.text().strip()
            suffix = f"\n已记录需求：{query}" if query else ""
            self._source_status.setText(f"{NETWORK_DISABLED_MESSAGE} 本阶段不会访问网页、下载内容或调用 AI。{suffix}")

        def _handle_manual_source(self) -> None:
            try:
                card = self._source_importer.create_manual_source_card(
                    source_url=self._manual_source_url.text(),
                    source_title=self._manual_source_title.text(),
                    source_label=self._manual_source_label.text(),
                    snippet=self._manual_source_snippet.toPlainText(),
                )
            except RecipeError as exc:
                self._source_status.setText(f"来源需要调整\n{exc}")
                return
            self._current_source_card = card
            self._current_extraction_draft = None
            self._source_recipe_draft = None
            lines = [
                "已生成来源卡片（未访问网络）",
                f"标题：{card.title}",
                f"来源：{card.source_label}",
                f"URL：{card.source_url or '未填写'}",
                f"访问记录：{card.accessed_at}",
                "",
                "摘要",
                card.snippet,
                "",
                "复核提示",
                card.trust_note,
            ]
            self._source_status.setText("\n".join(lines))

        def _handle_source_to_draft(self) -> None:
            if self._current_source_card is None:
                self._source_status.setText("请先手动添加来源并生成来源卡片。")
                return
            try:
                component = RecipeComponent(
                    name=self._extract_component_name.text().strip(),
                    amount=float(self._extract_component_amount.text().strip()),
                    unit=self._extract_component_unit.currentText(),
                    role="来源摘录组分",
                )
                extraction_draft = self._source_importer.create_extraction_draft(
                    source_card=self._current_source_card,
                    recipe_name=self._extract_recipe_name.text(),
                    extracted_components=(component,),
                    extracted_notes=(self._extract_notes.toPlainText().strip(),),
                    safety_notes=(SOURCE_REVIEW_NOTICE,),
                    preparation_notes=("用户手动摘录，未自动采集网页内容。",),
                    warnings=("来源内容需要人工核对。",),
                    edited_by_user=True,
                )
                recipe_draft = self._source_importer.to_user_recipe_draft(
                    extraction_draft,
                    default_volume=float(self._extract_default_volume.text().strip()),
                    default_volume_unit=self._extract_default_volume_unit.currentText(),
                    stock_concentration=self._extract_stock.text(),
                )
            except ValueError:
                self._source_status.setText("摘录需要调整\n用量和默认体积必须是有效数字。")
                return
            except RecipeError as exc:
                self._source_status.setText(f"摘录需要调整\n{exc}")
                return
            self._current_extraction_draft = extraction_draft
            self._source_recipe_draft = recipe_draft
            lines = [
                "已转为用户配方草稿，尚未确认保存。",
                f"配方：{recipe_draft.name}",
                f"来源标题：{recipe_draft.source_title}",
                f"默认体积：{format_number(recipe_draft.default_volume)} {recipe_draft.default_volume_unit}",
                f"组分数：{len(recipe_draft.components)}",
                "",
                "下一步",
                "请人工核对来源、组分和单位后点击“确认保存”。",
            ]
            self._source_status.setText("\n".join(lines))

        def _handle_confirm_source_draft(self) -> None:
            if self._source_recipe_draft is None:
                self._source_status.setText("请先将来源摘录转为用户配方草稿。")
                return
            try:
                recipe = self._user_store.confirm_draft(self._source_recipe_draft)
            except RecipeError as exc:
                self._source_status.setText(f"保存需要调整\n{exc}")
                return
            self._source_status.setText(f"已确认保存用户配方：{recipe.name}。当前仅保存在内存结构；如需持久化，请手动保存为本地 JSON。")
            self._current_recipe = recipe
            self._refresh_recipes()

        def _handle_save_user_recipes(self) -> None:
            recipes = self._user_store.list_recipes()
            if not recipes:
                self._user_recipe_summary.setText("尚未确认用户配方，未写入任何文件。")
                return
            path = self._select_user_recipe_save_path()
            if not path:
                self._user_recipe_summary.setText("已取消保存；未写入任何文件。")
                return
            try:
                result = self._perform_save_user_recipes(path)
            except RecipeError as exc:
                self._user_recipe_summary.setText(f"保存需要调整\n{exc}")
                return
            self._user_recipe_summary.setText(
                "\n".join(
                    [
                        "用户配方 JSON 已保存",
                        f"路径：{result.path}",
                        f"schema：{result.schema_version}",
                        f"配方数：{result.recipe_count}",
                        f"安全类别：{SAFETY_CATEGORY_TEXT}",
                        "",
                        "复核提示",
                        result.review_notice,
                    ]
                )
            )

        def _handle_load_user_recipes(self) -> None:
            path = self._select_user_recipe_load_path()
            if not path:
                self._user_recipe_summary.setText("已取消载入；当前用户配方未改变。")
                return
            try:
                result = self._perform_load_user_recipes(path)
            except RecipeError as exc:
                self._user_recipe_summary.setText(f"载入需要调整\n{exc}")
                return
            import_result = getattr(self, "_last_recipe_import_result", None)
            import_lines: list[str] = []
            if import_result is not None:
                import_lines.extend(
                    [
                        f"实际写入当前内存配方数：{import_result.imported_count}",
                        f"recipe_id 冲突数：{import_result.conflict_count}",
                    ]
                )
                versions = sorted({recipe.version for recipe in import_result.imported_recipes if recipe.version})
                if versions:
                    import_lines.append(f"载入版本：{', '.join(versions)}")
                import_lines.extend(import_result.warnings)
            self._refresh_recipes()
            self._user_recipe_summary.setText(
                "\n".join(
                    [
                        "用户配方 JSON 已载入",
                        f"路径：{result.path}",
                        f"schema：{result.schema_version}",
                        f"载入配方数：{result.recipe_count}",
                        f"安全类别：{SAFETY_CATEGORY_TEXT}",
                        *import_lines,
                        "",
                        "复核提示",
                        result.review_notice,
                    ]
                )
            )

        def _select_user_recipe_save_path(self) -> str:
            path, _selected_filter = QFileDialog.getSaveFileName(
                self,
                "保存用户配方草稿 JSON",
                "labtools_user_recipe_drafts.json",
                "JSON Files (*.json)",
            )
            return path

        def _select_user_recipe_load_path(self) -> str:
            path, _selected_filter = QFileDialog.getOpenFileName(
                self,
                "载入用户配方草稿 JSON",
                "",
                "JSON Files (*.json)",
            )
            return path

        def _perform_save_user_recipes(self, path: str):
            return save_user_recipe_store(self._user_store.list_recipes(), path)

        def _perform_load_user_recipes(self, path: str):
            result = load_user_recipe_store(path)
            self._last_recipe_import_result = self._user_store.import_recipes_with_summary(result.recipes)
            return result

        def _stylesheet(self) -> str:
            return f"""
            QWidget#labToolsRecipeWorkspace {{
                background: {COLORS["background"]};
                color: {COLORS["text"]};
                font-size: {FONT_SIZE["body"]}px;
            }}
            QLabel#labToolsSectionTitle {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["page_title"]}px;
                font-weight: 760;
            }}
            QLabel#recipeNotice, QLabel#recipeSupportLine {{
                color: {COLORS["muted"]};
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 10px;
            }}
            QLabel#recipeCardTitle {{
                color: {COLORS["bio"]};
                font-weight: 700;
            }}
            QFrame#labToolsCard {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
            }}
            QListWidget#recipeList, QTextEdit#recipeDetailPanel, QTextEdit#recipeResultPanel {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px;
            }}
            QPushButton#primaryButton {{
                color: #FFFFFF;
                background: {COLORS["bio"]};
                border: 1px solid {COLORS["bio"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 12px;
                font-weight: 700;
            }}
            QPushButton#secondaryButton {{
                color: {COLORS["bio"]};
                background: {COLORS["bio_soft"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 12px;
                font-weight: 600;
            }}
            """

else:  # pragma: no cover

    class LabToolsRecipeWidget:  # type: ignore[no-redef]
        pass
