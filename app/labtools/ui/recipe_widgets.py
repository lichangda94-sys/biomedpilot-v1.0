from __future__ import annotations

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QComboBox,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from app.labtools.calculators.calculator_models import CalculationError
    from app.labtools.calculators.unit_conversion import format_number, supported_mass_units, supported_volume_units
    from app.labtools.recipes import default_recipe_library
    from app.labtools.recipes.recipe_models import RECIPE_REVIEW_NOTICE, Recipe, RecipeComponent, RecipeDraft, RecipeError
    from app.labtools.recipes.recipe_scaling import calculate_stock_dilution, scale_recipe
    from app.labtools.recipes.user_recipe_store import UserRecipeStore
    from app.ui_style_tokens import COLORS, CONTROL_HEIGHT, FONT_SIZE, RADIUS, SPACING
except Exception:  # pragma: no cover
    QWidget = None  # type: ignore[assignment]


if QWidget is not None:

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
            self._recipes: tuple[Recipe, ...] = ()
            self._current_recipe: Recipe | None = None
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

            body = QHBoxLayout()
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
            right.addWidget(self._build_user_recipe_card())
            body.addLayout(right, 2)
            root.addLayout(body, 1)

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
            self._draft_status = QLabel("草稿确认后仅保存在当前内存结构，可导出为 JSON-compatible dict；不会自动写盘。")
            self._draft_status.setObjectName("recipeSupportLine")
            self._draft_status.setWordWrap(True)
            layout.addWidget(heading)
            layout.addLayout(grid)
            layout.addWidget(self._draft_status)
            return frame

        def _refresh_recipes(self) -> None:
            current_id = self._current_recipe.recipe_id if self._current_recipe else ""
            self._recipes = self._base_library.with_user_recipes(self._user_store.list_recipes()).list_recipes()
            self._recipe_list.clear()
            selected_row = 0
            for index, recipe in enumerate(self._recipes):
                item = QListWidgetItem(f"{recipe.name}\n{recipe.category}")
                item.setData(Qt.UserRole, recipe.recipe_id)
                self._recipe_list.addItem(item)
                if recipe.recipe_id == current_id:
                    selected_row = index
            if self._recipes:
                self._recipe_list.setCurrentRow(selected_row)

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
            self._draft_status.setText(f"已确认用户配方：{recipe.name}。本阶段仅保存在内存结构，不自动写盘。")
            self._current_recipe = recipe
            self._refresh_recipes()

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
